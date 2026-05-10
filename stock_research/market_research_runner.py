from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
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
    lead.why_surfaced = choose_longer(lead.why_surfaced, claim.claim)
    if not lead.company_name:
        lead.company_name = company_name_from_claim(claim.claim)
    text = f"{claim.claim} {claim.evidence}".lower()
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
        if lead.rumor_flag and lead.verification_status not in {"grok_only", "unverified", "partially_verified"}:
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
    quality_findings: list[str],
    provider_result: dict[str, Any],
) -> str:
    data = output_to_dict(decision) if decision else {}
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
    grok_leads = [lead for lead in candidate_leads if "grok" in lead.source_channels]
    if not grok_leads:
        return ["- No Grok/X candidate narratives were extracted from current evidence."]
    return [
        f"- {lead.ticker}: {lead.why_surfaced or 'surfaced by Grok/X'} "
        f"(hype={lead.hype_level}, verification={lead.verification_status}, rumor={str(lead.rumor_flag).lower()})"
        for lead in grok_leads
    ]


def format_candidate_table(candidate_leads: list[CandidateLead]) -> list[str]:
    if not candidate_leads:
        return ["No candidates extracted yet.", ""]
    rows = [
        "| Ticker | Channels | Verification | Hype | Cooldown | Next Action | Why surfaced |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for lead in candidate_leads:
        rows.append(
            "| "
            + " | ".join(
                [
                    lead.ticker or "",
                    ", ".join(lead.source_channels),
                    lead.verification_status,
                    lead.hype_level,
                    lead.rejected_cooldown_status,
                    lead.next_action,
                    sanitize_table_cell(truncate(lead.why_surfaced, 160)),
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
    for lead in candidate_leads:
        if lead.next_action == "verify":
            tasks.append(f"Verify candidate {lead.ticker} with Exa company search, filings where available, and market data before promotion.")
        elif lead.next_action == "human_review":
            tasks.append(f"Human review candidate {lead.ticker} for possible monitoring after evidence review.")
    return tasks


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
