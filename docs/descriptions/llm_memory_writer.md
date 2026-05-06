# Bounded LLM Memory Writer

Last updated: 2026-05-05

## Purpose

The bounded LLM memory writer reviews memory update drafts and helps improve the wording, scope, and usefulness of operational memory items.

Implementation: `stock_research/memory_llm_writer.py`.

It does not directly write to `agents/memory/*.md`.

## Official OpenAI Docs Reviewed

- Responses API: https://platform.openai.com/docs/api-reference/responses
- Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs

The implementation uses the Responses API shape with Structured Outputs when `--execute` is passed.

OpenAI's current API reference documents `text.format` on Responses API calls, and the Structured Outputs guide documents strict JSON schema output. The memory writer uses that pattern and also re-validates the returned JSON locally before it can update drafts.

## Workflow

```text
memory reflect-run / recurring-failures
  -> memory draft-updates
  -> memory writer-review
  -> optional draft update
  -> human/Codex approval
  -> memory apply-updates
  -> memory validate
```

## Commands

Build the prompt without calling an LLM:

```powershell
python -m stock_research memory writer-prompt --run-id 2026-05-09_weekly --write
```

Run deterministic writer review without an LLM:

```powershell
python -m stock_research memory writer-review --run-id 2026-05-09_weekly --write
```

Inspect recommendations without writing files:

```powershell
python -m stock_research memory writer-review --run-id 2026-05-09_weekly
```

Run the bounded OpenAI-backed writer:

```powershell
python -m stock_research memory writer-review --run-id 2026-05-09_weekly --execute --write --update-drafts
```

Apply approved ready drafts:

```powershell
python -m stock_research memory apply-updates --run-id 2026-05-09_weekly --proposal-id PROPOSAL_ID
```

## Guardrails

- The writer sees memory drafts and operational memory context, not secrets or brokerage/account data.
- The writer output must be structured JSON.
- Writer output is a recommendation only.
- CLI dry-runs do not write prompt/review artifacts unless `--write` or `--update-drafts` is passed.
- Accepted or revised drafts still need deterministic validation.
- Actual memory writes still go through `memory apply-updates`.
- Rejected or invalid writer recommendations must remain reviewable in `memory_writer_review.md`.

## Outputs

```text
agents/runs/{run_id}/memory_writer_prompt.json
agents/runs/{run_id}/memory_writer_prompt.md
agents/runs/{run_id}/memory_writer_review.json
agents/runs/{run_id}/memory_writer_review.md
```

When `--update-drafts` is passed, the writer also rewrites:

```text
agents/runs/{run_id}/memory_update_drafts.json
agents/runs/{run_id}/memory_update_drafts.md
```

Generated JSON artifacts are local runtime output and ignored by Git. Markdown writer artifacts are reviewable run artifacts.
