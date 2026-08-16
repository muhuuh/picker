from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ResearchWritePermissions:
    run_artifacts: bool
    reader_reports: bool
    human_input_queue: bool
    human_review_queue: bool
    factual_company_updates: bool
    category_state_updates: bool
    portfolio_membership: bool
    strategy: bool
    trade_execution: bool = False


@dataclass(frozen=True)
class ResearchProfile:
    profile_id: str
    purpose: str
    subject_types: tuple[str, ...]
    default_time_window_days: int
    provider_lanes: tuple[str, ...]
    depth: str
    output_contract: str
    materiality_rules: tuple[str, ...]
    write_permissions: ResearchWritePermissions


@dataclass(frozen=True)
class ResearchRunSpec:
    spec_version: int
    run_id: str
    request_id: str
    request: str
    profile: ResearchProfile
    subjects: tuple[dict[str, str], ...]
    status: str = "planned"


RESEARCH_PROFILES: dict[str, ResearchProfile] = {
    "portfolio_update": ResearchProfile(
        profile_id="portfolio_update",
        purpose="Recurring delta-first update for holdings, monitoring names, and portfolio industries.",
        subject_types=("portfolio", "company", "industry", "theme"),
        default_time_window_days=14,
        provider_lanes=(
            "financial_and_market_data",
            "filings_and_company_ir",
            "exa_current_web_and_news",
            "grok_x_community_and_experts",
            "portfolio_industry_context",
        ),
        depth="delta_first_materiality_triggered",
        output_contract="reports/portfolio_update/portfolio_executive_update.md",
        materiality_rules=(
            "Lead with changes since the last accepted run.",
            "Write a deep company report only for material changes, blocking gaps, or an explicit request.",
            "Require coverage evidence before claiming no material change.",
        ),
        write_permissions=ResearchWritePermissions(
            run_artifacts=True,
            reader_reports=True,
            human_input_queue=True,
            human_review_queue=True,
            factual_company_updates=True,
            category_state_updates=True,
            portfolio_membership=False,
            strategy=False,
        ),
    ),
    "company_deep_research": ResearchProfile(
        profile_id="company_deep_research",
        purpose="On-demand company research from first principles without changing tracking state.",
        subject_types=("company",),
        default_time_window_days=30,
        provider_lanes=(
            "financial_and_market_data",
            "filings_and_company_ir",
            "exa_company_web_and_news",
            "grok_x_community_and_experts",
            "industry_and_competitor_context",
        ),
        depth="full_company_deep_dive",
        output_contract="reports/company_deep_research/{subject_id}_deep_research.md",
        materiality_rules=(
            "Answer the user's question directly.",
            "Separate verified facts, social narrative, inference, and speculation.",
            "Do not infer a monitoring, holding, rejection, thesis, or trade decision.",
        ),
        write_permissions=ResearchWritePermissions(
            run_artifacts=True,
            reader_reports=True,
            human_input_queue=True,
            human_review_queue=False,
            factual_company_updates=False,
            category_state_updates=False,
            portfolio_membership=False,
            strategy=False,
        ),
    ),
    "industry_deep_research": ResearchProfile(
        profile_id="industry_deep_research",
        purpose="On-demand industry or theme research without creating a recurring priority.",
        subject_types=("industry", "theme"),
        default_time_window_days=30,
        provider_lanes=(
            "exa_industry_web_and_news",
            "exa_primary_source_contents",
            "grok_x_expert_and_community_discovery",
            "company_and_value_chain_discovery",
            "candidate_verification",
        ),
        depth="full_industry_deep_dive",
        output_contract="reports/industry_deep_research/{subject_id}_deep_research.md",
        materiality_rules=(
            "Explain the value chain, current change, investable read-throughs, and unresolved gaps.",
            "Keep discovered companies as research leads until separately verified and approved.",
            "Do not create a recurring strategy priority from a one-off research request.",
        ),
        write_permissions=ResearchWritePermissions(
            run_artifacts=True,
            reader_reports=True,
            human_input_queue=True,
            human_review_queue=False,
            factual_company_updates=False,
            category_state_updates=False,
            portfolio_membership=False,
            strategy=False,
        ),
    ),
    "candidate_discovery": ResearchProfile(
        profile_id="candidate_discovery",
        purpose="Discover and verify possible stocks without promoting them into monitoring.",
        subject_types=("industry", "theme", "company"),
        default_time_window_days=30,
        provider_lanes=(
            "exa_company_and_source_discovery",
            "grok_x_early_signals",
            "candidate_identity_normalization",
            "candidate_verification",
        ),
        depth="discovery_then_approval_gated_verification",
        output_contract="market_research/{subject_id}_manual_market_research.md",
        materiality_rules=(
            "Grok-only leads remain unverified.",
            "Promotion requires source-backed verification and explicit human approval.",
            "Rejected-stock cooldowns remain in force.",
        ),
        write_permissions=ResearchWritePermissions(
            run_artifacts=True,
            reader_reports=True,
            human_input_queue=True,
            human_review_queue=True,
            factual_company_updates=False,
            category_state_updates=False,
            portfolio_membership=False,
            strategy=False,
        ),
    ),
}


