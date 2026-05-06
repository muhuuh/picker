from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .memory import ITEM_MEMORY_FILES, format_memory_context_for_prompt, load_memory_state, validate_memory_fields
from .memory_updates import (
    MemoryUpdateDraft,
    MemoryUpdateDraftItem,
    build_memory_update_draft,
    memory_update_draft_to_dict,
    write_memory_update_draft,
)
from .repo import find_repo_root


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MEMORY_WRITER_MODEL = "gpt-5.4-mini"


class MemoryWriterError(RuntimeError):
    pass


@dataclass(frozen=True)
class MemoryWriterPrompt:
    run_id: str
    generated_at: str
    instructions: str
    input_payload: dict[str, Any]


@dataclass(frozen=True)
class MemoryWriterRecommendation:
    proposal_id: str
    decision: str
    target_file: str
    reason: str
    fields: dict[str, str] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryWriterReview:
    run_id: str
    generated_at: str
    mode: str
    model: str
    recommendations: list[MemoryWriterRecommendation] = field(default_factory=list)


def build_memory_writer_prompt(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
) -> MemoryWriterPrompt:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    draft = build_memory_update_draft(repo_root, run_id, today)
    memory_context = format_memory_context_for_prompt(load_memory_state(repo_root), "learning memory writer", max_items=30)
    instructions = memory_writer_instructions()
    return MemoryWriterPrompt(
        run_id=run_id,
        generated_at=today.isoformat(),
        instructions=instructions,
        input_payload={
            "run_id": run_id,
            "memory_context": memory_context,
            "memory_update_draft": memory_update_draft_to_dict(draft),
            "allowed_target_files": list(ITEM_MEMORY_FILES),
            "required_fields": [
                "id",
                "date",
                "type",
                "scope",
                "status",
                "confidence",
                "trigger/source",
                "lesson",
                "use_when",
                "do_not_use_when",
                "evidence",
                "owner",
                "next_review",
            ],
            "guardrails": [
                "Do not store secrets.",
                "Do not store raw provider output.",
                "Do not store ordinary company investment facts.",
                "Prefer updating/rejecting duplicates over adding duplicate lessons.",
                "Keep lessons short, actionable, and evidence-backed.",
            ],
        },
    )


