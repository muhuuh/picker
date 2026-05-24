# Scheduled Runner

Last updated: 2026-05-18

## Purpose

The scheduled runner is the tracked-stock workflow wrapper. The command is still named `run-weekly` because it builds weekly-style run artifacts, but the first Codex app automation runs it every two weeks. It chains the already-built repo loaders, manifest generation, provider task runner, analysis task runner, run summary, quality report, memory finalization, bounded memory-writer review, company-file factual sync, category state updates, final digest, human synthesis packs, human-review digest, and Codex-supervised review pack.

Implementation: `stock_research/scheduled_runner.py`.

The default local scheduled mode is Codex-supervised: Python gathers and validates evidence, then the Codex app reads the generated review pack and writes the final human-facing synthesis using the user's Codex GPT-5.5 high environment. The runner can still optionally call OpenAI Agents SDK company-research fanout and the main orchestrator when `--execute-orchestrator` is explicitly requested for API benchmarking, debugging, or remote/headless mode.

The CLI command is only the scheduler/manual entrypoint. Internal workflow steps should call importable Python functions directly rather than shelling out to other CLI commands.

## Codex App Automation

The first Codex app automation is configured as a biweekly tracked-stock run, not a remote worker. It runs every two weeks on Saturday at 08:00, starting 2026-05-16, from:

```text
C:\Users\valen\Documents\Code\stocks
```

Automation file:

```text
C:\Users\valen\.codex\automations\biweekly-holdings-and-monitoring-research\automation.toml
```

The automation must use the explicit Python executable and this exact lower-cost Codex-supervised command:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

This intentionally omits `--execute-orchestrator`. Do not add API SDK orchestration unless the user explicitly asks for remote/headless fallback or SDK debugging. Do not change it to bare `python`. Do not add `git fetch`, `git pull`, `git checkout`, `git reset`, or other Git metadata writes to the automation.

The automation prompt also requires Codex to write every canonical per-ticker final report target from the human synthesis packs, avoid side reports, and rerun the post-Codex quality gate with `--require-final-reports` before finishing.

The Codex exec-policy rules also allow the direct post-Codex quality-report command. Validate both scheduled commands with `codex execpolicy check` after changing the automation prompt or rules.

Codex automation sandbox rules are stored at:

```text
C:\Users\valen\.codex\rules\default.rules
```

The rules intentionally allow only the exact Codex-supervised stock workflow command above and the equivalent Windows PowerShell wrapper. The older API SDK command remains allowlisted only as an explicit benchmark/remote-mode escape hatch. Validate the scheduled command with:

