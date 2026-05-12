from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.context import ResearchRunContext, build_research_run_context
from stock_research.agent_runtime.orchestrators.market_research import (
    build_market_research_packet,
    run_market_research_sub_orchestrator_sync,
)
from stock_research.agent_runtime.outputs import CandidateLead, OrchestratorDecision
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.candidate_review import CandidateReviewGroup, group_candidate_leads
from stock_research.evidence import Claim, EvidencePacket
from stock_research.manifest import (
    discovery_query,
    provider_task,
    slugify,
    x_search_window_args,
)
from stock_research.provider_runner import run_provider_tasks
from stock_research.providers.xai_grok import industry_sentiment_prompt, latest_news_prompt
from stock_research.validation import parse_date


PROMOTING_ACTIONS = {"add_to_monitoring"}
GROK_PROVIDERS = {"xai_grok"}
EXA_PROVIDERS = {"exa"}
TICKER_STOPWORDS = {
    "AI",
    "API",
    "CEO",
    "CFO",
    "COO",
    "EU",
    "ETF",
    "EV",
    "GDP",
    "IPO",
    "LLM",
    "PE",
    "R&D",
    "SEC",
    "UK",
    "US",
    "USA",
    "USD",
    "BELGIUM",
    "CANADA",
    "CHINA",
    "CROATIA",
    "DENMARK",
    "FRANCE",
    "GERMANY",
    "HUNGARY",
    "INDIA",
    "ITALY",
    "MEXICO",
    "NETHERLANDS",
    "SPAIN",
    "SWITZERLAND",
    "VIETNAM",
}
RUMOR_WORDS = {"rumor", "rumour", "speculation", "unconfirmed", "whisper", "leak", "alleged"}
HYPE_WORDS = {"hype", "viral", "crowded", "momentum", "breakout", "moon", "squeeze", "trending"}
POSITIVE_WORDS = {"bullish", "positive", "enthusiastic", "upside", "growth", "winner"}
NEGATIVE_WORDS = {"bearish", "negative", "risk", "concern", "short", "problem"}


@dataclass
class ManualMarketResearchResult:
    run_id: str
    subject_type: str
    subject_id: str
    topic: str
    status: str
    provider_result: dict[str, Any] = field(default_factory=dict)
    decision: OrchestratorDecision | None = None
    candidate_leads: list[CandidateLead] = field(default_factory=list)
    quality_findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)
    live_model_called: bool = False


def run_manual_market_research(
    *,
    root: Path,
    topic: str,
    subject_type: str = "theme",
    subject_id: str = "",
    run_id: str = "",
    write: bool = False,
    execute_providers: bool = False,
    execute_orchestrator: bool = False,
    current_date: date | None = None,
    days: int = 21,
    model: str | None = None,
    timeout_seconds: float | None = 300.0,
) -> ManualMarketResearchResult:
    today = current_date or date.today()
    normalized_subject_type = subject_type.strip() or "theme"
    normalized_subject_id = subject_id.strip() or slugify(topic)
    normalized_run_id = run_id.strip() or f"{today.isoformat()}_manual-market"
    manifest = build_manual_market_manifest(
        topic=topic,
        subject_type=normalized_subject_type,
        subject_id=normalized_subject_id,
        run_id=normalized_run_id,
        current_date=today,
        days=days,
    )
    run_dir = root / "agents" / "runs" / normalized_run_id
    manifest_path = run_dir / "manifest.json"
    written_paths: list[str] = []
    if write:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written_paths.append(str(manifest_path))

    provider_result = run_provider_tasks(
        root=root,
        manifest=manifest,
        execute=execute_providers,
        current_date=today,
    )
    context = build_research_run_context(
        root=root,
        run_id=normalized_run_id,
        task="manual market research",
        manifest_path=manifest_path if write else None,
        dry_run=not execute_orchestrator,
        execute_providers=execute_providers,
    )
    decision: OrchestratorDecision | None = None
    if execute_orchestrator:
        decision, fanout = run_market_research_sub_orchestrator_sync(
            context,
            normalized_subject_id,
            normalized_subject_type,
            topic,
            timeout_seconds=timeout_seconds,
        )
        from stock_research.agent_runtime.orchestrators.market_research import write_market_research_report

        written_paths.extend(str(path) for path in write_market_research_report(context, normalized_subject_id, normalized_subject_type, topic, decision, fanout))
    else:
        decision = build_deterministic_market_decision(context, normalized_subject_id, normalized_subject_type, topic)

    packets = []
    if write or execute_providers:
        packets = read_market_packets_for_manual_run(context, normalized_subject_id, normalized_subject_type)
    candidates = extract_candidate_leads(
        packets=packets,
        root=root,
        current_date=today,
    )
    quality_findings = evaluate_candidate_leads_quality(candidates)
    if decision:
        decision.candidate_leads = candidates
        if quality_findings and decision.status == "ready":
            decision.status = "needs_human_review"
    report_paths: list[Path] = []
    if write:
        report_paths = write_manual_market_research_report(
            context=context,
            topic=topic,
            subject_type=normalized_subject_type,
            subject_id=normalized_subject_id,
            decision=decision,
            candidate_leads=candidates,
            evidence_packets=packets,
            quality_findings=quality_findings,
            provider_result=provider_result,
        )
        written_paths.extend(str(path) for path in report_paths)

    status = manual_status(provider_result, decision, quality_findings, execute_providers, execute_orchestrator)
    return ManualMarketResearchResult(
        run_id=normalized_run_id,
        subject_type=normalized_subject_type,
        subject_id=normalized_subject_id,
        topic=topic,
        status=status,
        provider_result=provider_result,
        decision=decision,
        candidate_leads=candidates,
        quality_findings=quality_findings,
        written_paths=dedupe_paths(written_paths),
        live_model_called=execute_orchestrator,
    )