def write_memory_writer_prompt(root: Path | None, prompt: MemoryWriterPrompt) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / prompt.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "memory_writer_prompt.json"
    md_path = run_dir / "memory_writer_prompt.md"
    json_path.write_text(json.dumps(memory_writer_prompt_to_dict(prompt), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_memory_writer_prompt_markdown(prompt), encoding="utf-8")
    return json_path, md_path


def build_memory_writer_review(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
    execute: bool = False,
    model: str = DEFAULT_MEMORY_WRITER_MODEL,
    api_key: str | None = None,
    update_drafts: bool = False,
    responder=None,
    write_artifacts: bool = False,
) -> tuple[MemoryWriterReview, list[Path]]:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    prompt = build_memory_writer_prompt(repo_root, run_id, today)
    paths: list[Path] = []
    if write_artifacts:
        paths.extend(write_memory_writer_prompt(repo_root, prompt))
    draft = build_memory_update_draft(repo_root, run_id, today)

    if execute:
        response = call_openai_memory_writer(prompt, model=model, api_key=api_key, responder=responder)
        raw_recommendations = response.get("recommendations", [])
        mode = "openai_responses"
    else:
        raw_recommendations = deterministic_recommendations(draft)
        mode = "deterministic_review"

    recommendations = validate_writer_recommendations(draft, raw_recommendations)
    review = MemoryWriterReview(
        run_id=run_id,
        generated_at=today.isoformat(),
        mode=mode,
        model=model if execute else "none",
        recommendations=recommendations,
    )
    if write_artifacts:
        paths.extend(write_memory_writer_review(repo_root, review))
    if update_drafts:
        updated_draft = build_draft_from_writer_review(draft, review)
        paths.extend(write_memory_update_draft(repo_root, updated_draft))
    return review, paths


def call_openai_memory_writer(
    prompt: MemoryWriterPrompt,
    model: str = DEFAULT_MEMORY_WRITER_MODEL,
    api_key: str | None = None,
    responder=None,
) -> dict[str, Any]:
    resolved_key = api_key or os.getenv("OPENAI_API_KEY")
    if not resolved_key:
        raise MemoryWriterError("OpenAI memory writer requires OPENAI_API_KEY or --api-key when --execute is used.")
    payload = {
        "model": model,
        "store": False,
        "input": [
            {"role": "system", "content": prompt.instructions},
            {"role": "user", "content": json.dumps(prompt.input_payload, sort_keys=True)},
        ],
        "text": {"format": memory_writer_response_format()},
    }
    if responder:
        response = responder(payload)
    else:
        response = post_openai_response(resolved_key, payload)
    text = extract_response_text(response)
    if not text:
        raise MemoryWriterError("OpenAI memory writer response did not contain output text.")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise MemoryWriterError(f"OpenAI memory writer returned invalid JSON: {exc}") from exc


def post_openai_response(api_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Picker Stock Research/0.1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise MemoryWriterError(f"OpenAI memory writer failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise MemoryWriterError(f"OpenAI memory writer failed: {exc.reason}") from exc


def extract_response_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]
    for output in response.get("output", []):
        for content in output.get("content", []):
            if isinstance(content.get("text"), str):
                return content["text"]
    return ""


def deterministic_recommendations(draft: MemoryUpdateDraft) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for item in draft.items:
        recommendations.append(
            {
                "proposal_id": item.proposal_id,
                "decision": "accept" if item.status == "ready" else "reject",
                "target_file": item.target_file,
                "reason": "Ready draft passes deterministic validation." if item.status == "ready" else "; ".join(item.issues),
                "fields": item.fields,
            }
        )
    return recommendations


def validate_writer_recommendations(
    draft: MemoryUpdateDraft,
    raw_recommendations: list[dict[str, Any]],
) -> list[MemoryWriterRecommendation]:
    draft_by_id = {item.proposal_id: item for item in draft.items}
    recommendations: list[MemoryWriterRecommendation] = []
    for raw in raw_recommendations:
        proposal_id = str(raw.get("proposal_id", ""))
        decision = str(raw.get("decision", "")).strip().lower()
        target_file = str(raw.get("target_file", "")).strip()
        fields = {str(key): str(value) for key, value in dict(raw.get("fields", {})).items()}
        issues: list[str] = []

        original = draft_by_id.get(proposal_id)
        if not original:
            issues.append("Unknown proposal_id.")
        if decision not in {"accept", "revise", "reject"}:
            issues.append(f"Invalid decision: {decision}")
        if target_file not in ITEM_MEMORY_FILES:
            issues.append(f"Invalid target_file: {target_file}")
        if decision == "accept" and original:
            fields = dict(original.fields)
            target_file = original.target_file
        elif decision in {"revise", "reject"} and not fields and original:
            fields = dict(original.fields)

        if decision in {"accept", "revise"}:
            try:
                validate_memory_fields(fields)
            except ValueError as exc:
                issues.append(str(exc))

        recommendations.append(
            MemoryWriterRecommendation(
                proposal_id=proposal_id,
                decision=decision,
                target_file=target_file,
                reason=str(raw.get("reason", "")),
                fields=fields,
                issues=issues,
            )
        )
    missing = set(draft_by_id) - {item.proposal_id for item in recommendations}
    for proposal_id in sorted(missing):
        original = draft_by_id[proposal_id]
        recommendations.append(
            MemoryWriterRecommendation(
                proposal_id=proposal_id,
                decision="reject",
                target_file=original.target_file,
                reason="Memory writer returned no recommendation for this proposal.",
                fields=dict(original.fields),
                issues=["Missing recommendation."],
            )
        )
    return recommendations


def build_draft_from_writer_review(draft: MemoryUpdateDraft, review: MemoryWriterReview) -> MemoryUpdateDraft:
    original_by_id = {item.proposal_id: item for item in draft.items}
    items: list[MemoryUpdateDraftItem] = []
    for recommendation in review.recommendations:
        original = original_by_id.get(recommendation.proposal_id)
        if not original:
            continue
        if recommendation.decision in {"accept", "revise"} and not recommendation.issues:
            items.append(
                MemoryUpdateDraftItem(
                    proposal_id=recommendation.proposal_id,
                    action=original.action,
                    target_file=recommendation.target_file,
                    status="ready",
                    reason=recommendation.reason or original.reason,
                    fields=recommendation.fields,
                    issues=[],
                )
            )
        else:
            items.append(
                MemoryUpdateDraftItem(
                    proposal_id=recommendation.proposal_id,
                    action=original.action,
                    target_file=original.target_file,
                    status="rejected" if recommendation.decision == "reject" else "blocked",
                    reason=recommendation.reason or original.reason,
                    fields=recommendation.fields or original.fields,
                    issues=recommendation.issues or [f"Writer decision: {recommendation.decision}"],
                )
            )
    return MemoryUpdateDraft(
        run_id=draft.run_id,
        generated_at=review.generated_at,
        source_files=draft.source_files + [f"agents/runs/{draft.run_id}/memory_writer_review.json"],
        items=items,
    )


def write_memory_writer_review(root: Path | None, review: MemoryWriterReview) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / review.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "memory_writer_review.json"
    md_path = run_dir / "memory_writer_review.md"
    json_path.write_text(json.dumps(memory_writer_review_to_dict(review), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_memory_writer_review_markdown(review), encoding="utf-8")
    return json_path, md_path


def memory_writer_prompt_to_dict(prompt: MemoryWriterPrompt) -> dict[str, Any]:
    return asdict(prompt)


def memory_writer_review_to_dict(review: MemoryWriterReview) -> dict[str, Any]:
    return {
        "run_id": review.run_id,
        "generated_at": review.generated_at,
        "mode": review.mode,
        "model": review.model,
        "recommendations": [asdict(recommendation) for recommendation in review.recommendations],
    }


def format_memory_writer_prompt_markdown(prompt: MemoryWriterPrompt) -> str:
    return "\n".join(
        [
            f"# Memory Writer Prompt: {prompt.run_id}",
            "",
            f"Generated: {prompt.generated_at}",
            "",
            "## Instructions",
            "",
            prompt.instructions,
            "",
            "## Input Payload",
            "",
            "```json",
            json.dumps(prompt.input_payload, indent=2, sort_keys=True),
            "```",
        ]
    ).rstrip() + "\n"


def format_memory_writer_review_markdown(review: MemoryWriterReview) -> str:
    lines = [
        f"# Memory Writer Review: {review.run_id}",
        "",
        f"Generated: {review.generated_at}",
        f"Mode: {review.mode}",
        f"Model: {review.model}",
        "",
        "## Recommendations",
        "",
    ]
    if not review.recommendations:
        lines.append("- No recommendations.")
        lines.append("")
    for recommendation in review.recommendations:
        lines.append(f"### {recommendation.proposal_id}")
        lines.append("")
        lines.append(f"- decision: {recommendation.decision}")
        lines.append(f"- target_file: {recommendation.target_file}")
        lines.append(f"- reason: {recommendation.reason}")
        if recommendation.issues:
            lines.append(f"- issues: {'; '.join(recommendation.issues)}")
        if recommendation.fields:
            lines.append(f"- item_id: {recommendation.fields.get('id', '')}")
            lines.append(f"- lesson: {recommendation.fields.get('lesson', '')}")
            lines.append(f"- evidence: {recommendation.fields.get('evidence', '')}")
        lines.append("")
    lines.extend(
        [
            "## Apply",
            "",
            "This review does not write operational memory directly. If drafts were updated, apply approved ready drafts with:",
            "",
            "```powershell",
            f"python -m stock_research memory apply-updates --run-id {review.run_id} --proposal-id PROPOSAL_ID",
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def memory_writer_instructions() -> str:
    return (
        "You are a bounded operational memory writer for a stock research automation repo. "
        "Return JSON only. Review proposed memory update drafts. Accept good drafts, revise drafts that are too verbose "
        "or not actionable, and reject duplicates, raw provider facts, secrets, ordinary company facts, or unsupported items. "
        "Do not invent evidence. Keep lessons short, operational, and scoped to agent behavior, workflow quality, source quality, "
        "or evaluation. Your output is still only a recommendation; deterministic validation and apply commands control writes."
    )


def memory_writer_response_format() -> dict[str, Any]:
    field_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "id": {"type": "string"},
            "date": {"type": "string"},
            "type": {"type": "string"},
            "scope": {"type": "string"},
            "status": {"type": "string"},
            "confidence": {"type": "string"},
            "trigger/source": {"type": "string"},
            "lesson": {"type": "string"},
            "use_when": {"type": "string"},
            "do_not_use_when": {"type": "string"},
            "evidence": {"type": "string"},
            "owner": {"type": "string"},
            "next_review": {"type": "string"},
        },
        "required": [
            "id",
            "date",
            "type",
            "scope",
            "status",
            "confidence",
            "trigger/source",
            "lesson",
            "use_when",
            "do_not_use_when",
            "evidence",
            "owner",
            "next_review",
        ],
    }
    return {
        "type": "json_schema",
        "name": "memory_writer_review",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "recommendations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "proposal_id": {"type": "string"},
                            "decision": {"type": "string", "enum": ["accept", "revise", "reject"]},
                            "target_file": {"type": "string"},
                            "reason": {"type": "string"},
                            "fields": field_schema,
                        },
                        "required": ["proposal_id", "decision", "target_file", "reason", "fields"],
                    },
                }
            },
            "required": ["recommendations"],
        },
    }
