from __future__ import annotations

import csv
from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import CompanyResearchLane, CompanyResearchPacket, OrchestratorDecision, SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.agent_runtime.specialists.company_news import build_agent as build_company_news_agent
from stock_research.agent_runtime.specialists.filing import build_agent as build_filing_agent
from stock_research.agent_runtime.specialists.financial import build_agent as build_financial_agent
from stock_research.agent_runtime.specialists.sentiment import build_agent as build_sentiment_agent
from stock_research.agent_runtime.tools.analysis_tools import analysis_tools
from stock_research.agent_runtime.tools.provider_tools import provider_tools
from stock_research.agent_runtime.tools.repo_tools import repo_tools
from stock_research.evidence import EvidencePacket, read_packet


FALLBACK_PROMPT = """
You are the company research sub-orchestrator.

For one ticker, synthesize deterministic evidence, specialist outputs, and operational memory into a structured company research decision.
Coordinate financials, company news, filings, sentiment, risks, thesis impact, update proposals, human-review items, and next-run tasks.
Do not directly edit files. Do not make automatic trading decisions. Preserve source gaps and uncertainty.
"""


LANE_DEFINITIONS = {
    "financials": {
        "providers": {"yfinance", "fmp", "polygon", "polygon_provider", "alpha_vantage", "financial_compare", "financial_data_specialist"},
        "reports": ("reports/financial_data_specialist/{ticker}_financial_review.md",),
        "missing": "Run financial_compare and financial_review for this ticker.",
    },
    "company_news": {
        "providers": {"company_news_specialist"},
        "reports": ("reports/company_news_specialist/{ticker}_company_news_review.md",),
        "missing": "Run Exa company-news search, contents follow-up, and company_news_review for this ticker.",
    },
    "filings": {
        "providers": {"sec_edgar"},
        "reports": (),
        "missing": "Run SEC EDGAR company provider task and filing review for this ticker.",
    },
    "sentiment": {
        "providers": {"xai_grok"},
        "reports": (),
        "missing": "Run xAI/Grok x_search sentiment provider task for this ticker.",
    },
    "company_search": {
        "providers": set(),
        "reports": (),
        "missing": "Run Exa company/general search for this ticker.",
    },
    "risk_thesis": {
        "providers": set(),
        "reports": (),
        "missing": "Run risk/thesis synthesis after company evidence lanes are available.",
    },
}


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/orchestrator/prompts/company_research.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)

    company_news_context = with_task_memory(context, "company news specialist") if context else None
    company_news_agent = build_company_news_agent(company_news_context)
    financial_context = with_task_memory(context, "financial specialist") if context else None
    financial_agent = build_financial_agent(financial_context)
    filing_context = with_task_memory(context, "SEC filing specialist") if context else None
    filing_agent = build_filing_agent(filing_context)
    sentiment_context = with_task_memory(context, "xAI Grok stock sentiment specialist") if context else None
    sentiment_agent = build_sentiment_agent(sentiment_context)
    return Agent[ResearchRunContext](
        name="Company Research Orchestrator",
        instructions=prompt,
        handoff_description="Coordinates one-ticker company research across evidence lanes and bounded specialists.",
        output_type=OrchestratorDecision,
        tools=[
            *repo_tools(),
            *provider_tools(),
            *analysis_tools(),
            company_news_agent.as_tool(
                tool_name="company_news_specialist",
                tool_description="Review existing company-news artifacts and produce a structured specialist result for this ticker.",
            ),
            financial_agent.as_tool(
                tool_name="financial_specialist",
                tool_description="Review existing financial comparison and financial-data specialist artifacts for this ticker.",
            ),
            filing_agent.as_tool(
                tool_name="filing_specialist",
                tool_description="Review existing SEC EDGAR filing artifacts for this ticker.",
            ),
            sentiment_agent.as_tool(
                tool_name="sentiment_specialist",
                tool_description="Review existing xAI/Grok X sentiment artifacts for this ticker and label social signals carefully.",
            ),
        ],
    )