def build_manual_market_manifest(
    *,
    topic: str,
    subject_type: str,
    subject_id: str,
    run_id: str,
    current_date: date,
    days: int = 21,
) -> dict[str, Any]:
    query = topic.strip()
    grok_prompt = latest_news_prompt(query) if subject_type == "theme" else industry_sentiment_prompt(query)
    return {
        "manifest_version": 1,
        "manifest_id": f"manual_market_{run_id}",
        "generated_at": current_date.isoformat(),
        "run_type": "manual_market_research",
        "run_date": current_date.isoformat(),
        "scope": ["US", "Europe"],
        "inputs": {
            "manual_request": {
                "topic": query,
                "subject_type": subject_type,
                "subject_id": subject_id,
            },
            "research_priorities": [
                {
                    "Topic": query,
                    "Type": subject_type,
                    "Priority": "manual",
                    "Status": "active",
                }
            ],
        },
        "provider_tasks": [
            provider_task(
                task_id=f"manual_exa_context_{subject_id}",
                provider="exa",
                tool="search",
                subject_type=subject_type,
                subject_id=subject_id,
                args={
                    "mode": "industry" if subject_type == "industry" else "general",
                    "query": f"{query} latest developments public companies investment implications US Europe",
                    "run_id": run_id,
                    "num_results": 8,
                },
                reason=f"Manual Exa context scan for {query}.",
                priority="high",
                source_bucket="manual_market_research",
            ),
            provider_task(
                task_id=f"manual_exa_company_discovery_{subject_id}",
                provider="exa",
                tool="search",
                subject_type=subject_type,
                subject_id=subject_id,
                args={
                    "mode": "company",
                    "query": discovery_query(query, "US and Europe"),
                    "run_id": run_id,
                    "num_results": 12,
                },
                reason=f"Manual Exa company-discovery scan for {query}.",
                priority="high",
                source_bucket="manual_market_research",
                follow_up=["Use Exa contents for high-value results before adding names to monitoring."],
            ),
            provider_task(
                task_id=f"manual_xai_x_search_{subject_id}",
                provider="xai_grok",
                tool="x_search",
                subject_type=subject_type,
                subject_id=subject_id,
                args={
                    "prompt": grok_prompt,
                    "run_id": run_id,
                    "research_kind": "industry_sentiment" if subject_type == "industry" else "latest_news",
                    "model": "grok-4.3",
                    **x_search_window_args(current_date, days=days),
                    "enable_image_understanding": True,
                },
                reason=f"Manual Grok/X discovery scan for niche trends, hype, rumors, sentiment, and emerging ticker leads around {query}.",
                priority="high",
                source_bucket="manual_market_research",
            ),
        ],
        "analysis_tasks": [],
        "outputs": {
            "manifest": f"agents/runs/{run_id}/manifest.json",
            "market_report": f"agents/runs/{run_id}/market_research/{subject_id}_manual_market_research.md",
        },
    }


def build_deterministic_market_decision(
    context: ResearchRunContext,
    subject_id: str,
    subject_type: str,
    topic: str,
) -> OrchestratorDecision:
    packet = build_market_research_packet(context, subject_id, subject_type, topic)
    ready_lanes = [lane for lane in packet.lanes if lane.status == "ready"]
    missing_lanes = [lane.lane_id for lane in packet.lanes if lane.status == "missing"]
    status = "partial"
    if "grok_x_discovery" in missing_lanes:
        status = "needs_human_review"
    elif not missing_lanes:
        status = "ready"
    summary = (
        f"Manual market research setup for {packet.topic} has {len(ready_lanes)} ready lane(s), "
        f"{len(missing_lanes)} missing lane(s), and {packet.evidence_packet_count} evidence packet(s). "
        "Grok/X leads are treated as social lead generation and require Exa, filing, or market-data verification before promotion."
    )
    return OrchestratorDecision(
        agent_id="manual_market_research",
        run_id=context.run_id,
        status=status,
        summary=summary,
        next_run_tasks=[f"Fill missing market research lane `{lane_id}` for {packet.topic}." for lane_id in missing_lanes],
        memory_item_ids_used=list(context.memory_item_ids),
    )


def extract_candidate_leads(
    *,
    packets: list[EvidencePacket],
    root: Path,
    current_date: date | None = None,
) -> list[CandidateLead]:
    candidates: dict[str, CandidateLead] = {}
    for packet in packets:
        channel = source_channel(packet)
        for claim in packet.claims:
            for ticker in extract_tickers_from_text(f"{claim.claim} {claim.evidence}"):
                lead = candidates.setdefault(ticker, CandidateLead(ticker=ticker))
                merge_candidate_from_claim(lead, packet, claim, channel)
        if not packet.claims:
            for ticker in extract_tickers_from_text(packet.notes):
                lead = candidates.setdefault(ticker, CandidateLead(ticker=ticker))
                merge_candidate_from_packet_notes(lead, packet, channel)

    cooldown = rejected_cooldown_by_ticker(root, current_date or date.today())
    for lead in candidates.values():
        lead.source_channels = sorted(set(lead.source_channels))
        lead.source_ids = sorted(set(lead.source_ids))
        lead.verification_status = verification_status_for(lead.source_channels)
        lead.rejected_cooldown_status = cooldown.get(lead.ticker, "not_rejected")
        lead.next_action = next_action_for(lead)
        lead.needs_human_review = lead.next_action in {"human_review", "add_to_monitoring"} or lead.rejected_cooldown_status != "not_rejected"
        lead.notes = notes_for_candidate(lead)
    return sorted(candidates.values(), key=lambda item: (action_rank(item.next_action), item.ticker))


def merge_candidate_from_claim(lead: CandidateLead, packet: EvidencePacket, claim: Claim, channel: str) -> None:
    if channel and channel not in lead.source_channels:
        lead.source_channels.append(channel)
    lead.source_ids.extend(claim.source_ids or [packet.packet_id])
    candidate_reason = candidate_reason_from_claim(lead.ticker, claim)
    lead.why_surfaced = combine_candidate_reason(lead.why_surfaced, candidate_reason)
    if not lead.company_name:
        lead.company_name = company_name_from_claim(claim.claim)
    text = (candidate_reason or claim.claim).lower()
    lead.rumor_flag = lead.rumor_flag or any(word in text for word in RUMOR_WORDS)
    lead.hype_level = combine_hype_level(lead.hype_level, hype_level_for_text(text))
    lead.sentiment = combine_sentiment(lead.sentiment, sentiment_for_text(text))
    if not lead.industry and packet.subject_type in {"industry", "theme"}:
        lead.industry = packet.subject_id.replace("_", " ")


