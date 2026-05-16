# Codex-Supervised Workflow

Last updated: 2026-05-16

## Purpose

Codex-supervised mode is the default local scheduled workflow. It reduces OpenAI API cost by letting the Codex app act as the outer orchestrator while Python handles deterministic evidence gathering, analysis, memory reflection, file sync, and report generation.

Python still cannot call the current Codex chat model internally. The direction is the reverse:

```text
Codex app automation
  -> runs deterministic Python commands
  -> Python gathers Exa, Grok/xAI, SEC, yfinance, FMP, Polygon/Massive, Alpha Vantage evidence
  -> Python writes reports, memory/finalization artifacts, state updates, and a Codex review pack
  -> Codex reads the pack and linked artifacts
  -> Codex writes the final human-facing synthesis and updates docs/memory/scratchpads when useful
```

## Default Scheduled Command

The scheduled Codex app automation should run:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

This intentionally omits `--execute-orchestrator`.

Do not add `--execute-orchestrator` to the scheduled Codex-supervised automation unless the user explicitly asks for API-mode benchmarking or remote/headless simulation.

## Review Pack Contract

Every written weekly run now creates:

```text
agents/runs/{run_id}/codex_supervised_review_pack.md
agents/runs/{run_id}/codex_supervised_review_pack.json
```

The review pack is the handoff contract from deterministic Python to Codex. Codex must read it before writing the final review.

The pack points Codex to:

- `final_digest.md`
- all `reports/opportunity_assessment/*_opportunity_assessment.md`
- `quality_report.md`
- `run_summary.md`
- `finalization.md`
- memory reflection and memory draft artifacts
- `company_file_factual_updates.md`
- category state update artifacts
- `agents/human_review_digest.md`
- artifact hygiene/index files when present

Codex should then write:

```text
agents/runs/{run_id}/codex_supervised_review.md
```

## Required Codex Review Behavior

The Codex final review must be more useful than a status summary. It should include:

- bottom-line verdict for the run,
- per-ticker attention ranking,
- material X/Grok narrative shifts,
- source-backed news and developments,
- valuation/financial flags,
- non-obvious opportunities and risks,
- changes vs existing company files,
- open human-review decisions,
- memory/learning notes,
- report-quality assessment,
- next actions.

Codex should actively inspect output quality. If reports are truncated, duplicated, stale, shallow, missing X/community insight, or not actionable, Codex should fix the relevant prompt/formatter/code and regenerate the affected report before finishing.

For the 2026-05-16 real-holdings run, this quality check must include explicit scans for mojibake/encoding artifacts, dead citation markers, dead bracketed source ids, visible truncation, duplicate report sections, and dangling excerpt tails. Passing provider execution is not enough to call the run good.

## Memory And Learning

Codex-supervised mode must preserve the learning loop.

Still deterministic:

- run summary,
- quality report,
- memory reflection,
- memory update drafts,
- memory writer deterministic review,
- run finalization,
- recurring failure detection,
- category state updates,
- artifact hygiene/indexing,
- human-review digest.

Codex responsibilities:

- read memory/finalization artifacts,
- update scratchpads/backlog when the run reveals implementation work,
- update `agents/memory/` only for durable operational lessons, using the repo memory rules,
- avoid storing ordinary company facts in operational memory,
- keep rejected/archived/stale artifacts discoverable without cluttering active context.

## Company File And Human Review Rules

- Low-risk, source-backed factual company-file updates should be applied by the scoped deterministic writer and summarized as FYI.
- Thesis changes, opinion changes, strategy changes, status moves, buy/sell/position-size recommendations, and ambiguous edits must stay approval-gated.
- `agents/human_review_digest.md` is the user-facing decision inbox.
- Codex must not auto-approve review rows or move stocks between holdings, monitoring, and rejected without explicit user approval.

## API SDK Mode

The OpenAI Agents SDK workflow remains available:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900
```

Use API SDK mode for:

- remote/headless workers without Codex app automation,
- structured SDK traces and token metrics,
- benchmarking Codex-supervised output against API specialists,
- debugging specialist fanout,
- testing the formal Agents SDK architecture.

Do not use API SDK mode as the default local scheduled workflow because it adds OpenAI API synthesis cost where Codex app automation can provide higher-quality supervised synthesis through the subscription.

## Quality Benchmark

Codex-supervised mode should meet or exceed API SDK mode for human-facing quality. The benchmark is not speed; the benchmark is:

- actionable investor insight,
- strong X/Grok/community synthesis,
- clear source-backed facts,
- concise but useful final report,
- correct memory and hygiene behavior,
- no duplicate/truncated/stale sections,
- clear next decisions for the human.

2026-05-16 postmortem result: the first real Codex-supervised run exposed lazy SDK import gaps, stale API-mode artifact cleanup gaps, FMP/Alpha provider-unavailable handling gaps, and weak report-quality gates. The fixed baseline is a 10-holding run with 131 evidence packets, 0 provider errors, 0 deterministic quality findings, deduped HRQ counts, explicit provider coverage-gap packets, and human-facing markdown validation over the final digest, HRQ digest, Codex review, and opportunity reports.

2026-05-16 stabilization update: open rows in `agents/human_review_digest.md` are no longer treated as automation failure by the scheduled runner or review-pack status. They remain normal human decisions. Financial metadata normalization was also tightened so harmless company-name/share-class differences and exchange aliases do not create thesis-blocking financial review gates. FMP partial endpoint success is preserved for smaller names when profile data is available but quote/TTM endpoints are blocked by plan coverage.
