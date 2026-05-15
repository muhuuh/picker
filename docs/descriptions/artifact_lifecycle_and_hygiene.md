# Artifact Lifecycle And Hygiene

Last updated: 2026-05-15

## Goal

Keep the repo useful as research volume grows.

The system will eventually research many stocks, industries, and themes. Not every run artifact should stay in the active working surface forever. The goal is to keep active holdings, monitoring names, current priorities, and open decisions easy to find while preserving old research in an archive that Codex can still locate when needed.

## Core Principle

Do not delete useful research by default. Move it out of the active surface and index it.

Active truth should live in:

- `stock_tracking/current_holdings/`
- `stock_tracking/monitoring/`
- `stock_tracking/rejected/`
- `stock_tracking/stock_info_files/`
- `market_research/industries/`
- `market_research/themes/`
- `strategy/`
- `agents/human_review_digest.md`

Run artifacts under `agents/runs/` are evidence and audit history. They are useful, but they should not become the primary place to find current investment state.

## Proposed Archive Structure

```text
archive/
  research_index.md
  company_research/
    active/
    archived/
  market_research/
    active/
    archived/
  runs/
    YYYY/
```

This structure can be added later. For now, the important part is to plan for it and avoid treating `agents/runs/` as the long-term knowledge index.

## Research Index

Create a durable index when archive automation starts:

```text
archive/research_index.md
```

Each row should track:

- ticker or topic
- company/topic name
- status: active_holding, monitoring, rejected_cooldown, rejected_archive, archived, superseded
- latest active file
- archived evidence path
- last reviewed date
- next eligible review date
- reason archived or rejected
- confidence / usefulness note

This lets Codex answer: "Have we researched this before, and where is the material?"

## Company Lifecycle

```mermaid
flowchart TD
    A["Discovered lead"] --> B["Candidate review"]
    B --> C["Verification result"]
    C --> D{"Decision"}
    D --> E["Monitoring"]
    D --> F["Rejected cooldown"]
    D --> G["Archived research only"]
    E --> H["Current holding"]
    E --> F
    H --> E
    H --> F
    F --> I["Eligible after cooldown"]
    I --> B
```

Rules:

- Holdings and monitoring names stay in active stock tracking and should have detailed company files.
- Rejected names keep enough information to explain why they were rejected and when they can resurface.
- Old run reports for non-active names can move to archive after the key conclusion is captured in the rejected row/index.
- If a rejected stock resurfaces after cooldown, Codex should read the archived/indexed prior research before starting from scratch.

## Run Artifact Hygiene

Keep:

- final digests,
- opportunity assessments for active holdings/monitoring names,
- market reports tied to active priorities,
- candidate verification results,
- memory/reflection summaries,
- quality reports needed for debugging.

Archive or compress from the active view:

- old raw run reports for candidates rejected or ignored,
- duplicate regenerated reports,
- stale candidate-review artifacts superseded by newer review groups,
- temporary debug artifacts after their lessons are captured in memory/backlog.

Ignored local JSON/raw/evidence artifacts should remain local runtime outputs unless they are explicitly needed for a reproducible test fixture.

## Automation Backlog

1. Add `archive/research_index.md`.
2. Add an artifact inventory command that lists active vs stale run artifacts.
3. Add an archive command that moves old run markdown into `archive/` and updates the index.
4. Add guardrails so archiving never removes active holding/monitoring company files.
5. Add run-finalization logic that proposes archive candidates after reports are promoted into durable company/market/strategy files.

## Guardrails

- Never archive current holding or monitoring company files.
- Never delete evidence by default; move and index.
- Never archive an item with an open HRQ decision unless the HRQ row is superseded or resolved.
- Preserve rejected cooldown dates and reasons.
- Keep archive indexes concise so future Codex chats do not need to scan hundreds of old reports.