```powershell
codex execpolicy check --pretty --rules C:\Users\valen\.codex\rules\default.rules -- C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

The expected decision is `allow`. Broad Git commands and arbitrary `stock_research` provider execution should remain unallowlisted.

## Command

Dry-run the weekly workflow without writing artifacts or calling live APIs:

```powershell
python -m stock_research run-weekly
```

Persist manifest, summaries, quality report, memory finalization, memory-writer review, final digest, human-review digest, Codex review pack, and orchestration report:

```powershell
python -m stock_research run-weekly --write
```

Execute live provider and analysis tasks:

```powershell
python -m stock_research run-weekly --write --execute-providers --execute-analysis
```

This is the default Codex-supervised automation path. After it finishes, Codex should read:

```text
agents/runs/{run_id}/codex_supervised_review_pack.md
```

and then write:

```text
agents/runs/{run_id}/codex_supervised_review.md
agents/runs/{run_id}/reports/human_synthesis/{TICKER}_final_human_report.md for every synthesis pack
```

After writing those Codex-authored reports, Codex must run:

```powershell
python -m stock_research quality-report --run-id {run_id} --write --require-final-reports
```

This post-Codex gate prevents the scheduled or manual workflow from silently accepting missing, orphaned, shallow, or malformed final reports.

When live provider or analysis execution is enabled, the runner first cleans generated artifacts in the target run directory (`evidence_packets/`, `raw/`, `reports/`, and generated root report files). This keeps repeated manual smoke tests or reruns from double-counting stale evidence packets.

Optionally call the live OpenAI-backed memory writer:

```powershell
python -m stock_research run-weekly --write --execute-memory-writer
```

Optionally call the OpenAI Agents SDK orchestrator:

```powershell
python -m stock_research run-weekly --write --execute-orchestrator
python -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 300
```

`--execute-orchestrator` requires `OPENAI_API_KEY` and `--write`. SDK timeout/error results are written as blocked reviewable artifacts plus `run_metrics.md`, then memory reflection can turn them into learning-loop issues.

When SDK orchestration is enabled, the runner first runs generic company-research fanout for every ticker in `stock_tracking/current_holdings/current_holdings.csv` and `stock_tracking/monitoring/monitoring.csv`. This produces per-ticker research artifacts before the main orchestrator synthesis.

## Workflow

```text
load repo state
  -> build weekly manifest
  -> provider tasks (dry-run unless --execute-providers)
  -> analysis tasks (dry-run unless --execute-analysis)
  -> run_summary
  -> quality_report
  -> memory finalize-run
  -> memory writer-review
  -> SDK company-research fanout for current/monitoring tickers (only with --execute-orchestrator)
  -> SDK portfolio/memory/main orchestrators (only with --execute-orchestrator)
  -> SDK proposal review bridge (only after successful SDK orchestrator output)
  -> final_digest
  -> human_synthesis_packs
  -> human_review_digest
  -> codex_supervised_review_pack
  -> Codex app reads pack and writes codex_supervised_review.md
  -> Codex app writes canonical reports/human_synthesis/*_final_human_report.md targets
  -> post-Codex quality_report --require-final-reports
  -> orchestration_report
```

## Outputs

When `--write` is used:

- `agents/runs/{run_id}/manifest.json`
- `agents/runs/{run_id}/run_summary.md`
- `agents/runs/{run_id}/quality_report.md`
- `agents/runs/{run_id}/memory_reflection.md`
- `agents/runs/{run_id}/memory_update_drafts.md`
- `agents/runs/{run_id}/memory_writer_prompt.md`
- `agents/runs/{run_id}/memory_writer_review.md`
- `agents/runs/{run_id}/finalization.md`
- `agents/runs/{run_id}/final_digest.md`
- `agents/runs/{run_id}/reports/human_synthesis/{TICKER}_synthesis_pack.md`
- `agents/human_review_digest.md`
- `agents/runs/{run_id}/codex_supervised_review_pack.md`
- `agents/runs/{run_id}/codex_supervised_review_pack.json`
- `agents/runs/{run_id}/codex_supervised_review.md` when Codex app automation completes the supervised review step
- `agents/runs/{run_id}/company_research/{TICKER}_company_research.md` when `--execute-orchestrator` is used and tracked tickers exist
- `agents/runs/{run_id}/company_research/{TICKER}_company_research_metrics.md` when company-research fanout writes metrics
- `agents/runs/{run_id}/agent_runtime_main_orchestrator.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestrator_update_proposals.md` when successful SDK output contains file update proposals
- `agents/runs/{run_id}/trace_links.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/run_metrics.md` when `--execute-orchestrator` is used
- `agents/runs/{run_id}/orchestration_report.md`

Generated JSON files remain ignored local runtime artifacts. They should not be committed. After the run is finalized, memory drafts are handled, open review references are resolved, and canonical final human reports exist, local JSON can be cleaned with:

```powershell
python -m stock_research artifact-hygiene cleanup-json
python -m stock_research artifact-hygiene cleanup-json --write
```

The cleanup command is dry-run by default and only deletes generated JSON under `agents/runs/`.

The final digest includes readable financial formatting, forward P/E and analyst target context when available, explicit per-ticker evidence links, concrete news developments, Grok/X pulse, recurring bull/bear narratives, accounts/posts to review, hype/noise, and deterministic digest quality findings when required evidence links, financial/news statuses, social-signal labels, status-only social output, missing social narratives, or trade-instruction guardrails fail.

The deeper per-company opportunity report includes the richer investor insight section: executive read, company/industry context, thesis/trend change, Grok/X expert-community split, non-obvious insights, valuation/analyst target snapshot, peer context, decision table, and next research questions. Treat it as deterministic audit/evidence. The reader-facing per-ticker report should be written from `reports/human_synthesis/{TICKER}_synthesis_pack.md` by Codex app GPT-5.5 high. The human-review digest is refreshed so the report can point the user to current approve/reject/needs-more-research/leave-open decisions.

Manual market-research reports use the same investor-usefulness standard. They should show industry/theme context, X/community pulse, trend evolution, candidate pipeline, non-obvious/contrarian angles, a decision table, and explicit approve/reject/request-more-research choices instead of generic lane/status labels.

## Status Semantics

- `dry_run`: no files were written.
- `complete`: written run completed without deterministic quality findings, provider errors, analysis errors/skips, memory finalization issues, SDK quality/freshness findings, or digest quality findings. Open human-review digest rows do not by themselves make the run fail; they are normal asynchronous decisions.
- `needs_review`: provider errors, analysis errors/skips, quality findings, finalization issues, SDK errors, company-research fanout errors/partial results, SDK quality findings, digest quality findings, or actionable SDK output from dry-run provider/analysis inputs exist.

Financial-review metadata normalization should not make the whole scheduled run fail. Name/share-class differences such as `Alphabet Inc.` vs `Alphabet Inc. Class A Common Stock`, and exchange aliases such as `XNAS`/`NCM` or `XNYS`/`NYQ`, are metadata/watch items unless they expose a real thesis-relevant financial conflict. True missing coverage, material numeric disagreement, and low-confidence core financial metrics still need review.

If the SDK orchestrator is enabled while provider or analysis tasks are dry-run, it receives that execution-mode context in its prompt. If it still produces ready/actionable alerts or file update proposals, the runner appends a freshness finding and marks the scheduled run `needs_review`.

## Current Boundary

The default local orchestration boundary is now:

- Codex-supervised scheduled mode: `C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis`, then Codex reads `codex_supervised_review_pack.md` and writes `codex_supervised_review.md`.
- API SDK mode remains available for remote/headless execution, structured SDK traces, and benchmarking through `--execute-orchestrator`.

The agent framework decision is resolved:

- Selected framework: OpenAI Agents SDK.
- Dedicated plan: `docs/plans/openai_agents_sdk_orchestration_backlog.md`.
- Dedicated scratchpad: `docs/scratchpads/openai_agents_sdk_orchestration_scratchpad.md`.

Current SDK integration:

- Manual SDK run: `python -m stock_research agent-runtime run --run-id RUN_ID --execute --write`.
- Scheduled opt-in SDK run: `python -m stock_research run-weekly --write --execute-orchestrator`.
- Fresh actionable local Codex-supervised research should normally use `--execute-providers --execute-analysis` and then Codex should write the supervised review. Fresh API SDK benchmark/remote research should use `--execute-providers --execute-analysis --execute-orchestrator`; otherwise SDK proposals are review-only.
- Scheduled SDK orchestration now includes per-ticker company-research fanout before the main orchestrator. Fanout task names include tickers as labels only; specialists are generic and reusable.
- Repeated fresh runs are idempotent at the generated-artifact level because live execution cleans prior generated run artifacts before rebuilding them.
- Successful SDK file update proposals are routed through `orchestrator_update_proposals.md` and duplicate-safe human-review queue rows before any company-file writer can apply them.
- Approved proposals can be applied after human review with `python -m stock_research agent-runtime apply-proposal --run-id RUN_ID --proposal-id ORP-0001 --write`; this is intentionally outside the automatic weekly flow for now.