def list_research_profiles() -> tuple[ResearchProfile, ...]:
    return tuple(RESEARCH_PROFILES[key] for key in sorted(RESEARCH_PROFILES))


def get_research_profile(profile_id: str) -> ResearchProfile:
    normalized = str(profile_id or "").strip().lower().replace("-", "_")
    try:
        return RESEARCH_PROFILES[normalized]
    except KeyError as exc:
        raise ValueError(
            f"Unknown research profile `{profile_id}`. Available profiles: {', '.join(sorted(RESEARCH_PROFILES))}."
        ) from exc


def build_research_run_spec(
    profile_id: str,
    *,
    run_id: str,
    request_id: str,
    request: str,
    subjects: Iterable[dict[str, str]],
) -> ResearchRunSpec:
    profile = get_research_profile(profile_id)
    normalized_subjects = tuple(normalize_subject(subject) for subject in subjects)
    if not normalized_subjects:
        raise ValueError(f"Research profile `{profile.profile_id}` requires at least one subject.")
    invalid_types = sorted(
        {
            subject["subject_type"]
            for subject in normalized_subjects
            if subject["subject_type"] not in profile.subject_types
        }
    )
    if invalid_types:
        raise ValueError(
            f"Research profile `{profile.profile_id}` does not support subject type(s): {', '.join(invalid_types)}."
        )
    return ResearchRunSpec(
        spec_version=1,
        run_id=run_id.strip(),
        request_id=request_id.strip(),
        request=request.strip(),
        profile=profile,
        subjects=normalized_subjects,
    )


def write_research_run_spec(root: Path, spec: ResearchRunSpec) -> Path:
    assert_write_allowed(spec.profile, "run_artifacts")
    run_dir = root.resolve() / "agents" / "runs" / spec.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "research_run_spec.json"
    path.write_text(json.dumps(research_run_spec_to_dict(spec), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def research_run_spec_to_dict(spec: ResearchRunSpec) -> dict[str, Any]:
    return asdict(spec)


def assert_write_allowed(profile: ResearchProfile, permission: str) -> None:
    if not hasattr(profile.write_permissions, permission):
        raise ValueError(f"Unknown research write permission `{permission}`.")
    if not bool(getattr(profile.write_permissions, permission)):
        raise PermissionError(
            f"Research profile `{profile.profile_id}` does not permit `{permission}` writes. "
            "Use an explicit approval/status-change workflow instead."
        )


def normalize_subject(subject: dict[str, str]) -> dict[str, str]:
    subject_type = str(subject.get("subject_type", "")).strip().lower()
    subject_id = str(subject.get("subject_id", "")).strip()
    if not subject_type or not subject_id:
        raise ValueError("Research subjects require non-empty subject_type and subject_id values.")
    return {
        "subject_type": subject_type,
        "subject_id": subject_id,
        "label": str(subject.get("label", subject_id)).strip() or subject_id,
    }
