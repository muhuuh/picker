# Codex-Supervised Workflow

Last updated: 2026-05-18

## Purpose

Codex-supervised mode is the default local scheduled workflow. It reduces OpenAI API cost by letting the Codex app act as the outer orchestrator while Python handles deterministic evidence gathering, analysis, memory reflection, file sync, and report generation.

Python still cannot call the current Codex chat model internally. The direction is the reverse:

```text
Codex app automation
  -> runs deterministic Python commands
  -> Python gathers Exa, Grok/xAI, SEC, yfinance, FMP, Polygon/Massive, Alpha Vantage evidence
  -> Python writes evidence/audit reports, human synthesis packs, memory/finalization artifacts, state updates, and a Codex review pack
  -> Codex reads the pack, synthesis packs, and linked artifacts
  -> Codex writes the final human-facing synthesis from first principles and updates docs/memory/scratchpads when useful
```

## Default Scheduled Command

The scheduled Codex app automation should run:

```powershell
C:\Python313\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis
```

This intentionally omits `--execute-orchestrator`.

Do not add `--execute-orchestrator` to the scheduled Codex-supervised automation unless the user explicitly asks for remote/headless fallback or SDK debugging.

## Review Pack Contract

Every written weekly run now creates:

```text
agents/runs/{run_id}/codex_supervised_review_pack.md
agents/runs/{run_id}/codex_supervised_review_pack.json
```

The review pack is the handoff contract from deterministic Python to Codex. Codex must read it before writing the final review.

The pack points Codex to:

- `final_digest.md`
- all `reports/human_synthesis/*_synthesis_pack.md`
- all `reports/opportunity_assessment/*_opportunity_assessment.md` as deterministic audit/evidence reports, not final prose
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
agents/runs/{run_id}/reports/human_synthesis/{TICKER}_final_human_report.md for every human synthesis pack
```

Then Codex must rerun the post-Codex quality gate:

```powershell
python -m stock_research quality-report --run-id {run_id} --write --require-final-reports
```

This command is the deterministic proof that the final report layer is present in the canonical workflow paths. A run should not be treated as complete if this gate reports missing final reports, orphan final reports, shallow final reports, malformed final reports, repeated claims, or other human-facing quality findings.

Reader-facing artifact contract:

- `codex_supervised_review.md` is the crafted run-level final digest/review written by Codex app.
- `reports/human_synthesis/*_final_human_report.md` are the crafted per-ticker company/opportunity reports written by Codex app.
- `final_digest.md` is a deterministic quick-read source map that must remain readable and quality-gated, but it is not the only final narrative.
- `reports/opportunity_assessment/*_opportunity_assessment.md` are deterministic audit/evidence reports.
- `reports/financial_data_specialist/` and `reports/company_news_specialist/` are specialist input reports; Codex should read them, not paste them.

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

Per-ticker opportunity assessments are not the final reading experience. They are audit artifacts that preserve score factors, evidence lanes, and source coverage. The final human-facing report must be written from a human synthesis pack by the Codex app so the output has a coherent storyline, explains why each fact matters, separates verified facts from Grok/X social narrative and auxiliary Grok web context, and avoids over-compressed bullets that are technically accurate but not useful.

## Established Per-Ticker Final Report Shape

The accepted baseline is the 2026-05-16 AMBA final human report. Manual one-off research and scheduled automation must use the same final-report contract; Codex should not create a new report name or ad hoc structure when the user asks for automation-style research.

Each `reports/human_synthesis/{TICKER}_final_human_report.md` must start with a provenance paragraph stating that it is a Codex-written synthesis from the synthesis pack, deterministic audit report, company-news and financial specialist outputs, raw Grok/X sentiment, Grok web deep dive, and the current company file. It must also state that the deterministic opportunity assessment remains the audit artifact.

Required sections:

- Bottom Line
- What [Company] Actually Does
- Why The Setup Changed
- X Sentiment And What It Is Really Saying
- Financial And Valuation Read
- Bull Case
- Bear Case
- What Would Change The Thesis
- Next Research Checks
- Final Assessment
- Sources

The final report is a cleaner story, not a smaller story. It must preserve at least the same investor-useful insight coverage as the opportunity assessment while removing repetition and pasted-subreport feel. The required coverage includes source-backed developments, market/industry context, X pulse and trend evolution, recurring bull and bear social claims, notable accounts/posts or source-quality context, rumors/unverified claims, non-obvious or under-discussed angles, valuation/analyst gaps, a decision table or investor scorecard, thesis changers, and concrete next checks.

The report-quality gate treats missing provenance/required sections, incomplete evidence, repeated or paraphrased boilerplate, and failed reader-value dimensions as workflow defects. It does not use a universal word-count floor or keyword checklist: stable names may be concise, while material changes must remain specific, source-backed, decision-relevant, and complete. A weak or differently shaped final report should be fixed in the workflow instructions/templates and regenerated, not padded or patched into a separate report artifact.

Post-Codex report validation must use `quality-report --require-final-reports`. The default pre-Codex quality report can run before Codex has written the final reports, but the post-Codex gate must require every synthesis pack to have exactly the expected canonical final report target. Extra `*_final_human_report.md` files without matching `*_synthesis_pack.md` are orphan artifacts and should be removed or moved into the correct run workflow rather than left as alternate reports.

For the 2026-05-16 real-holdings run, this quality check must include explicit scans for mojibake/encoding artifacts, dead citation markers, dead bracketed source ids, visible truncation, duplicate report sections, and dangling excerpt tails. Passing provider execution is not enough to call the run good.

Custom/manual manifests can name xAI/Grok raw artifacts differently from the default manifest. The synthesis-pack builder must include both default `x_search` / `web_search` names and custom names such as `xai_x` / `xai_web`; otherwise a run can falsely appear to lack same-run Grok/X or Grok web evidence even when provider execution succeeded.

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

Use API SDK mode only for:

- remote/headless workers without Codex app automation,
- structured SDK traces and token metrics,
- debugging specialist fanout,
- testing the formal Agents SDK architecture.

Do not use API SDK mode as the default local scheduled workflow because it adds OpenAI API synthesis cost where Codex app automation can provide higher-quality supervised synthesis through the subscription.

## Quality Standard

Codex-supervised mode is the primary quality path for local scheduled and manual runs. The API path is a fallback/debug route, not the target writer. The quality standard is:

- actionable investor insight,
- strong X/Grok/community synthesis,
- clear source-backed facts,
- concise but useful final report,
- correct memory and hygiene behavior,
- no duplicate/truncated/stale sections,
- clear next decisions for the human.

2026-05-16 postmortem result: the first real Codex-supervised run exposed lazy SDK import gaps, stale API-mode artifact cleanup gaps, FMP/Alpha provider-unavailable handling gaps, and weak report-quality gates. The fixed baseline is a 10-holding run with 131 evidence packets, 0 provider errors, 0 deterministic quality findings, deduped HRQ counts, explicit provider coverage-gap packets, and human-facing markdown validation over the final digest, HRQ digest, Codex review, and opportunity reports.

2026-05-16 stabilization update: open rows in `agents/human_review_digest.md` are no longer treated as automation failure by the scheduled runner or review-pack status. They remain normal human decisions. Financial metadata normalization was also tightened so harmless company-name/share-class differences and exchange aliases do not create thesis-blocking financial review gates. FMP partial endpoint success is preserved for smaller names when profile data is available but quote/TTM endpoints are blocked by plan coverage.
