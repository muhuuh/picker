from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .memory import relative_to_root
from .repo import find_repo_root
from .report_formatting import format_financial_value


@dataclass(frozen=True)
class HumanSynthesisPack:
    run_id: str
    ticker: str
    status: str
    expected_final_report_path: str
    synthesis_pack_path: str
    synthesis_pack_json_path: str
    artifacts: list[dict[str, Any]]
    quality_findings: list[str]


@dataclass(frozen=True)
class HumanSynthesisPackResult:
    run_id: str
    status: str
    packs: list[HumanSynthesisPack]
    quality_findings: list[str]
    written_paths: list[str]


def build_human_synthesis_packs(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
    tickers: list[str] | None = None,
    write: bool = False,
) -> HumanSynthesisPackResult:
    repo_root = find_repo_root(root)
    ticker_list = [ticker.upper() for ticker in (tickers or discover_opportunity_tickers(repo_root, run_id))]
    packs = [build_human_synthesis_pack(repo_root, run_id, ticker, current_date=current_date, write=write) for ticker in ticker_list]
    quality_findings: list[str] = []
    if not packs:
        quality_findings.append(f"No opportunity assessments found for run {run_id}; no human synthesis packs built.")
    for pack in packs:
        quality_findings.extend(pack.quality_findings)
    status = "ready" if packs and not quality_findings else "needs_review"
    return HumanSynthesisPackResult(
        run_id=run_id,
        status=status,
        packs=packs,
        quality_findings=unique(quality_findings),
        written_paths=[path for pack in packs for path in (pack.synthesis_pack_json_path, pack.synthesis_pack_path) if path],
    )


def build_human_synthesis_pack(
    root: Path,
    run_id: str,
    ticker: str,
    current_date: date | None = None,
    write: bool = False,
) -> HumanSynthesisPack:
    repo_root = find_repo_root(root)
    ticker_upper = ticker.upper()
    run_dir = repo_root / "agents" / "runs" / run_id
    out_dir = run_dir / "reports" / "human_synthesis"
    md_path = out_dir / f"{ticker_upper}_synthesis_pack.md"
    json_path = out_dir / f"{ticker_upper}_synthesis_pack.json"
    final_report_path = out_dir / f"{ticker_upper}_final_human_report.md"
    artifacts = collect_ticker_artifacts(repo_root, run_id, ticker_upper)
    assessment = read_json(run_dir / "raw" / "opportunity_assessment" / f"{ticker_upper}_opportunity_assessment.json")
    quality_findings = validate_pack_inputs(ticker_upper, assessment, artifacts)
    status = "ready_for_codex_synthesis" if not quality_findings else "needs_review"

    pack = HumanSynthesisPack(
        run_id=run_id,
        ticker=ticker_upper,
        status=status,
        expected_final_report_path=relative_to_root(repo_root, final_report_path).as_posix(),
        synthesis_pack_path=relative_to_root(repo_root, md_path).as_posix(),
        synthesis_pack_json_path=relative_to_root(repo_root, json_path).as_posix(),
        artifacts=artifacts,
        quality_findings=quality_findings,
    )
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        payload = human_synthesis_pack_to_dict(pack)
        payload["evidence_summary"] = evidence_summary(assessment)
        payload["generated_at"] = (current_date or date.today()).isoformat()
        json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(format_human_synthesis_pack_markdown(pack, assessment, current_date=current_date), encoding="utf-8")
    return pack


def discover_opportunity_tickers(root: Path, run_id: str) -> list[str]:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "opportunity_assessment"
    if not raw_dir.exists():
        return []
    return sorted(path.name[: -len("_opportunity_assessment.json")].upper() for path in raw_dir.glob("*_opportunity_assessment.json"))


