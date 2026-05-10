from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import MarketResearchLane, MarketResearchPacket, OrchestratorDecision, SpecialistResult
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.agent_runtime.specialists.discovery import build_agent as build_discovery_agent
from stock_research.agent_runtime.specialists.exa_industry import build_agent as build_exa_industry_agent
from stock_research.agent_runtime.specialists.grok_discovery import build_agent as build_grok_discovery_agent
from stock_research.agent_runtime.specialists.quality_review import build_agent as build_quality_review_agent
from stock_research.agent_runtime.tools.provider_tools import provider_tools
from stock_research.agent_runtime.tools.repo_tools import repo_tools
from stock_research.agent_runtime.tracing import write_run_metrics
from stock_research.evidence import EvidencePacket, read_packet


FALLBACK_PROMPT = """
You are the market research sub-orchestrator.

Coordinate industry/theme discovery using Exa web/company evidence and xAI/Grok X social-signal evidence.
Grok is mandatory for niche trends, hype, rumors, emerging tickers, and community sentiment, but Grok/X output is lead generation only.
Candidate names must be verified with Exa, filings, or market-data providers before promotion.
"""


LANE_DEFINITIONS = {
    "exa_industry": {
        "providers": {"exa"},
        "missing": "Run Exa industry/general/news search for this topic.",
    },
    "exa_company_discovery": {
        "providers": {"exa"},
        "missing": "Run Exa company search for public company discovery in this topic.",
    },
    "grok_x_discovery": {
        "providers": {"xai_grok"},
        "missing": "Run xAI/Grok x_search with date window and X-search parameters for this topic.",
    },
    "candidate_synthesis": {
        "providers": set(),
        "missing": "Run candidate discovery synthesis after Exa and Grok lanes exist.",
    },
}


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/orchestrator/prompts/market_research.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)

    exa_context = with_task_memory(context, "Exa industry research specialist") if context else None
    exa_agent = build_exa_industry_agent(exa_context)
    grok_context = with_task_memory(context, "xAI Grok industry sentiment specialist") if context else None
    grok_agent = build_grok_discovery_agent(grok_context)
    discovery_context = with_task_memory(context, "discovery specialist") if context else None
    discovery_agent = build_discovery_agent(discovery_context)
    quality_context = with_task_memory(context, "quality reviewer specialist") if context else None
    quality_agent = build_quality_review_agent(quality_context)

    return Agent[ResearchRunContext](
        name="Market Research Orchestrator",
        instructions=prompt,
        handoff_description="Coordinates industry/theme research, X trend discovery, candidate discovery, and strategy fit.",
        output_type=OrchestratorDecision,
        tools=[
            *repo_tools(),
            *provider_tools(),
            exa_agent.as_tool(
                tool_name="exa_industry_specialist",
                tool_description="Review existing Exa industry/theme/company-discovery artifacts and source-backed web evidence.",
            ),
            grok_agent.as_tool(
                tool_name="grok_discovery_specialist",
                tool_description="Review existing xAI/Grok x_search artifacts for X trends, hype, rumors, and emerging ticker leads.",
            ),
            discovery_agent.as_tool(
                tool_name="discovery_specialist",
                tool_description="Combine Exa-verified and Grok-surfaced leads into strategy-aware candidate discovery output.",
            ),
            quality_agent.as_tool(
                tool_name="quality_reviewer_specialist",
                tool_description="Review market-discovery output quality, citations, verification gaps, and rejected-stock cooldown issues.",
            ),
        ],
    )


def build_market_research_packet(context: ResearchRunContext, subject_id: str, subject_type: str = "theme", topic: str = "") -> MarketResearchPacket:
    normalized_subject_id = subject_id.strip() or slugify(topic)
    normalized_subject_type = subject_type.strip() or "theme"
    manifest = read_manifest(context)
    provider_tasks = matching_market_tasks(manifest.get("provider_tasks", []), normalized_subject_id, normalized_subject_type)
    packets = read_market_packets(context, normalized_subject_id, normalized_subject_type)
    topic_label = topic or topic_from_manifest(manifest, normalized_subject_id) or normalized_subject_id.replace("_", " ")
    source_bucket = source_bucket_from_tasks(provider_tasks)
    lanes = [
        build_lane(lane_id, definition, packets, provider_tasks)
        for lane_id, definition in LANE_DEFINITIONS.items()
    ]
    return MarketResearchPacket(
        run_id=context.run_id,
        subject_type=normalized_subject_type,
        subject_id=normalized_subject_id,
        topic=topic_label,
        source_bucket=source_bucket,
        lanes=lanes,
        evidence_packet_count=len(packets),
        planned_provider_task_ids=[str(task.get("id", "")) for task in provider_tasks if task.get("id")],
        memory_item_ids=list(context.memory_item_ids),
    )


