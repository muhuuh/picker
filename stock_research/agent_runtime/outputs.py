from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Confidence = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high", "critical"]
DecisionStatus = Literal["ready", "partial", "needs_human_review", "blocked"]
VerificationStatus = Literal[
    "verified",
    "partially_verified",
    "grok_only",
    "exa_only",
    "unverified",
    "cooldown_blocked",
]
CandidateNextAction = Literal["ignore", "verify", "add_to_monitoring", "human_review", "reject"]
HypeLevel = Literal["low", "medium", "high", "unknown"]


@dataclass
class SourceReference:
    source_id: str
    title: str = ""
    url: str = ""
    artifact_path: str = ""
    confidence: Confidence = "medium"


@dataclass
class AlertProposal:
    subject_type: str
    subject_id: str
    title: str
    summary: str
    severity: Severity = "medium"
    confidence: Confidence = "medium"
    source_ids: list[str] = field(default_factory=list)
    needs_human_review: bool = False


@dataclass
class FileUpdateProposal:
    target_file: str
    update_type: str
    summary: str
    confidence: Confidence = "medium"
    source_ids: list[str] = field(default_factory=list)
    needs_human_review: bool = True


@dataclass
class HumanReviewItem:
    title: str
    question: str
    reason: str
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    source_ids: list[str] = field(default_factory=list)


@dataclass
class SpecialistResult:
    agent_id: str
    subject_type: str
    subject_id: str
    status: DecisionStatus
    summary: str
    confidence: Confidence = "medium"
    sources: list[SourceReference] = field(default_factory=list)
    alerts: list[AlertProposal] = field(default_factory=list)
    file_update_proposals: list[FileUpdateProposal] = field(default_factory=list)
    human_review_items: list[HumanReviewItem] = field(default_factory=list)
    memory_item_ids_used: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


@dataclass
class CandidateLead:
    ticker: str = ""
    company_name: str = ""
    exchange: str = ""
    country: str = ""
    sector: str = ""
    industry: str = ""
    why_surfaced: str = ""
    source_channels: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    hype_level: HypeLevel = "unknown"
    sentiment: str = "unknown"
    verification_status: VerificationStatus = "unverified"
    strategy_fit: str = "unknown"
    rejected_cooldown_status: str = "not_rejected"
    next_action: CandidateNextAction = "verify"
    rumor_flag: bool = False
    needs_human_review: bool = True
    notes: str = ""


@dataclass
class OrchestratorDecision:
    agent_id: str
    run_id: str
    status: DecisionStatus
    summary: str
    specialist_results: list[SpecialistResult] = field(default_factory=list)
    alerts: list[AlertProposal] = field(default_factory=list)
    file_update_proposals: list[FileUpdateProposal] = field(default_factory=list)
    human_review_items: list[HumanReviewItem] = field(default_factory=list)
    candidate_leads: list[CandidateLead] = field(default_factory=list)
    next_run_tasks: list[str] = field(default_factory=list)
    memory_item_ids_used: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompanyResearchLane:
    lane_id: str
    status: Literal["ready", "partial", "missing"]
    summary: str
    evidence_packet_ids: list[str] = field(default_factory=list)
    report_paths: list[str] = field(default_factory=list)
    planned_task_ids: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CompanyResearchPacket:
    run_id: str
    ticker: str
    stock_bucket: str = ""
    stock_info_file: str = ""
    lanes: list[CompanyResearchLane] = field(default_factory=list)
    evidence_packet_count: int = 0
    planned_provider_task_ids: list[str] = field(default_factory=list)
    planned_analysis_task_ids: list[str] = field(default_factory=list)
    memory_item_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketResearchLane:
    lane_id: str
    status: Literal["ready", "partial", "missing"]
    summary: str
    evidence_packet_ids: list[str] = field(default_factory=list)
    planned_task_ids: list[str] = field(default_factory=list)
    missing_items: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MarketResearchPacket:
    run_id: str
    subject_type: str
    subject_id: str
    topic: str
    source_bucket: str = ""
    lanes: list[MarketResearchLane] = field(default_factory=list)
    evidence_packet_count: int = 0
    planned_provider_task_ids: list[str] = field(default_factory=list)
    memory_item_ids: list[str] = field(default_factory=list)