def collect_ticker_artifacts(root: Path, run_id: str, ticker: str) -> list[dict[str, Any]]:
    run_dir = root / "agents" / "runs" / run_id
    artifact_specs: list[tuple[Path, str, bool]] = [
        (
            run_dir / "reports" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.md",
            "Deterministic opportunity/audit report. Use it for evidence coverage, not as final prose.",
            True,
        ),
        (
            run_dir / "raw" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.json",
            "Structured deterministic assessment used to seed this synthesis pack.",
            True,
        ),
        (
            run_dir / "reports" / "financial_data_specialist" / f"{ticker}_financial_review.md",
            "Financial specialist review with provider conflicts and missing metrics.",
            True,
        ),
        (
            run_dir / "reports" / "company_news_specialist" / f"{ticker}_company_news_review.md",
            "Source-backed company-news review and content follow-up status.",
            True,
        ),
        (
            run_dir / "raw" / "financial_data_specialist" / f"{ticker}_financial_review.json",
            "Structured financial specialist output.",
            False,
        ),
        (
            run_dir / "raw" / "company_news_specialist" / f"{ticker}_company_news_review.json",
            "Structured company-news specialist output.",
            False,
        ),
    ]
    artifacts = [artifact(root, path, purpose, required=required) for path, purpose, required in artifact_specs]
    artifacts.extend(grok_artifacts(root, run_dir, ticker))
    company_file = find_company_file(root, ticker)
    if company_file:
        artifacts.append(artifact(root, company_file, "Current durable company-file context and prior thesis state.", required=False))
    return artifacts