def build_market_research_input(context: ResearchRunContext, subject_id: str, subject_type: str = "theme", topic: str = "") -> str:
    packet = build_market_research_packet(context, subject_id, subject_type, topic)
    return "\n".join(
        [
            f"Review market research topic `{packet.topic}` for run `{packet.run_id}`.",
            "",
            "Use the market research packet below as the deterministic starting point.",
            "Grok/X is mandatory for niche trends, hype, rumors, and early company leads, but must be labeled as social signal.",
            "Exa/web evidence is required to verify material claims and candidate companies before promotion.",
            "Return a structured OrchestratorDecision with alerts, candidate review items, and next-run tasks.",
            "",
            "Market research packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
        ]
    )


def build_market_research_fanout_tasks(
    context: ResearchRunContext,
    subject_id: str,
    subject_type: str = "theme",
    topic: str = "",
    *,
    timeout_seconds: float | None = 300.0,
) -> list[Any]:
    from stock_research.agent_runtime.fanout import AgentFanoutTask

    packet = build_market_research_packet(context, subject_id, subject_type, topic)
    suffix = packet.subject_id.lower()
    return [
        AgentFanoutTask(
            task_id=f"exa_industry_{suffix}",
            agent_id="exa_industry_specialist",
            task="Exa industry research specialist",
            prompt=build_market_research_specialist_prompt(packet, "exa_industry"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"grok_discovery_{suffix}",
            agent_id="grok_discovery_specialist",
            task="xAI Grok industry sentiment specialist",
            prompt=build_market_research_specialist_prompt(packet, "grok_x_discovery"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"discovery_{suffix}",
            agent_id="discovery_specialist",
            task="discovery specialist",
            prompt=build_market_research_specialist_prompt(packet, "candidate_synthesis"),
            timeout_seconds=timeout_seconds,
        ),
        AgentFanoutTask(
            task_id=f"quality_{suffix}",
            agent_id="quality_reviewer_specialist",
            task="quality reviewer specialist",
            prompt=build_market_research_specialist_prompt(packet, "candidate_synthesis"),
            timeout_seconds=timeout_seconds,
        ),
    ]


def run_market_research_sub_orchestrator_sync(
    context: ResearchRunContext,
    subject_id: str,
    subject_type: str = "theme",
    topic: str = "",
    *,
    timeout_seconds: float | None = 300.0,
    runner=None,
):
    from stock_research.agent_runtime.fanout import run_agent_fanout_sync

    tasks = build_market_research_fanout_tasks(context, subject_id, subject_type, topic, timeout_seconds=timeout_seconds)
    kwargs = {"runner": runner} if runner else {}
    fanout = run_agent_fanout_sync(context, tasks, **kwargs)
    return aggregate_market_research(context, subject_id, subject_type, topic, fanout), fanout


def aggregate_market_research(context: ResearchRunContext, subject_id: str, subject_type: str, topic: str, fanout) -> OrchestratorDecision:
    packet = build_market_research_packet(context, subject_id, subject_type, topic)
    specialist_results = [specialist_result_from_output(item.final_output, packet) for item in fanout.results]
    missing_lanes = [lane.lane_id for lane in packet.lanes if lane.status == "missing"]
    fanout_failures = [item.task_id for item in fanout.results if item.status in {"error", "timeout"}]
    blocked_specialists = [result.agent_id for result in specialist_results if result.status in {"blocked", "needs_human_review"}]
    partial_specialists = [result.agent_id for result in specialist_results if result.status == "partial"]
    status = "ready"
    if fanout_failures or missing_lanes or partial_specialists:
        status = "partial"
    if "grok_x_discovery" in missing_lanes or blocked_specialists:
        status = "needs_human_review"
    summary = (
        f"Market research packet for {packet.topic} covers {packet.evidence_packet_count} evidence packet(s), "
        f"{len([lane for lane in packet.lanes if lane.status == 'ready'])} ready lane(s), "
        f"and {len(missing_lanes)} missing lane(s). Grok/X discovery is required for niche trend and rumor coverage, "
        "but all Grok leads require verification before promotion."
    )
    next_tasks = [f"Fill missing market research lane `{lane_id}` for {packet.topic}." for lane_id in missing_lanes]
    next_tasks.extend(f"Review fanout failure `{task_id}` for {packet.topic}." for task_id in fanout_failures)
    next_tasks.extend(f"Review blocked market specialist `{agent_id}` for {packet.topic}." for agent_id in blocked_specialists)
    next_tasks.extend(f"Review partial market specialist `{agent_id}` for {packet.topic}." for agent_id in partial_specialists)
    return OrchestratorDecision(
        agent_id="market_research_orchestrator",
        run_id=context.run_id,
        status=status,
        summary=summary,
        specialist_results=specialist_results,
        next_run_tasks=next_tasks,
        memory_item_ids_used=list(context.memory_item_ids),
    )


def write_market_research_report(context: ResearchRunContext, subject_id: str, subject_type: str, topic: str, decision: OrchestratorDecision, fanout) -> tuple[Path, Path, Path]:
    target_dir = context.run_dir / "market_research"
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_id = slugify(subject_id or topic)
    json_path = target_dir / f"{safe_id}_market_research.json"
    md_path = target_dir / f"{safe_id}_market_research.md"
    metrics_path = target_dir / f"{safe_id}_market_research_metrics.md"
    json_path.write_text(json.dumps({"decision": output_to_dict(decision), "fanout": fanout_to_dict(fanout)}, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(format_market_research_markdown(context, subject_id, subject_type, topic, decision, fanout), encoding="utf-8")
    write_run_metrics(context, list(fanout.metrics), path=metrics_path)
    return json_path, md_path, metrics_path


def fanout_to_dict(fanout) -> dict[str, Any]:
    from stock_research.agent_runtime.fanout import fanout_result_to_dict

    return fanout_result_to_dict(fanout)


def format_market_research_markdown(context: ResearchRunContext, subject_id: str, subject_type: str, topic: str, decision: OrchestratorDecision, fanout) -> str:
    packet = build_market_research_packet(context, subject_id, subject_type, topic)
    lines = [
        f"# Market Research: {packet.topic}",
        "",
        f"- run_id: {context.run_id}",
        f"- subject_type: {packet.subject_type}",
        f"- subject_id: {packet.subject_id}",
        f"- status: {decision.status}",
        f"- fanout_status: {fanout.status}",
        "",
        "## Summary",
        "",
        decision.summary,
        "",
        "## Lanes",
        "",
    ]
    for lane in packet.lanes:
        lines.append(f"- {lane.lane_id}: {lane.status} ({len(lane.evidence_packet_ids)} packet(s))")
        for missing in lane.missing_items:
            lines.append(f"  - missing: {missing}")
    lines.extend(["", "## Specialist Fanout", ""])
    for item in fanout.results:
        lines.append(f"- {item.task_id}: {item.status} via `{item.agent_id}`")
    lines.extend(["", "## Next Run Tasks", ""])
    if decision.next_run_tasks:
        lines.extend(f"- {task}" for task in decision.next_run_tasks)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def build_market_research_specialist_prompt(packet: MarketResearchPacket, lane_id: str) -> str:
    lane = next((item for item in packet.lanes if item.lane_id == lane_id), None)
    return "\n".join(
        [
            f"Review market topic `{packet.topic}` for lane `{lane_id}`.",
            "",
            "Use existing repo/run artifacts only unless explicit tool permission allows otherwise.",
            "For Grok/X: identify niche trends, hype, rumors, and emerging tickers, but label them as social signals.",
            "For Exa/web: verify public-company facts and source-backed claims.",
            "Return a structured SpecialistResult with sources, confidence, alerts, human review items, and next actions.",
            "",
            "Market research packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
            "",
            f"Lane focus: {json.dumps(asdict(lane), sort_keys=True) if lane else 'unknown'}",
        ]
    )


def build_lane(lane_id: str, definition: dict[str, Any], packets: list[EvidencePacket], provider_tasks: list[dict[str, Any]]) -> MarketResearchLane:
    lane_packets = [packet for packet in packets if packet_belongs_to_lane(packet, lane_id)]
    lane_tasks = [task for task in provider_tasks if task_belongs_to_lane(task, lane_id)]
    missing_items = []
    if not lane_packets:
        missing_items.append(str(definition["missing"]))
    status = "ready"
    if missing_items and lane_tasks:
        status = "partial"
    elif missing_items:
        status = "missing"
    return MarketResearchLane(
        lane_id=lane_id,
        status=status,
        summary=f"{lane_id} lane has {len(lane_packets)} evidence packet(s) and {len(lane_tasks)} planned task(s).",
        evidence_packet_ids=[packet.packet_id for packet in lane_packets],
        planned_task_ids=[str(task.get("id", "")) for task in lane_tasks if task.get("id")],
        missing_items=missing_items,
    )


def read_manifest(context: ResearchRunContext) -> dict[str, Any]:
    path = context.manifest_path or context.run_dir / "manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def matching_market_tasks(tasks: list[Any], subject_id: str, subject_type: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if str(task.get("subject_id", "")) == subject_id and str(task.get("subject_type", "")) == subject_type:
            result.append(task)
    return result


def read_market_packets(context: ResearchRunContext, subject_id: str, subject_type: str) -> list[EvidencePacket]:
    evidence_dir = context.run_dir / "evidence_packets"
    if not evidence_dir.exists():
        return []
    packets: list[EvidencePacket] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            packet = read_packet(path)
        except Exception:
            continue
        if packet.subject_id == subject_id and packet.subject_type == subject_type:
            packets.append(packet)
    return packets


def task_belongs_to_lane(task: dict[str, Any], lane_id: str) -> bool:
    provider = str(task.get("provider", ""))
    task_id = str(task.get("id", ""))
    args = task.get("args", {}) if isinstance(task.get("args", {}), dict) else {}
    mode = str(args.get("mode", ""))
    if lane_id == "exa_industry":
        return provider == "exa" and mode in {"industry", "general", "news"}
    if lane_id == "exa_company_discovery":
        return provider == "exa" and mode == "company"
    if lane_id == "grok_x_discovery":
        return provider == "xai_grok" or "x_search" in task_id
    if lane_id == "candidate_synthesis":
        return "discovery" in task_id
    return False


def packet_belongs_to_lane(packet: EvidencePacket, lane_id: str) -> bool:
    packet_id = packet.packet_id.lower()
    if lane_id == "exa_industry":
        return packet.provider == "exa" and "exa_discovery" not in packet_id and "company" not in packet_id
    if lane_id == "exa_company_discovery":
        return packet.provider == "exa" and ("exa_discovery" in packet_id or "company" in packet_id)
    if lane_id == "grok_x_discovery":
        return packet.provider == "xai_grok"
    if lane_id == "candidate_synthesis":
        return bool(packet.recommended_updates or packet.claims)
    return False


def topic_from_manifest(manifest: dict[str, Any], subject_id: str) -> str:
    for priority in manifest.get("inputs", {}).get("research_priorities", []) or []:
        if slugify(str(priority.get("Topic", ""))) == subject_id:
            return str(priority.get("Topic", ""))
    return ""


def source_bucket_from_tasks(tasks: list[dict[str, Any]]) -> str:
    buckets = [str(task.get("source_bucket", "")) for task in tasks if task.get("source_bucket")]
    return buckets[0] if buckets else ""


def specialist_result_from_output(output: Any, packet: MarketResearchPacket) -> SpecialistResult:
    data = output_to_dict(output)
    return SpecialistResult(
        agent_id=str(data.get("agent_id", "unknown_specialist")),
        subject_type=str(data.get("subject_type", packet.subject_type)),
        subject_id=str(data.get("subject_id", packet.subject_id)),
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


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "unknown"
