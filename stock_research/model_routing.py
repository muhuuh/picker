from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .repo import find_repo_root


MODEL_ROUTING_PATH = Path("agents/model_routing.yaml")

DEFAULTS: dict[str, str] = {
    "openai_strong": "gpt-5.5",
    "openai_balanced": "gpt-5.4-mini",
    "openai_fast": "gpt-5.4-mini",
    "openai_nano": "gpt-5.4-mini",
    "xai_grok_x_search": "grok-4.6",
    "codex_manual_model": "gpt-5.5",
    "codex_manual_reasoning": "high",
}

BLOCKED_LEGACY_MODELS = {
    "gpt-4.1",
    "gpt-4.1-2025-04-14",
    "gpt_4_1",
    "gpt_4_1_2025_04_14",
}

DEFAULT_ROUTES: dict[str, dict[str, str]] = {
    "main_orchestrator": {"provider": "openai", "model_tier": "strong", "complexity": "high"},
    "company_research_orchestrator": {"provider": "openai", "model_tier": "strong", "complexity": "high"},
    "market_research_orchestrator": {"provider": "openai", "model_tier": "strong", "complexity": "high"},
    "opportunity_assessment_specialist": {"provider": "openai", "model_tier": "strong", "complexity": "high"},
    "risk_thesis_specialist": {"provider": "openai", "model_tier": "strong", "complexity": "high"},
    "discovery_specialist": {"provider": "openai", "model_tier": "balanced", "complexity": "medium_high"},
    "grok_discovery_specialist": {"provider": "openai", "model_tier": "balanced", "complexity": "medium_high"},
    "sentiment_specialist": {"provider": "openai", "model_tier": "balanced", "complexity": "medium_high"},
    "company_search_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "company_news_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "financial_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "filing_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "exa_industry_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "writer_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "low_medium"},
    "quality_reviewer_specialist": {"provider": "openai", "model_tier": "fast", "complexity": "low_medium"},
    "portfolio_review_orchestrator": {"provider": "openai", "model_tier": "fast", "complexity": "medium"},
    "memory_evaluation_orchestrator": {"provider": "openai", "model_tier": "fast", "complexity": "low_medium"},
    "memory_writer": {"provider": "openai", "model_tier": "fast", "complexity": "low_medium"},
    "xai_stock_sentiment": {"provider": "xai", "model_tier": "grok_x_search", "complexity": "high"},
    "xai_industry_discovery": {"provider": "xai", "model_tier": "grok_x_search", "complexity": "high"},
    "xai_latest_news": {"provider": "xai", "model_tier": "grok_x_search", "complexity": "medium_high"},
    "xai_company_deep_dive": {"provider": "xai", "model_tier": "grok_x_search", "complexity": "medium_high"},
}

TASK_ROUTE_ALIASES: tuple[tuple[str, str], ...] = (
    ("main orchestrator", "main_orchestrator"),
    ("company research", "company_research_orchestrator"),
    ("market research", "market_research_orchestrator"),
    ("portfolio review", "portfolio_review_orchestrator"),
    ("memory evaluation", "memory_evaluation_orchestrator"),
    ("opportunity assessment", "opportunity_assessment_specialist"),
    ("risk thesis", "risk_thesis_specialist"),
    ("quality reviewer", "quality_reviewer_specialist"),
    ("writer", "writer_specialist"),
    ("company news", "company_news_specialist"),
    ("company search", "company_search_specialist"),
    ("financial", "financial_specialist"),
    ("filing", "filing_specialist"),
    ("sec filing", "filing_specialist"),
    ("grok", "grok_discovery_specialist"),
    ("sentiment", "sentiment_specialist"),
    ("exa industry", "exa_industry_specialist"),
    ("discovery", "discovery_specialist"),
)


@dataclass(frozen=True)
class ModelRoute:
    route_id: str
    provider: str
    model_tier: str
    model: str
    complexity: str
    source: str
    codex_preferred_when_manual: bool = False
    codex_manual_model: str = ""
    codex_manual_reasoning: str = ""