def merge_candidate_from_packet_notes(lead: CandidateLead, packet: EvidencePacket, channel: str) -> None:
    if channel and channel not in lead.source_channels:
        lead.source_channels.append(channel)
    lead.source_ids.append(packet.packet_id)
    lead.why_surfaced = choose_longer(lead.why_surfaced, packet.notes)
    text = packet.notes.lower()
    lead.rumor_flag = lead.rumor_flag or any(word in text for word in RUMOR_WORDS)
    lead.hype_level = combine_hype_level(lead.hype_level, hype_level_for_text(text))
    lead.sentiment = combine_sentiment(lead.sentiment, sentiment_for_text(text))


def extract_tickers_from_text(text: str) -> list[str]:
    candidates: set[str] = set()
    patterns = [
        r"\$([A-Z][A-Z0-9.]{1,6})\b",
        r"\b(?:NASDAQ|NYSE|AMEX|LSE|XETRA|ETR|EPA|BIT|AMS|SWX|SIX|OTCQX|OTC):\s*([A-Z0-9.]{1,8})\b",
        r"\bticker\s+([A-Z][A-Z0-9.]{1,6})\b",
        r"\(([A-Z][A-Z0-9.]{1,8})\)\s+is\s+a\b",
        r"\bStock Symbols?:\s*([A-Z][A-Z0-9.]{1,8})\b",
    ]
    for pattern in patterns:
        for value in re.findall(pattern, text, flags=re.IGNORECASE):
            ticker = value.upper().strip(".")
            if ticker and ticker not in TICKER_STOPWORDS:
                candidates.add(ticker)
    return sorted(candidates)


def company_name_from_claim(claim: str) -> str:
    prefix = "Relevant Exa result:"
    if claim.startswith(prefix):
        value = claim[len(prefix) :].strip()
        return value.split(" (", 1)[0].strip()
    return ""


def candidate_reason_from_claim(ticker: str, claim: Claim) -> str:
    cleaned_evidence = clean_research_text(claim.evidence)
    if claim.claim.startswith("Relevant Exa result:") and cleaned_evidence:
        return f"{claim.claim}: {first_sentence(cleaned_evidence)}"
    ticker_context = ticker_context_from_text(ticker, claim.evidence)
    if ticker_context:
        return ticker_context
    return claim.claim


def combine_candidate_reason(current: str, candidate: str) -> str:
    candidate = clean_research_text(candidate)
    current = clean_research_text(current)
    if not candidate:
        return current
    if not current:
        return candidate
    if candidate.lower() in current.lower():
        return current
    if current.lower() in candidate.lower():
        return candidate
    return truncate(f"{current} Also surfaced because: {candidate}", 320)


def ticker_context_from_text(ticker: str, text: str) -> str:
    if not ticker or not text:
        return ""
    patterns = [rf"\${re.escape(ticker)}\b", rf"\b{re.escape(ticker)}\b"]
    chunks = re.split(r"(?:\n\s*[-*]\s+|\n\n+|;\s+|(?<=[.!?])\s+)", text)
    for chunk in chunks:
        if any(re.search(pattern, chunk, flags=re.IGNORECASE) for pattern in patterns):
            return truncate(clean_research_text(chunk), 260)
    return ""


def source_channel(packet: EvidencePacket) -> str:
    if packet.provider in GROK_PROVIDERS:
        return "grok"
    if packet.provider in EXA_PROVIDERS:
        return "exa"
    return packet.provider or "unknown"


def verification_status_for(channels: list[str]) -> str:
    channel_set = set(channels)
    if "grok" in channel_set and "exa" in channel_set:
        return "verified"
    if "grok" in channel_set and any(channel not in {"grok"} for channel in channel_set):
        return "partially_verified"
    if channel_set == {"grok"}:
        return "grok_only"
    if channel_set == {"exa"}:
        return "exa_only"
    if channel_set:
        return "partially_verified"
    return "unverified"


def next_action_for(lead: CandidateLead) -> str:
    if lead.rejected_cooldown_status == "cooldown_active":
        return "ignore"
    if lead.rumor_flag:
        return "verify"
    if lead.verification_status == "grok_only":
        return "verify"
    if lead.verification_status in {"verified", "partially_verified"}:
        return "human_review"
    return "verify"


def evaluate_candidate_leads_quality(candidate_leads: list[CandidateLead]) -> list[str]:
    findings: list[str] = []
    for lead in candidate_leads:
        label = lead.ticker or lead.company_name or "unknown candidate"
        if not lead.source_ids:
            findings.append(f"{label}: candidate is missing source_ids.")
        if not lead.verification_status:
            findings.append(f"{label}: candidate is missing verification_status.")
        if lead.next_action in PROMOTING_ACTIONS and lead.verification_status == "grok_only":
            findings.append(f"{label}: Grok-only lead cannot be promoted to monitoring.")
        if lead.next_action in PROMOTING_ACTIONS and "cooldown_active" in lead.rejected_cooldown_status:
            findings.append(f"{label}: rejected-stock cooldown blocks promotion.")
        if lead.rumor_flag and lead.next_action != "verify":
            findings.append(f"{label}: rumor-like lead must remain explicitly verification-limited.")
    return findings