def build_company_research_packet(context: ResearchRunContext, ticker: str) -> CompanyResearchPacket:
    normalized = ticker.upper()
    manifest = read_manifest(context)
    provider_tasks = matching_tasks(manifest.get("provider_tasks", []), normalized)
    analysis_tasks = matching_tasks(manifest.get("analysis_tasks", []), normalized)
    packets = read_company_packets(context, normalized)
    stock_bucket, stock_info_file = find_stock_tracking_row(context, normalized)
    lanes = [
        build_lane(context, normalized, lane_id, definition, packets, provider_tasks, analysis_tasks)
        for lane_id, definition in LANE_DEFINITIONS.items()
    ]
    return CompanyResearchPacket(
        run_id=context.run_id,
        ticker=normalized,
        stock_bucket=stock_bucket,
        stock_info_file=stock_info_file,
        lanes=lanes,
        evidence_packet_count=len(packets),
        planned_provider_task_ids=[str(task.get("id", "")) for task in provider_tasks if task.get("id")],
        planned_analysis_task_ids=[str(task.get("id", "")) for task in analysis_tasks if task.get("id")],
        memory_item_ids=list(context.memory_item_ids),
    )


def build_company_research_fanout_tasks(
    context: ResearchRunContext,
    ticker: str,
    *,
    timeout_seconds: float | None = 300.0,
) -> list[Any]:
    from stock_research.agent_runtime.fanout import AgentFanoutTask

    packet = build_company_research_packet(context, ticker)
    return [
        AgentFanoutTask(
            task_id=f"financial_{packet.ticker.lower()}",
            agent_id="financial_specialist",
            task="financial specialist",
            prompt=build_company_research_specialist_prompt(packet, "financials"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"company_news_{packet.ticker.lower()}",
            agent_id="company_news_specialist",
            task="company news specialist",
            prompt=build_company_research_specialist_prompt(packet, "company_news"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"filings_{packet.ticker.lower()}",
            agent_id="filing_specialist",
            task="SEC filing specialist",
            prompt=build_company_research_specialist_prompt(packet, "filings"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"sentiment_{packet.ticker.lower()}",
            agent_id="sentiment_specialist",
            task="xAI Grok stock sentiment specialist",
            prompt=build_company_research_specialist_prompt(packet, "sentiment"),
            timeout_seconds=timeout_seconds,
        )
    ]


def build_company_research_input(context: ResearchRunContext, ticker: str) -> str:
    packet = build_company_research_packet(context, ticker)
    return "\n".join(
        [
            f"Review company `{packet.ticker}` for run `{packet.run_id}`.",
            "",
            "Use the company research packet below as the deterministic starting point.",
            "Inspect run artifacts with repo tools before producing final conclusions.",
            "Return a structured OrchestratorDecision with alerts, file update proposals, human review items, and next-run tasks.",
            "Do not invent missing facts. Missing lanes must become next-run tasks.",
            "",
            "Company research packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
        ]
    )


def run_company_research_sub_orchestrator_sync(
    context: ResearchRunContext,
    ticker: str,
    *,
    timeout_seconds: float | None = 300.0,
    runner=None,
) -> tuple[OrchestratorDecision, AgentFanoutResult]:
    from stock_research.agent_runtime.fanout import run_agent_fanout_sync

    tasks = build_company_research_fanout_tasks(context, ticker, timeout_seconds=timeout_seconds)
    kwargs = {"runner": runner} if runner else {}
    fanout = run_agent_fanout_sync(context, tasks, **kwargs)
    return aggregate_company_research(context, ticker, fanout), fanout


def aggregate_company_research(context: ResearchRunContext, ticker: str, fanout: AgentFanoutResult) -> OrchestratorDecision:
    packet = build_company_research_packet(context, ticker)
    specialist_results = [specialist_result_from_output(item.final_output) for item in fanout.results]
    missing_lanes = [lane.lane_id for lane in packet.lanes if lane.status == "missing"]
    partial_lanes = [lane.lane_id for lane in packet.lanes if lane.status == "partial"]
    fanout_failures = [item.task_id for item in fanout.results if item.status in {"error", "timeout"}]
    status = "ready"
    if fanout_failures or missing_lanes:
        status = "partial"
    if len(missing_lanes) >= len(packet.lanes):
        status = "needs_human_review"
    summary = (
        f"Company research packet for {packet.ticker} covers {packet.evidence_packet_count} evidence packet(s), "
        f"{len([lane for lane in packet.lanes if lane.status == 'ready'])} ready lane(s), "
        f"{len(partial_lanes)} partial lane(s), and {len(missing_lanes)} missing lane(s). "
        f"Fanout status is {fanout.status}; review missing lanes before treating this as complete."
    )
    next_tasks = [
        f"Fill missing company research lane `{lane_id}` for {packet.ticker}."
        for lane_id in missing_lanes
    ]
    next_tasks.extend(
        f"Review fanout failure `{task_id}` for {packet.ticker}."
        for task_id in fanout_failures
    )
    return OrchestratorDecision(
        agent_id="company_research_orchestrator",
        run_id=context.run_id,
        status=status,
        summary=summary,
        specialist_results=specialist_results,
        next_run_tasks=next_tasks,
        memory_item_ids_used=list(context.memory_item_ids),
    )


def build_company_research_specialist_prompt(packet: CompanyResearchPacket, lane_id: str) -> str:
    lane = next((item for item in packet.lanes if item.lane_id == lane_id), None)
    return "\n".join(
        [
            f"Review ticker `{packet.ticker}` for company research lane `{lane_id}`.",
            "",
            "Use existing repo/run artifacts only unless an explicit tool permission allows otherwise.",
            "Return a structured SpecialistResult with sources, confidence, alerts, update proposals, and next actions.",
            "",
            "Company research packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
            "",
            f"Lane focus: {json.dumps(asdict(lane), sort_keys=True) if lane else 'unknown'}",
        ]
    )


def build_lane(
    context: ResearchRunContext,
    ticker: str,
    lane_id: str,
    definition: dict[str, Any],
    packets: list[EvidencePacket],
    provider_tasks: list[dict[str, Any]],
    analysis_tasks: list[dict[str, Any]],
) -> CompanyResearchLane:
    providers = set(definition["providers"])
    lane_packets = [packet for packet in packets if packet.provider in providers or packet_belongs_to_lane(packet, lane_id)]
    lane_provider_tasks = [task for task in provider_tasks if task_belongs_to_lane(task, lane_id)]
    lane_analysis_tasks = [task for task in analysis_tasks if task_belongs_to_lane(task, lane_id)]
    report_paths = existing_report_paths(context, ticker, definition.get("reports", ()))
    missing_items = []
    if not lane_packets:
        missing_items.append(str(definition["missing"]))
    if lane_id in {"company_news", "financials"} and not report_paths:
        missing_items.append(f"Missing markdown review report for {lane_id}.")
    status = "ready"
    if missing_items and (lane_packets or report_paths or lane_provider_tasks or lane_analysis_tasks):
        status = "partial"
    elif missing_items:
        status = "missing"
    summary = (
        f"{lane_id} lane has {len(lane_packets)} evidence packet(s), "
        f"{len(report_paths)} report(s), and {len(lane_provider_tasks) + len(lane_analysis_tasks)} planned task(s)."
    )
    return CompanyResearchLane(
        lane_id=lane_id,
        status=status,
        summary=summary,
        evidence_packet_ids=[packet.packet_id for packet in lane_packets],
        report_paths=report_paths,
        planned_task_ids=[str(task.get("id", "")) for task in [*lane_provider_tasks, *lane_analysis_tasks] if task.get("id")],
        missing_items=missing_items,
    )


def read_manifest(context: ResearchRunContext) -> dict[str, Any]:
    path = context.manifest_path or context.run_dir / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_company_packets(context: ResearchRunContext, ticker: str) -> list[EvidencePacket]:
    evidence_dir = context.run_dir / "evidence_packets"
    if not evidence_dir.exists():
        return []
    packets: list[EvidencePacket] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            packet = read_packet(path)
        except Exception:
            continue
        if packet.subject_type == "company" and packet.subject_id.upper() == ticker:
            packets.append(packet)
    return packets


def matching_tasks(tasks: list[Any], ticker: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        subject_id = str(task.get("subject_id") or task.get("args", {}).get("ticker", ""))
        if subject_id.upper() == ticker:
            result.append(task)
    return result


def task_belongs_to_lane(task: dict[str, Any], lane_id: str) -> bool:
    provider = str(task.get("provider", ""))
    tool = str(task.get("tool", ""))
    task_id = str(task.get("id", ""))
    if lane_id == "financials":
        return provider in LANE_DEFINITIONS[lane_id]["providers"] or tool in {"financial_compare", "financial_review"}
    if lane_id == "company_news":
        return "news" in task_id or tool in {"company_news_contents_follow_up", "company_news_review"}
    if lane_id == "filings":
        return provider == "sec_edgar" or "filing" in task_id
    if lane_id == "sentiment":
        return provider == "xai_grok" or "sentiment" in task_id or "x_search" in tool
    if lane_id == "company_search":
        return provider == "exa" and "news" not in task_id
    if lane_id == "risk_thesis":
        return tool in {"risk_review", "thesis_review"} or "risk" in task_id or "thesis" in task_id
    return False


def packet_belongs_to_lane(packet: EvidencePacket, lane_id: str) -> bool:
    packet_id = packet.packet_id.lower()
    if lane_id == "company_news":
        return packet.provider == "exa" and ("news" in packet_id or "contents_follow_up" in packet_id)
    if lane_id == "company_search":
        return packet.provider == "exa" and "news" not in packet_id and "contents_follow_up" not in packet_id
    if lane_id == "risk_thesis":
        return bool(packet.risks or packet.contradictions or packet.recommended_updates)
    return False


def existing_report_paths(context: ResearchRunContext, ticker: str, patterns: tuple[str, ...]) -> list[str]:
    paths: list[str] = []
    for pattern in patterns:
        relative = pattern.format(ticker=ticker)
        path = context.run_dir / relative
        if path.exists():
            paths.append(relative)
    return paths


def find_stock_tracking_row(context: ResearchRunContext, ticker: str) -> tuple[str, str]:
    for bucket, relative in (
        ("current_holdings", "stock_tracking/current_holdings/current_holdings.csv"),
        ("monitoring", "stock_tracking/monitoring/monitoring.csv"),
        ("rejected", "stock_tracking/rejected/rejected.csv"),
    ):
        path = context.root / relative
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                row_ticker = row.get("ticker") or row.get("symbol") or row.get("stock_abr") or row.get("abr") or ""
                if row_ticker.upper() == ticker:
                    return bucket, row.get("stock_info_file", "")
    return "", ""


def specialist_result_from_output(output: Any) -> SpecialistResult:
    data = output_to_dict(output)
    return SpecialistResult(
        agent_id=str(data.get("agent_id", "unknown_specialist")),
        subject_type=str(data.get("subject_type", "company")),
        subject_id=str(data.get("subject_id", "")),
        status=data.get("status", "partial") if data.get("status") in {"ready", "partial", "needs_human_review", "blocked"} else "partial",
        summary=str(data.get("summary", "No specialist summary returned.")),
        confidence=data.get("confidence", "medium") if data.get("confidence") in {"low", "medium", "high"} else "medium",
        sources=list(data.get("sources", [])),
        alerts=list(data.get("alerts", [])),
        file_update_proposals=list(data.get("file_update_proposals", [])),
        human_review_items=list(data.get("human_review_items", [])),
        memory_item_ids_used=list(data.get("memory_item_ids_used", [])),
        next_actions=list(data.get("next_actions", [])),
    )