def resolve_model_for_route(
    root: Path | None,
    route_or_task: str,
    *,
    explicit_model: str | None = None,
) -> ModelRoute:
    config = load_model_routing_config(root)
    route_id = normalize_route_id(route_or_task, config)
    routes = merged_routes(config)
    defaults = merged_defaults(config)
    route = routes.get(route_id, routes.get("main_orchestrator", DEFAULT_ROUTES["main_orchestrator"]))
    provider = str(route.get("provider", "openai"))
    tier = str(route.get("model_tier", "strong"))
    complexity = str(route.get("complexity", "medium"))
    codex_preferred = truthy(route.get("codex_preferred_when_manual", False))

    if explicit_model:
        model = explicit_model
        source = "explicit"
    else:
        env_model = route_env_model(route_id)
        if env_model:
            model = env_model
            source = f"env:{route_env_name(route_id)}"
        else:
            tier_env = tier_env_model(provider, tier)
            if tier_env:
                model = tier_env
                source = f"env:{tier_env_name(provider, tier)}"
            else:
                model = default_model_for_provider_tier(defaults, provider, tier)
                source = "config" if config else "built_in"

    validate_resolved_model(model, source)
    return ModelRoute(
        route_id=route_id,
        provider=provider,
        model_tier=tier,
        model=model,
        complexity=complexity,
        source=source,
        codex_preferred_when_manual=codex_preferred,
        codex_manual_model=str(defaults.get("codex_manual_model", DEFAULTS["codex_manual_model"])),
        codex_manual_reasoning=str(defaults.get("codex_manual_reasoning", DEFAULTS["codex_manual_reasoning"])),
    )


def load_model_routing_config(root: Path | None = None) -> dict[str, Any]:
    try:
        repo_root = find_repo_root(root)
    except FileNotFoundError:
        return {}
    path = repo_root / MODEL_ROUTING_PATH
    if not path.exists():
        return {}
    return parse_simple_yaml(path.read_text(encoding="utf-8"))


def merged_defaults(config: dict[str, Any]) -> dict[str, str]:
    values = dict(DEFAULTS)
    for key, value in dict(config.get("defaults", {})).items():
        values[str(key)] = str(value)
    return values


def merged_routes(config: dict[str, Any]) -> dict[str, dict[str, Any]]:
    values = {key: dict(value) for key, value in DEFAULT_ROUTES.items()}
    for key, value in dict(config.get("routes", {})).items():
        route_id = str(key)
        if isinstance(value, dict):
            values[route_id] = {**values.get(route_id, {}), **value}
    return values


def normalize_route_id(value: str, config: dict[str, Any] | None = None) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    routes = set(DEFAULT_ROUTES)
    if config:
        routes.update(str(key) for key in dict(config.get("routes", {})))
    if normalized in routes:
        return normalized
    label = str(value or "").strip().lower().replace("_", " ")
    for needle, route_id in TASK_ROUTE_ALIASES:
        if needle in label:
            return route_id
    return normalized or "main_orchestrator"


def default_model_for_provider_tier(defaults: dict[str, str], provider: str, tier: str) -> str:
    if provider == "xai":
        return defaults.get("xai_grok_x_search", DEFAULTS["xai_grok_x_search"])
    key = f"openai_{tier}"
    return defaults.get(key, defaults.get("openai_strong", DEFAULTS["openai_strong"]))


def validate_resolved_model(model: str, source: str) -> None:
    normalized = model.strip().lower().replace("-", "_")
    if model.strip().lower() in BLOCKED_LEGACY_MODELS or normalized in BLOCKED_LEGACY_MODELS:
        raise ValueError(
            f"Resolved blocked legacy model `{model}` from {source}. "
            "Use agents/model_routing.yaml or STOCK_RESEARCH_OPENAI_*_MODEL to select an approved GPT-5.x model."
        )


def route_env_name(route_id: str) -> str:
    return f"STOCK_RESEARCH_MODEL_{route_id.upper().replace('-', '_')}"


def route_env_model(route_id: str) -> str:
    return os.getenv(route_env_name(route_id), "").strip()


def tier_env_name(provider: str, tier: str) -> str:
    if provider == "xai":
        return "STOCK_RESEARCH_XAI_GROK_MODEL"
    return f"STOCK_RESEARCH_OPENAI_{tier.upper()}_MODEL"


def tier_env_model(provider: str, tier: str) -> str:
    return os.getenv(tier_env_name(provider, tier), "").strip()


def truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_simple_yaml(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        line = raw_line.strip()
        if ":" not in line:
            continue
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if not raw_value:
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = parse_scalar(raw_value)
    return root


def parse_scalar(value: str) -> Any:
    normalized = value.strip().strip('"').strip("'")
    lowered = normalized.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    return normalized


def model_route_to_dict(route: ModelRoute) -> dict[str, Any]:
    return {
        "route_id": route.route_id,
        "provider": route.provider,
        "model_tier": route.model_tier,
        "model": route.model,
        "complexity": route.complexity,
        "source": route.source,
        "codex_preferred_when_manual": route.codex_preferred_when_manual,
        "codex_manual_model": route.codex_manual_model,
        "codex_manual_reasoning": route.codex_manual_reasoning,
    }