def write_manual_market_research_report(
    *,
    context: ResearchRunContext,
    topic: str,
    subject_type: str,
    subject_id: str,
    decision: OrchestratorDecision | None,
    candidate_leads: list[CandidateLead],
    evidence_packets: list[EvidencePacket],
    quality_findings: list[str],
    provider_result: dict[str, Any],
) -> list[Path]:
    target_dir = context.run_dir / "market_research"
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_id = slugify(subject_id or topic)
    md_path = target_dir / f"{safe_id}_manual_market_research.md"
    candidates_path = target_dir / f"{safe_id}_candidate_leads.json"
    md_path.write_text(
        format_manual_market_research_markdown(
            context=context,
            topic=topic,
            subject_type=subject_type,
            subject_id=subject_id,
            decision=decision,
            candidate_leads=candidate_leads,
            evidence_packets=evidence_packets or [],
            quality_findings=quality_findings,
            provider_result=provider_result,
        ),
        encoding="utf-8",
    )
    candidates_path.write_text(json.dumps([asdict(lead) for lead in candidate_leads], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [md_path, candidates_path]


def format_manual_market_research_markdown(
    *,
    context: ResearchRunContext,
    topic: str,
    subject_type: str,
    subject_id: str,
    decision: OrchestratorDecision | None,
    candidate_leads: list[CandidateLead],
    evidence_packets: list[EvidencePacket],
    quality_findings: list[str],
    provider_result: dict[str, Any],
) -> str:
    data = output_to_dict(decision) if decision else {}
    insights = build_market_investor_insight_report(
        topic=topic,
        subject_type=subject_type,
        candidate_leads=candidate_leads,
        evidence_packets=evidence_packets or [],
    )
    lines = [
        f"# Manual Market Research: {topic}",
        "",
        f"- run_id: {context.run_id}",
        f"- subject_type: {subject_type}",
        f"- subject_id: {subject_id}",
        f"- status: {data.get('status', 'unknown')}",
        f"- provider_mode: {provider_result.get('mode', 'unknown')}",
        f"- planned_provider_tasks: {provider_result.get('planned_count', 0)}",
        "",
        "## Summary",
        "",
        str(data.get("summary", "") or "No synthesis available yet."),
        "",
        *format_market_investor_insight_markdown(insights),
        "",
        "## Notable X Narratives",
        "",
        *format_x_narratives(candidate_leads),
        "",
        "## Companies Discovered",
        "",
        *format_candidate_table(candidate_leads),
        "",
        "## Verified Vs Unverified Leads",
        "",
        *format_verification_summary(candidate_leads),
        "",
        "## Hype / Noise Assessment",
        "",
        *format_hype_summary(candidate_leads),
        "",
        "## Discovery Quality Gate",
        "",
    ]
    if quality_findings:
        lines.extend(f"- {finding}" for finding in quality_findings)
    else:
        lines.append("- Passed: no deterministic discovery quality findings.")
    lines.extend(["", "## Next Research Tasks", ""])
    next_tasks = list(data.get("next_run_tasks") or [])
    next_tasks.extend(next_tasks_from_candidates(candidate_leads))
    lines.extend(f"- {task}" for task in dedupe_strings(next_tasks)) if next_tasks else lines.append("- None.")
    lines.extend(["", "## Source Artifacts", ""])
    lines.append(f"- manifest: agents/runs/{context.run_id}/manifest.json")
    lines.append(f"- candidate_leads: agents/runs/{context.run_id}/market_research/{slugify(subject_id or topic)}_candidate_leads.json")
    lines.append(f"- evidence_packets: agents/runs/{context.run_id}/evidence_packets/")
    return "\n".join(lines).rstrip() + "\n"


def build_market_investor_insight_report(
    *,
    topic: str,
    subject_type: str,
    candidate_leads: list[CandidateLead],
    evidence_packets: list[EvidencePacket],
) -> dict[str, Any]:
    exa_claims = research_claims(evidence_packets, provider="exa")
    grok_claims = research_claims(evidence_packets, provider="xai_grok")
    top_candidates = rank_candidate_leads(candidate_leads)[:8]
    verified_count = sum(1 for lead in candidate_leads if lead.verification_status in {"verified", "partially_verified"})
    grok_only_count = sum(1 for lead in candidate_leads if lead.verification_status == "grok_only")
    return {
        "executive_read": build_market_executive_read(topic, top_candidates, exa_claims, grok_claims, verified_count, grok_only_count),
        "industry_context": market_context_items(exa_claims, limit=5),
        "x_pulse": x_pulse_items(grok_claims, limit=6),
        "trend_evolution": trend_items(exa_claims, grok_claims, limit=6),
        "bullish_narratives": grok_section_items(grok_claims, ["Recurring bullish narratives"], limit=5),
        "skeptical_narratives": grok_section_items(grok_claims, ["Recurring bearish/skeptical narratives", "Recurring bearish or skeptical narratives"], limit=5),
        "grok_candidate_follow_up": grok_section_items(grok_claims, ["Candidate follow-up list", "Companies being discussed"], limit=8),
        "grok_scorecard": grok_scorecard_table(grok_claims),
        "candidate_pipeline": build_candidate_pipeline(candidate_leads),
        "non_obvious_angles": non_obvious_market_angles(exa_claims, grok_claims, candidate_leads, limit=6),
        "hype_noise": grok_section_items(grok_claims, ["Hype/noise/rumors map", "Hype/noise/spam level", "Rumors or unverified claims"], limit=5),
        "decision_table": build_market_decision_table(candidate_leads),
        "next_questions": market_next_questions(topic, top_candidates, grok_only_count),
        "coverage": {
            "subject_type": subject_type,
            "candidate_count": len(candidate_leads),
            "verified_or_partially_verified": verified_count,
            "grok_only": grok_only_count,
            "source_packet_count": len(evidence_packets),
        },
    }


def format_market_investor_insight_markdown(report: dict[str, Any]) -> list[str]:
    lines = [
        "## Investor Insight Report",
        "",
        "### Executive Read",
        "",
        str(report.get("executive_read") or "No investor-grade synthesis available yet."),
        "",
        "### Industry / Theme Context",
        "",
    ]
    append_report_bullets(lines, report.get("industry_context"), "No source-backed industry context extracted yet.")
    lines.extend(["", "### X / Community Pulse", ""])
    append_report_bullets(lines, report.get("x_pulse"), "No Grok/X community pulse extracted yet.")
    lines.extend(["", "### Trend Evolution And Demand Signals", ""])
    append_report_bullets(lines, report.get("trend_evolution"), "No trend evolution signals extracted yet.")
    lines.extend(["", "### Bullish Narratives From X", ""])
    append_report_bullets(lines, report.get("bullish_narratives"), "No bullish Grok/X narratives extracted yet.")
    lines.extend(["", "### Skeptical Narratives From X", ""])
    append_report_bullets(lines, report.get("skeptical_narratives"), "No skeptical Grok/X narratives extracted yet.")
    lines.extend(["", "### Grok Candidate Follow-up", ""])
    append_report_bullets(lines, report.get("grok_candidate_follow_up"), "No Grok candidate follow-up list extracted yet.")
    scorecard = report.get("grok_scorecard") or []
    if scorecard:
        lines.extend(["", "### Grok Investor Scorecard", ""])
        lines.extend(scorecard)
    lines.extend(["", "### Candidate Pipeline", ""])
    lines.extend(report.get("candidate_pipeline") or ["No candidate pipeline extracted yet."])
    lines.extend(["", "### Non-obvious / Contrarian Angles To Verify", ""])
    append_report_bullets(lines, report.get("non_obvious_angles"), "No non-obvious angles extracted yet.")
    lines.extend(["", "### Hype / Noise / Rumors", ""])
    append_report_bullets(lines, report.get("hype_noise"), "No hype/noise map extracted yet.")
    lines.extend(["", "### Decision Table", ""])
    lines.extend(report.get("decision_table") or ["No decision table available yet."])
    lines.extend(["", "### Next Research Questions", ""])
    append_report_bullets(lines, report.get("next_questions"), "No next questions available yet.")
    return lines


def build_market_executive_read(
    topic: str,
    candidate_leads: list[CandidateLead],
    exa_claims: list[Claim],
    grok_claims: list[Claim],
    verified_count: int,
    grok_only_count: int,
) -> str:
    context = first_research_bullet(exa_claims) or "source-backed industry context is still thin"
    x_pulse_candidates = x_pulse_items(grok_claims, limit=1)
    x_pulse = strip_source_label(x_pulse_candidates[0]) if x_pulse_candidates else "X/community pulse is still thin"
    candidate_names = ", ".join(display_candidate(lead) for lead in candidate_leads[:5]) or "no candidate yet"
    return (
        f"{topic}: {context} X/community angle: {x_pulse} "
        f"Candidate pipeline: {candidate_names}. Verification state: {verified_count} verified/partially verified, "
        f"{grok_only_count} Grok-only lead(s). Grok-only ideas are discovery leads, not monitoring additions."
    )


def research_claims(evidence_packets: list[EvidencePacket], *, provider: str) -> list[Claim]:
    claims: list[Claim] = []
    for packet in evidence_packets:
        if packet.provider == provider:
            packet_claims = list(packet.claims)
            if provider == "xai_grok" and packet_claims:
                full_text = load_full_grok_text(packet)
                if full_text:
                    packet_claims[0] = replace(packet_claims[0], evidence=full_text)
            claims.extend(packet_claims)
    return claims


def load_full_grok_text(packet: EvidencePacket) -> str:
    if not packet.raw_artifact_path:
        return ""
    path = Path(packet.raw_artifact_path)
    if not path.exists():
        return ""
    try:
        from stock_research.providers.xai_grok import extract_output_text

        data = json.loads(path.read_text(encoding="utf-8"))
        response = data.get("response", data)
        return extract_output_text(response)
    except Exception:
        return ""


def market_context_items(exa_claims: list[Claim], *, limit: int) -> list[str]:
    items: list[str] = []
    for claim in exa_claims:
        if claim.claim.startswith("Exa "):
            continue
        evidence = clean_research_text(claim.evidence)
        if looks_like_company_profile(evidence):
            continue
        item = first_sentence(evidence) or clean_research_text(claim.claim)
        if item:
            items.append(source_labeled_text(item, claim.source_ids))
    return dedupe_strings(items)[:limit]


def x_pulse_items(grok_claims: list[Claim], *, limit: int) -> list[str]:
    items: list[str] = []
    for claim in grok_claims:
        items.extend(extract_section_points(claim.evidence, ["Industry X pulse", "Executive X pulse", "Executive X pulse"], limit=3))
        items.extend(extract_section_points(claim.evidence, ["Social Sentiment", "Expert/community split"], limit=3))
        if not items:
            items.append(first_sentence(claim.evidence))
    return [source_labeled_text(item, source_ids_from_claims(grok_claims)) for item in dedupe_strings(items)[:limit] if item]


def trend_items(exa_claims: list[Claim], grok_claims: list[Claim], *, limit: int) -> list[str]:
    items: list[str] = []
    for claim in grok_claims:
        items.extend(extract_section_points(claim.evidence, ["Trend evolution", "What changed recently"], limit=3))
        items.extend(extract_section_points(claim.evidence, ["Key technologies and demand drivers", "Verified Facts", "Verified facts people are reacting to"], limit=3))
    for claim in exa_claims:
        if claim.claim.startswith("Exa "):
            continue
        text = clean_research_text(claim.evidence)
        if looks_like_company_profile(text):
            continue
        if any(word in text.lower() for word in ["growth", "deal", "capacity", "revenue", "demand", "investment", "capital", "market"]):
            items.append(source_labeled_text(first_sentence(text), claim.source_ids))
    return dedupe_strings([item for item in items if item])[:limit]


def build_candidate_pipeline(candidate_leads: list[CandidateLead]) -> list[str]:
    if not candidate_leads:
        return ["No candidates extracted yet."]
    groups = rank_candidate_groups(candidate_leads)[:8]
    rows = [
        "| Candidate | Signal | Verification | Why it matters | Human decision |",
        "| --- | --- | --- | --- | --- |",
    ]
    for group in groups:
        rows.append(
            "| "
            + " | ".join(
                [
                    sanitize_table_cell(display_candidate_group(group)),
                    sanitize_table_cell(candidate_group_signal_label(group)),
                    group.verification_status,
                    sanitize_table_cell(truncate(clean_research_text(group.why_surfaced), 220)),
                    human_decision_label_for_group(group),
                ]
            )
            + " |"
        )
    return rows


def non_obvious_market_angles(
    exa_claims: list[Claim],
    grok_claims: list[Claim],
    candidate_leads: list[CandidateLead],
    *,
    limit: int,
) -> list[str]:
    items: list[str] = []
    for claim in grok_claims:
        items.extend(extract_section_points(claim.evidence, ["Non-obvious or contrarian angles", "Non-obvious or under-discussed angles"], limit=4))
        items.extend(extract_section_points(claim.evidence, ["Candidate follow-up list", "Companies being discussed", "Companies/tickers surfaced"], limit=4))
    for claim in exa_claims:
        if claim.claim.startswith("Exa "):
            continue
        text = clean_research_text(claim.evidence)
        if looks_like_company_profile(text):
            continue
        if any(word in text.lower() for word in ["bottleneck", "risk", "queue", "selective", "tightened", "struggling", "outperform"]):
            items.append(source_labeled_text(first_sentence(text), claim.source_ids))
    for lead in candidate_leads:
        if lead.verification_status == "grok_only" or lead.rumor_flag:
            items.append(f"{display_candidate(lead)} is a Grok/X-only or rumor-like lead; verify with Exa, filings, and market data before any monitoring decision.")
    return dedupe_strings([item for item in items if item])[:limit]


def build_market_decision_table(candidate_leads: list[CandidateLead]) -> list[str]:
    rows = [
        "| Dimension | Current read | Actionable next step |",
        "| --- | --- | --- |",
    ]
    verified = [lead for lead in candidate_leads if lead.verification_status in {"verified", "partially_verified"}]
    grok_only = [lead for lead in candidate_leads if lead.verification_status == "grok_only"]
    exa_only = [lead for lead in candidate_leads if lead.verification_status == "exa_only"]
    rows.append(f"| Source-backed candidates | {len(verified)} verified/partially verified; {len(exa_only)} Exa-only | Prioritize Exa-only names for financial and filing checks before monitoring. |")
    rows.append(f"| X/community leads | {len(grok_only)} Grok-only lead(s) | Treat as early signal; require Exa or primary-source verification before promotion. |")
    rows.append("| Hype/noise | " + sanitize_table_cell(hype_summary_sentence(candidate_leads)) + " | Separate durable demand signals from ticker pumps and promotional posts. |")
    rows.append("| Human decision | Candidates are research leads, not automatic additions | Approve verify / reject / more research from the human review digest. |")
    return rows


def market_next_questions(topic: str, candidate_leads: list[CandidateLead], grok_only_count: int) -> list[str]:
    questions = [
        f"Which companies are the real economic beneficiaries of {topic}, rather than just adjacent names surfaced by search?",
        "Which surfaced names have public tickers, adequate liquidity, and financial data good enough for a company research run?",
    ]
    if grok_only_count:
        questions.append("Which Grok/X-only leads can be verified by Exa company search, filings, or financial providers?")
    if candidate_leads:
        questions.append(f"Run company research on the highest-signal candidate: {display_candidate(candidate_leads[0])}.")
    return questions


def rank_candidate_leads(candidate_leads: list[CandidateLead]) -> list[CandidateLead]:
    return sorted(candidate_leads, key=lambda lead: (candidate_rank(lead), lead.ticker or lead.company_name))


def candidate_rank(lead: CandidateLead) -> tuple[int, int, int]:
    verification = {"verified": 0, "partially_verified": 1, "exa_only": 2, "grok_only": 3, "unverified": 4, "cooldown_blocked": 5}.get(lead.verification_status, 9)
    hype = {"high": 0, "medium": 1, "low": 2, "unknown": 3}.get(lead.hype_level, 3)
    rumor = 1 if lead.rumor_flag else 0
    return verification, hype, rumor


def display_candidate(lead: CandidateLead) -> str:
    if lead.company_name and lead.ticker:
        return f"{lead.company_name} ({lead.ticker})"
    return lead.company_name or lead.ticker or "unknown"


def candidate_signal_label(lead: CandidateLead) -> str:
    channels = "+".join(lead.source_channels) or "unknown"
    tags = [channels]
    if lead.hype_level != "unknown":
        tags.append(f"{lead.hype_level} hype")
    if lead.sentiment != "unknown":
        tags.append(f"{lead.sentiment} sentiment")
    if lead.rumor_flag:
        tags.append("rumor/speculation")
    return ", ".join(tags)


def human_decision_label(lead: CandidateLead) -> str:
    if lead.next_action == "verify":
        return "approve verification / reject / request more research"
    if lead.next_action == "human_review":
        return "approve monitoring review / reject / request more research"
    if lead.next_action == "ignore":
        return "ignore unless user overrides"
    return lead.next_action


def hype_summary_sentence(candidate_leads: list[CandidateLead]) -> str:
    if not candidate_leads:
        return "No candidate hype state extracted yet."
    high = [display_candidate(lead) for lead in candidate_leads if lead.hype_level == "high"]
    rumors = [display_candidate(lead) for lead in candidate_leads if lead.rumor_flag]
    return f"High-hype: {', '.join(high) if high else 'none'}; rumor/speculation: {', '.join(rumors) if rumors else 'none'}."


def append_report_bullets(lines: list[str], values: Any, empty: str) -> None:
    items = [str(value) for value in (values or []) if str(value).strip()]
    if not items:
        lines.append(f"- {empty}")
        return
    lines.extend(f"- {item}" for item in items)


def grok_section_items(grok_claims: list[Claim], section_titles: list[str], *, limit: int) -> list[str]:
    items: list[str] = []
    for claim in grok_claims:
        items.extend(extract_section_points(claim.evidence, section_titles, limit=limit))
    return [source_labeled_text(item, source_ids_from_claims(grok_claims)) for item in dedupe_strings(items)[:limit] if item]


def grok_scorecard_table(grok_claims: list[Claim]) -> list[str]:
    for claim in grok_claims:
        body = extract_section_body(claim.evidence, ["Investor implications and scorecard", "Investor scorecard"])
        rows = [line.rstrip() for line in body.splitlines() if line.strip().startswith("|")]
        if len(rows) >= 2:
            return rows
    return []


def first_research_bullet(claims: list[Claim]) -> str:
    for claim in claims:
        if claim.claim.startswith("Exa "):
            continue
        evidence = clean_research_text(claim.evidence)
        if looks_like_company_profile(evidence):
            continue
        bullets = extract_any_bullets(evidence, limit=1)
        if bullets:
            return bullets[0]
        sentence = first_sentence(evidence)
        if sentence:
            return sentence
    return ""


def extract_section_bullets(text: str, section_title: str, *, limit: int) -> list[str]:
    return extract_section_points(text, [section_title], limit=limit, bullets_only=True)


def extract_section_points(text: str, section_titles: list[str], *, limit: int, bullets_only: bool = False) -> list[str]:
    body = extract_section_body(text, section_titles)
    if not body:
        return []
    bullets = extract_any_bullets(body, limit=limit)
    if bullets or bullets_only:
        return bullets[:limit]
    paragraphs = [clean_research_text(part) for part in re.split(r"\n\s*\n+", body) if clean_research_text(part)]
    if paragraphs:
        return [truncate(paragraph, 320) for paragraph in paragraphs[:limit]]
    return [first_sentence(body)] if first_sentence(body) else []


def extract_section_body(text: str, section_titles: list[str]) -> str:
    wanted = [normalize_research_heading(title) for title in section_titles]
    sections = split_research_sections(text)
    for title in wanted:
        for heading, body in sections:
            normalized = normalize_research_heading(heading)
            if normalized == title or normalized.startswith(title) or title in normalized:
                return body.strip()
    return ""


def split_research_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    current_heading = ""
    current_lines: list[str] = []
    for line in text.splitlines():
        heading = parse_research_heading(line)
        if heading:
            if current_heading or current_lines:
                sections.append((current_heading, current_lines))
            current_heading = heading
            current_lines = []
            continue
        current_lines.append(line)
    if current_heading or current_lines:
        sections.append((current_heading, current_lines))
    return [(heading, "\n".join(lines).strip()) for heading, lines in sections if heading]


def parse_research_heading(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return ""
    stripped = stripped.strip("*").strip()
    stripped = stripped.lstrip("#").strip()
    match = re.match(r"^\d+[\).]\s*(.+?)\s*$", stripped)
    if match:
        return match.group(1).strip(" *:")
    if stripped.endswith(":") and len(stripped.split()) <= 7:
        return stripped.strip(":")
    return ""


def normalize_research_heading(value: str) -> str:
    value = value.strip().strip("*").lstrip("#").strip().lower()
    value = re.sub(r"^\d+[\).]\s*", "", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def extract_any_bullets(text: str, *, limit: int) -> list[str]:
    bullets: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "*")):
            value = clean_research_text(stripped.lstrip("-* "))
            if value.endswith(":") and len(value.split()) <= 4:
                continue
            if value:
                bullets.append(truncate(value, 280))
        if len(bullets) >= limit:
            break
    return bullets


def source_labeled_text(text: str, source_ids: list[str]) -> str:
    label = ", ".join(source_ids[:3])
    suffix = f" [{label}]" if label else ""
    return f"{truncate(clean_research_text(text), 420)}{suffix}"


def strip_source_label(value: str) -> str:
    return re.sub(r"\s+\[[^\]]+\]$", "", value).strip()


def looks_like_company_profile(text: str) -> bool:
    sample = text[:900].lower()
    return (
        " is a " in sample
        and " company" in sample
        and any(marker in sample for marker in ["employs", "headquartered", "market cap", "ipo", "founded"])
    )


def source_ids_from_claims(claims: list[Claim]) -> list[str]:
    result: list[str] = []
    for claim in claims:
        result.extend(claim.source_ids)
    return dedupe_strings(result)


def clean_research_text(value: str) -> str:
    value = value or ""
    replacements = {
        "\u200b": "",
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u2192": "->",
        mojibake("\u2192"): "->",
        mojibake("\u2013"): "-",
        mojibake("\u2014"): "-",
        mojibake("\u2018"): "'",
        mojibake("\u2019"): "'",
        mojibake("\u201c"): '"',
        mojibake("\u201d"): '"',
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    value = re.sub(r"\[\[(\d+)\]\]\([^)]+\)", r"[\1]", value)
    value = re.sub(r"\s+", " ", value)
    value = value.replace("**", "").replace("###", "").replace("##", "").strip()
    value = value.lstrip("-* ").strip()
    return value


def mojibake(value: str) -> str:
    return value.encode("utf-8").decode("cp1252", errors="replace")


def first_sentence(value: str) -> str:
    text = clean_research_text(value)
    if not text:
        return ""
    match = re.search(r"(.{80,}?[.!?])\s", text)
    if match:
        return match.group(1).strip()
    return truncate(text, 220)


def manual_market_result_to_dict(result: ManualMarketResearchResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "subject_type": result.subject_type,
        "subject_id": result.subject_id,
        "topic": result.topic,
        "status": result.status,
        "provider_result": result.provider_result,
        "decision": output_to_dict(result.decision) if result.decision else {},
        "candidate_leads": [asdict(lead) for lead in result.candidate_leads],
        "quality_findings": result.quality_findings,
        "written_paths": result.written_paths,
        "live_model_called": result.live_model_called,
    }


def read_market_packets_for_manual_run(context: ResearchRunContext, subject_id: str, subject_type: str) -> list[EvidencePacket]:
    from stock_research.agent_runtime.orchestrators.market_research import read_market_packets

    return read_market_packets(context, subject_id, subject_type)


def rejected_cooldown_by_ticker(root: Path, today: date) -> dict[str, str]:
    path = root / "stock_tracking" / "rejected" / "rejected.csv"
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            eligible = parse_date(str(row.get("next_eligible_review_date", "")))
            if eligible and eligible > today:
                result[ticker] = "cooldown_active"
            elif eligible:
                result[ticker] = "cooldown_elapsed"
            else:
                result[ticker] = "rejected_missing_cooldown_date"
    return result


def manual_status(
    provider_result: dict[str, Any],
    decision: OrchestratorDecision | None,
    quality_findings: list[str],
    execute_providers: bool,
    execute_orchestrator: bool,
) -> str:
    if provider_result.get("errors"):
        return "needs_review"
    if quality_findings:
        return "needs_review"
    if execute_orchestrator:
        if decision and decision.status == "ready":
            return "complete"
        if decision and decision.status == "needs_human_review":
            return "needs_review"
        return "partial"
    if not execute_providers:
        return "dry_run"
    return "partial"


def format_x_narratives(candidate_leads: list[CandidateLead]) -> list[str]:
    grok_groups = [group for group in rank_candidate_groups(candidate_leads) if "grok" in group.source_channels]
    if not grok_groups:
        return ["- No Grok/X candidate narratives were extracted from current evidence."]
    return [
        f"- {display_candidate_group(group)}: {group.why_surfaced or 'surfaced by Grok/X'} "
        f"(hype={group.hype_level}, verification={group.verification_status}, rumor={str(group.rumor_flag).lower()})"
        for group in grok_groups
    ]


def format_candidate_table(candidate_leads: list[CandidateLead]) -> list[str]:
    if not candidate_leads:
        return ["No candidates extracted yet.", ""]
    groups = rank_candidate_groups(candidate_leads)
    rows = [
        "| Candidate | Tickers | Channels | Verification | Hype | Cooldown | Next Action | Why surfaced |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for group in groups:
        rows.append(
            "| "
            + " | ".join(
                [
                    sanitize_table_cell(group.canonical_name),
                    ", ".join(group.tickers),
                    ", ".join(group.source_channels),
                    group.verification_status,
                    group.hype_level,
                    group.rejected_cooldown_status,
                    group.next_action,
                    sanitize_table_cell(truncate(group.why_surfaced, 180)),
                ]
            )
            + " |"
        )
    return rows


def format_verification_summary(candidate_leads: list[CandidateLead]) -> list[str]:
    if not candidate_leads:
        return ["- No candidate verification state yet."]
    counts: dict[str, int] = {}
    for lead in candidate_leads:
        counts[lead.verification_status] = counts.get(lead.verification_status, 0) + 1
    return [f"- {status}: {count}" for status, count in sorted(counts.items())]


def format_hype_summary(candidate_leads: list[CandidateLead]) -> list[str]:
    if not candidate_leads:
        return ["- No hype/noise assessment yet."]
    high_hype = [lead for lead in candidate_leads if lead.hype_level == "high"]
    rumor_leads = [lead for lead in candidate_leads if lead.rumor_flag]
    return [
        f"- High-hype leads: {', '.join(lead.ticker for lead in high_hype) if high_hype else 'none'}",
        f"- Rumor/unverified leads: {', '.join(lead.ticker for lead in rumor_leads) if rumor_leads else 'none'}",
        "- Grok-only leads remain verification tasks, not monitoring additions.",
    ]


def next_tasks_from_candidates(candidate_leads: list[CandidateLead]) -> list[str]:
    tasks = []
    for group in rank_candidate_groups(candidate_leads):
        label = display_candidate_group(group)
        if group.next_action == "verify":
            if len(group.tickers) > 1 and group.verification_status == "grok_only":
                tasks.append(f"Decide whether to verify Grok/X basket {label}; if approved, run Exa/company/financial checks on the strongest names first.")
            else:
                tasks.append(f"Verify candidate {label} with Exa company search, filings where available, and market data before promotion.")
        elif group.next_action == "human_review":
            tasks.append(f"Human review candidate {label} for possible monitoring after evidence review.")
    return tasks


def rank_candidate_groups(candidate_leads: list[CandidateLead]) -> list[CandidateReviewGroup]:
    return group_candidate_leads(rank_candidate_leads(candidate_leads))


def display_candidate_group(group: CandidateReviewGroup) -> str:
    tickers = f" ({', '.join(group.tickers)})" if group.tickers else ""
    return f"{group.canonical_name}{tickers}"


def candidate_group_signal_label(group: CandidateReviewGroup) -> str:
    channels = "+".join(group.source_channels) or "unknown"
    tags = [channels]
    if group.hype_level != "unknown":
        tags.append(f"{group.hype_level} hype")
    if group.sentiment != "unknown":
        tags.append(f"{group.sentiment} sentiment")
    if group.rumor_flag:
        tags.append("rumor/speculation")
    if len(group.tickers) > 1:
        tags.append("basket")
    return ", ".join(tags)


def human_decision_label_for_group(group: CandidateReviewGroup) -> str:
    if group.next_action == "verify":
        if len(group.tickers) > 1 and group.verification_status == "grok_only":
            return "approve basket verification / reject / narrow scope"
        return "approve verification / reject / request more research"
    if group.next_action == "human_review":
        return "approve monitoring review / reject / request more research"
    if group.next_action == "ignore":
        return "ignore unless user overrides"
    return group.next_action


def hype_level_for_text(text: str) -> str:
    return "high" if any(word in text for word in HYPE_WORDS) else "unknown"


def combine_hype_level(current: str, new: str) -> str:
    if "high" in {current, new}:
        return "high"
    if "medium" in {current, new}:
        return "medium"
    if "low" in {current, new}:
        return "low"
    return "unknown"


def sentiment_for_text(text: str) -> str:
    positive = any(word in text for word in POSITIVE_WORDS)
    negative = any(word in text for word in NEGATIVE_WORDS)
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    return "unknown"


def combine_sentiment(current: str, new: str) -> str:
    if current == "unknown":
        return new
    if new == "unknown" or new == current:
        return current
    return "mixed"


def notes_for_candidate(lead: CandidateLead) -> str:
    notes = []
    if lead.verification_status == "grok_only":
        notes.append("Grok-only social lead; verify before promotion.")
    if lead.rumor_flag:
        notes.append("Contains rumor/speculation language.")
    if lead.rejected_cooldown_status == "cooldown_active":
        notes.append("Rejected cooldown active; do not resurface unless user overrides.")
    return " ".join(notes)


def choose_longer(current: str, candidate: str) -> str:
    candidate = candidate.strip()
    if len(candidate) > len(current):
        return candidate
    return current


def action_rank(action: str) -> int:
    return {"human_review": 0, "verify": 1, "ignore": 2, "reject": 3, "add_to_monitoring": 4}.get(action, 9)


def sanitize_table_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def truncate(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return value[: length - 3].rstrip() + "..."


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def dedupe_paths(values: list[str]) -> list[str]:
    return dedupe_strings(values)
