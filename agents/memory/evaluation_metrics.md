# Evaluation Metrics

Last updated: 2026-05-04

Run-quality memory for weekly/manual runs and future post-run reflection.

## Metrics To Capture Per Run

- run_id
- run_type: weekly | manual | smoke_test
- start_time and end_time
- deterministic tasks planned
- deterministic tasks completed
- provider tasks planned/completed/failed
- analysis tasks planned/completed/failed
- evidence packets created
- quality issues found
- missing citations
- provider conflicts preserved
- false-positive alerts
- stale data fixed
- file updates made
- human review items created
- user corrections received
- memory items added/updated/deprecated

## Current Baseline

- id: eval-2026-05-03-provider-smoke-tests
- date: 2026-05-03
- type: evaluation
- scope: provider
- status: active
- confidence: high
- trigger/source: Provider implementation smoke tests.
- lesson: SEC, yfinance, Exa, xAI/Grok, FMP, Polygon/Massive, Alpha Vantage, and financial comparison have live or deterministic smoke-test artifacts. Future evaluation should treat these as baseline provider-path checks, not as investment research conclusions.
- use_when: Verifying provider regressions and planning first full weekly run.
- do_not_use_when: Making investment decisions.
- evidence: `agents/runs/2026-05-09_weekly/evidence_packets/`
- owner: memory and evaluation orchestrator
- next_review: 2026-06-01

## Post-Run Reflection Checklist

After a weekly or manual run:

- Which provider calls failed or produced low-value output?
- Which evidence packets lacked enough source metadata?
- Which claims were contradicted by another provider?
- Which alerts were noisy or too vague?
- Which file updates needed human correction?
- Which prompt/tool pattern worked well enough to reuse?
- Which memory item should be added, updated, superseded, or deprecated?

## Recurring Failure Patterns

- No recurring full-run failure patterns recorded yet.
- Direct X.com API path was a corrected provider-routing mistake and is now tracked in `deprecated_memory.md` and `orchestrator_lessons.md`.
