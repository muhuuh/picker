# Google Sheet Stock Intake Plan

Last updated: 2026-05-24

## Goal

Use the Google Sheet `new_stock_overview` as a fast stock idea inbox, then let Codex explicitly move selected rows into the repo candidate validation workflow.

## Scope

- In scope: Sheet columns/dropdowns, Codex-assisted row capture, selected-row repo import, candidate-review handoff, verification planning, documentation.
- Out of scope: automatic background watching of the Sheet, automatic broker/trade actions, automatic monitoring promotion without user approval.

## Action Plan

- [x] Confirm the Sheet is accessible through the Google Drive plugin.
- [x] Define clear Sheet action/status values that do not duplicate `validate`, `monitor`, and `needs more info`.
- [x] Update the live Sheet headers, notes, filters, freeze row, and dropdown validation.
- [x] Add deterministic `sheet-intake selected-rows` bridge for selected rows.
- [x] Reuse the existing candidate-review and candidate-verification workflow instead of creating a parallel stock pipeline.
- [x] Make candidate follow-up read both old detailed candidate-review tables and the newer compact table shape.
- [x] Add focused tests for Sheet row normalization, queue creation, CLI stdin import, and verification-plan creation.
- [x] Document the user journey, column meanings, and status update rules.
- [x] Verify live Google Sheet read/write/update behavior with ASTS and SIVE sample rows.
- [ ] Add a convenience helper for Codex sessions to read live Sheet rows into the CLI JSON shape only if repeated manual Sheet processing becomes annoying.
- [ ] Add an optional row-status update helper only if Codex connector write-back becomes repetitive after real processing batches.

## Current Decisions

- The user must proactively ask Codex to process `action=research` rows. No automation should start research just because a Sheet row changed.
- Blank `action` is the no-processing inbox state; `research` is the processing trigger; `add to monitoring`, `bought`, `ignore`, and `rejected` are post-research outcomes.
- `Processing status` stays a simple process-state dropdown: `not processed`, `in research`, `done`, or `needs fix`.
- The Sheet is not the source of truth for holdings, monitoring, or rejected state.
- `available` is a yes/no broker availability field; blank means unknown.
- `Score` is the user's personal quick-interest grade from A+ to D-.
- `P/S` is a quick price-to-sales valuation snapshot, especially useful when P/E is unavailable or the company is loss-making.
- `Forecast` is the average analyst forecast/upside snapshot.
- `Comment` should be a concise skim summary, not full research reasoning.

## Next Useful Step

Use Codex's Google Sheets connector for live reads/writes for now. Build a helper only after real batches show the connector path is too repetitive.

## 2026-05-17 Update

- Live Sheet validation passed with rows 2-3 populated from the user's ASTS/SIVE pasted report.
- Read/write/update checks verified:
  - write full rows with strict dropdown values,
  - read rows and validation metadata back from `Sheet1!A1:P3`,
  - update processing status and `Last checked`,
  - read the updated cells back successfully.
- CLI dry-run check selected one `research` row and skipped one blank-action row.
- After user feedback, simplified visible dropdowns: removed `save idea` and `research next`, preserved plus/minus scores such as `B+`, and reduced processing status to four values.

## 2026-05-24 Update

- Added a `P/S` column next to `Forward PE` in the live Sheet.
- Updated the intake schema/parser so `P/S`, `PS`, and price-to-sales header variants are preserved in candidate notes.
- Updated ticker normalization so cashtag-style inputs such as `$VPG` are accepted and processed as `VPG`.
- Removed the visible `Source / link` Sheet column; detailed evidence belongs in repo artifacts linked from `Repo link`.