def grok_artifacts(root: Path, run_dir: Path, ticker: str) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    raw_dir = run_dir / "raw" / "xai_grok"
    ticker_key = ticker.lower()
    ticker_slug = "".join(character.lower() if character.isalnum() else "_" for character in ticker).strip("_")
    patterns = [
        ("*x_search*" + ticker_key + "*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*" + ticker_key + "*x_search*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*xai_x*" + ticker_key + "*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*" + ticker_key + "*xai_x*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*web_search*" + ticker_key + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_key + "*web_search*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*web_deep_dive*" + ticker_key + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_key + "*web_deep_dive*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*xai_web*" + ticker_key + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_key + "*xai_web*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*x_search*" + ticker_slug + "*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*" + ticker_slug + "*x_search*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*xai_x*" + ticker_slug + "*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*" + ticker_slug + "*xai_x*.json", "Grok/X social narrative raw artifact. Treat as social signal, not fact."),
        ("*web_search*" + ticker_slug + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_slug + "*web_search*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*web_deep_dive*" + ticker_slug + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_slug + "*web_deep_dive*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*xai_web*" + ticker_slug + "*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
        ("*" + ticker_slug + "*xai_web*.json", "Grok web-search deep-dive raw artifact. Treat as auxiliary coverage-gap evidence until verified."),
    ]
    seen: set[Path] = set()
    if raw_dir.exists():
        for pattern, purpose in patterns:
            for path in sorted(raw_dir.glob(pattern)):
                if path in seen:
                    continue
                seen.add(path)
                artifacts.append(artifact(root, path, purpose, required=False))
    return artifacts


def find_company_file(root: Path, ticker: str) -> Path | None:
    info_dir = root / "stock_tracking" / "stock_info_files"
    if not info_dir.exists():
        return None
    candidates = sorted(info_dir.glob(f"**/{ticker}.md"))
    return candidates[0] if candidates else None


def validate_pack_inputs(ticker: str, assessment: dict[str, Any], artifacts: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    if not assessment:
        findings.append(f"{ticker} synthesis pack is missing structured opportunity assessment JSON.")
    missing_required = [item["path"] for item in artifacts if item["required"] and not item["exists"]]
    if missing_required:
        findings.append(f"{ticker} synthesis pack is missing required artifacts: {', '.join(missing_required)}.")
    if assessment:
        financial = assessment.get("financial_snapshot") or {}
        news = assessment.get("news_snapshot") or {}
        social = assessment.get("social_snapshot") or {}
        if financial.get("status") == "missing":
            findings.append(f"{ticker} synthesis pack has no usable financial specialist status.")
        if news.get("status") == "missing":
            findings.append(f"{ticker} synthesis pack has no usable company-news specialist status.")
        if social.get("status") == "available" and not social.get("x_pulse"):
            findings.append(f"{ticker} synthesis pack has Grok/X data but no X pulse narrative.")
    return findings


def format_human_synthesis_pack_markdown(
    pack: HumanSynthesisPack,
    assessment: dict[str, Any],
    current_date: date | None = None,
) -> str:
    today = (current_date or date.today()).isoformat()
    summary = evidence_summary(assessment)
    lines = [
        f"# Human Synthesis Pack: {pack.ticker}",
        "",
        f"Run: `{pack.run_id}`",
        f"Generated: {today}",
        f"Status: {pack.status}",
        f"Expected final report: `{pack.expected_final_report_path}`",
        "",
        "## Purpose",
        "",
        "This is the deterministic handoff to the Codex app for a first-principles human report. Codex app GPT-5.5 high is the primary writer; API/OpenRouter writing is only a remote/headless fallback. The deterministic opportunity assessment is an evidence and audit layer; it is not the final reading experience.",
        "",
        "## Synthesis Instructions",
        "",
        "1. Write the final human-facing report from scratch; do not paste sections together.",
        "2. Use the established AMBA report only as a format exemplar; do not invent a new report format unless the user explicitly asks.",
        provenance_instruction(pack),
        "4. Required sections, in this order: Bottom Line; What [Company] Actually Does; Why The Setup Changed; X Sentiment And What It Is Really Saying; Financial And Valuation Read; Bull Case; Bear Case; What Would Change The Thesis; Next Research Checks; Final Assessment; Sources.",
        "5. Coverage rule: preserve material investor insight, but do not target a word count. Stable or low-signal names should be brief; evidence-rich material changes should receive more space.",
        "6. Required insight coverage: source-backed developments, market/industry context, X pulse and trend evolution, recurring bull and bear social claims, notable accounts/posts or source-quality context, rumors/unverified claims, non-obvious or under-discussed angles, valuation/analyst gaps, decision table or scorecard, thesis changers, and concrete next checks.",
        "7. Explain why each important point matters to an investor. Do not compress facts so far that a reader cannot act on them.",
        "8. Separate verified facts, auxiliary Grok web context, Grok/X social narrative, rumors, and your synthesis.",
        "9. Prefer fewer stronger points over every available point, but include every material insight that would change research priority, thesis confidence, or a follow-up check. Remove repeated claims across sections.",
        "10. Use exact dates and numbers where available. If providers conflict, name the conflict and how to verify it.",
        "11. Before finishing, self-check that the report is not merely a high-level summary: it should preserve opportunity-assessment depth, include a scorecard or decision table, and keep source-backed facts separate from social/rumor evidence.",
        "12. Do not give buy/sell/trade instructions or position-size advice.",
        "",
        "## Evidence Priority",
        "",
        "- Highest confidence: company filings, financial providers, company IR/releases, and source-backed Exa contents.",
        "- Medium confidence: specialist summaries that cite the artifacts above.",
        "- Auxiliary only: Grok web-search context, especially analyst consensus, rumors, and broad web facts until independently verified.",
        "- Social signal only: Grok/X sentiment, influencer narratives, and X rumors.",
        "- Evidence packets expose bounded complete-sentence excerpts for navigation. When a claim is promoted into the final report, follow its full-evidence path/raw artifact and verify the complete selected text rather than extending or repairing the excerpt.",
        "",
        "## Current Deterministic View",
        "",
        f"- Opportunity view: {summary.get('opportunity_view') or 'unknown'}",
        f"- Score / risk / confidence: {summary.get('opportunity_score') or 'unknown'} / {summary.get('risk_level') or 'unknown'} / {summary.get('confidence') or 'unknown'}",
        f"- Thesis freshness: {summary.get('thesis_freshness') or 'unknown'}",
        f"- One-line summary: {summary.get('summary') or 'none'}",
        f"- Recommended next action from audit layer: {summary.get('recommended_next_action') or 'none'}",
        "",
    ]
    append_financial_summary(lines, summary.get("financial_snapshot") or {})
    append_news_summary(lines, summary.get("news_snapshot") or {})
    append_social_summary(lines, summary.get("social_snapshot") or {})
    append_grok_web_summary(lines, summary.get("grok_web_snapshot") or {})
    seen_claims = seen_from_lines(lines)
    append_list(lines, "Positives To Consider", summary.get("positives") or [], seen=seen_claims)
    append_list(lines, "Risks / Headwinds To Consider", summary.get("negatives") or [], seen=seen_claims)
    append_list(lines, "Next Checks From Audit Layer", summary.get("watch_items") or [], seen=seen_claims)
    lines.extend(["## Artifact Map", ""])
    append_artifact_table(lines, pack.artifacts)
    lines.extend(["", "## Pack Quality Findings", ""])
    if pack.quality_findings:
        lines.extend(f"- {finding}" for finding in pack.quality_findings)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def provenance_instruction(pack: HumanSynthesisPack) -> str:
    has_grok_web = any(
        item.get("exists") and "web-search deep-dive" in str(item.get("purpose", ""))
        for item in pack.artifacts
    )
    optional_web = (
        " A same-run Grok web gap-fill artifact is present, so identify it as auxiliary context."
        if has_grok_web
        else " No same-run Grok web gap-fill ran, so do not claim or imply that it did."
    )
    return (
        "3. After the run/date metadata, include a provenance paragraph beginning `This report is a Codex-written "
        "synthesis from` and name only inputs that actually exist in the artifact map. End by stating `The deterministic "
        "opportunity assessment remains the audit artifact.`"
        + optional_web
    )


def evidence_summary(assessment: dict[str, Any]) -> dict[str, Any]:
    if not assessment:
        return {}
    insight = assessment.get("investor_insight_report") or {}
    return {
        "ticker": assessment.get("ticker", ""),
        "opportunity_view": assessment.get("opportunity_view", ""),
        "opportunity_score": assessment.get("opportunity_score", ""),
        "risk_level": assessment.get("risk_level", ""),
        "confidence": assessment.get("confidence", ""),
        "thesis_freshness": assessment.get("thesis_freshness", ""),
        "summary": assessment.get("summary", ""),
        "recommended_next_action": assessment.get("recommended_next_action", ""),
        "financial_snapshot": assessment.get("financial_snapshot") or {},
        "news_snapshot": assessment.get("news_snapshot") or {},
        "social_snapshot": assessment.get("social_snapshot") or {},
        "grok_web_snapshot": assessment.get("grok_web_snapshot") or insight.get("grok_web_research") or {},
        "positives": list(assessment.get("positives") or [])[:6],
        "negatives": list(assessment.get("negatives") or [])[:6],
        "watch_items": list(assessment.get("watch_items") or [])[:8],
    }


def append_financial_summary(lines: list[str], financial: dict[str, Any]) -> None:
    lines.extend(["## Financial / Valuation Inputs", ""])
    keys = [
        "latest_price",
        "market_cap",
        "pe_ratio",
        "forward_pe",
        "analyst_target_price",
        "analyst_target_implied_upside",
        "price_to_sales_ttm",
        "revenue_ttm",
        "profit_margin",
        "operating_margin_ttm",
        "free_cash_flow_per_share_ttm",
        "currency",
        "material_conflict_count",
        "valuation_sanity_warning_count",
    ]
    for key in keys:
        if key in financial:
            lines.append(f"- {key}: {format_financial_value(key, financial.get(key))}")
    warnings = financial.get("valuation_sanity_warnings") or []
    if warnings:
        lines.append("- valuation warnings:")
        lines.extend(f"  - {item}" for item in warnings[:4])
    if len(lines) >= 2 and lines[-1] == "":
        lines.append("- No financial inputs available.")
    lines.append("")


def append_news_summary(lines: list[str], news: dict[str, Any]) -> None:
    lines.extend(["## Source-Backed News Inputs", ""])
    lines.append(f"- status/source count: {news.get('status', 'missing')} / {news.get('source_count', 0)}")
    developments = news.get("material_developments") or []
    if developments:
        lines.append("- material developments:")
        for item in developments[:6]:
            claim = item.get("claim") if isinstance(item, dict) else str(item)
            lines.append(f"  - {claim}")
    else:
        lines.append("- material developments: none extracted.")
    lines.append("")


def append_social_summary(lines: list[str], social: dict[str, Any]) -> None:
    lines.extend(["## Grok/X Social Signal Inputs", ""])
    lines.append(f"- status/sentiment: {social.get('status', 'missing')} / {social.get('sentiment', 'missing')}")
    if social.get("x_pulse"):
        lines.append(f"- X pulse: {social['x_pulse']}")
    append_list(lines, "Bullish X Claims", social.get("bullish_claims") or [], heading_level="###")
    append_list(lines, "Bearish / Skeptical X Claims", social.get("bearish_claims") or [], heading_level="###")
    if social.get("notable_accounts"):
        lines.append(f"- notable accounts: {', '.join(social['notable_accounts'][:8])}")
    if social.get("rumor_flag"):
        lines.append("- rumor flag: true; keep rumors explicitly labeled.")
    lines.append("")


def append_grok_web_summary(lines: list[str], grok_web: dict[str, Any]) -> None:
    lines.extend(["## Auxiliary Grok Web Inputs", ""])
    if not grok_web or grok_web.get("status") == "missing":
        lines.append("- No same-run Grok web deep-dive snapshot was available.")
        lines.append("")
        return
    fields = [
        ("Business / technology", "business_technology_overview"),
        ("Industry / competition", "industry_competition"),
        ("Financial snapshot", "financial_snapshot"),
        ("Analyst forecasts", "analyst_forecasts"),
        ("Overall assessment", "overall_assessment"),
    ]
    for label, key in fields:
        value = grok_web.get(key)
        if value:
            lines.append(f"- {label}: {value}")
    append_list(lines, "Latest News / Rumors From Grok Web", grok_web.get("latest_news_rumors") or [], heading_level="###")
    append_list(lines, "Grok Web Catalysts To Verify", grok_web.get("catalysts_tailwinds") or [], heading_level="###")
    append_list(lines, "Grok Web Risks To Verify", grok_web.get("risks_headwinds") or [], heading_level="###")
    lines.append("")


def append_list(lines: list[str], title: str, items: list[Any], heading_level: str = "##", seen: set[str] | None = None) -> None:
    if heading_level:
        lines.extend([f"{heading_level} {title}", ""])
    if not items:
        lines.append("- None.")
        lines.append("")
        return
    emitted = 0
    for item in items[:8]:
        text = str(item)
        key = claim_key(text)
        if seen is not None and key and is_duplicate_claim(key, seen):
            continue
        if seen is not None and key:
            seen.add(key)
        lines.append(f"- {text}")
        emitted += 1
    if emitted == 0:
        lines.append("- Covered by earlier sections.")
    lines.append("")


def append_artifact_table(lines: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        lines.append("- None.")
        return
    lines.extend(["| Status | Required | Artifact | Purpose |", "| --- | --- | --- | --- |"])
    for row in rows:
        status = "present" if row["exists"] else "missing"
        required = "yes" if row["required"] else "no"
        lines.append(f"| {status} | {required} | `{row['path']}` | {row['purpose']} |")


def artifact(root: Path, path: Path, purpose: str, *, required: bool) -> dict[str, Any]:
    return {
        "path": relative_to_root(root, path).as_posix(),
        "exists": path.exists(),
        "required": required,
        "purpose": purpose,
    }


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def seen_from_lines(lines: list[str]) -> set[str]:
    seen: set[str] = set()
    for line in lines:
        key = claim_key(line)
        if key:
            seen.add(key)
    return seen


def claim_key(value: str) -> str:
    import re

    text = re.sub(r"\[[^\]]+\]\([^)]+\)", "", str(value).lower())
    text = re.sub(r"[^a-z0-9]+", " ", text)
    key = " ".join(text.split())
    return key if len(key.split()) >= 8 else ""


def is_duplicate_claim(key: str, seen: set[str]) -> bool:
    words = set(key.split())
    for previous in seen:
        if key == previous or key in previous or previous in key:
            return True
        previous_words = set(previous.split())
        if len(words & previous_words) / max(len(words), len(previous_words)) >= 0.82:
            return True
    return False


def human_synthesis_pack_to_dict(pack: HumanSynthesisPack) -> dict[str, Any]:
    return asdict(pack)


def human_synthesis_pack_result_to_dict(result: HumanSynthesisPackResult) -> dict[str, Any]:
    return asdict(result)


def unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
