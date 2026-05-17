# Google Sheet Stock Intake

Last updated: 2026-05-17

## Purpose

The Google Sheet `new_stock_overview` is a quick capture inbox for stocks the user comes across. It is for fast triage and memory, not for durable portfolio state.

Source sheet:

```text
https://docs.google.com/spreadsheets/d/16S9NXkIi4IH6fPHe3DMpxvtjknzzRIjyxW2XjJp6Jr0/edit
```

Durable state still lives in the repo:

- current holdings: `stock_tracking/current_holdings/`
- monitored stocks: `stock_tracking/monitoring/`
- rejected stocks: `stock_tracking/rejected/`
- candidate verification artifacts: `agents/runs/{run_id}/market_research/`
- human decisions: `agents/human_review_digest.md` and `agents/human_review_queue.md`

## User Journey

1. User hears about a stock.
2. User asks Codex chat to fill one row in the Sheet from a pasted paragraph, source link, or quick note.
3. Codex fills the row with basic company data, analyst forecast if available, the user's `Score`, broker `available` value, a concise `Comment`, and the source link.
4. User reviews the Sheet every one or two weeks.
5. User changes `action` to `research` only for rows that should enter the repo validation path.
6. User explicitly asks Codex to process those `research` rows.
7. Codex turns selected rows into repo candidate-review artifacts and, only when explicitly requested, verification tasks.
8. After research, the Sheet row should be updated to show the final routing in `action`, plus simple `Processing status`, `Repo link`, and `Last checked` fields.

No background automation should watch the Sheet and start research without an explicit user request.

## Sheet Columns

| Column | Meaning |
| --- | --- |
| `Date` | Date the stock idea was captured. |
| `Name` | Company name. |
| `Ticker` | Exchange ticker or best-known symbol. |
| `Industry` | Short industry/theme label. |
| `Mcap` | Market capitalization snapshot for triage. |
| `Forward PE` | Forward P/E snapshot for triage. |
| `Forecast` | Average analyst forecast/upside noted at capture time. |
| `Score` | User's personal interest grade: `A+` strongest, `D-` weakest. |
| `available` | Broker/provider availability: `yes` or `no`; blank means unknown. |
| `action` | User routing decision for the row. |
| `Comment` | Few-sentence skim summary of what the stock is and why it is interesting. |
| `Source / link` | Optional article, post, note, or URL behind the idea. |
| `Processing status` | Simple Codex/repo processing status for this row. |
| `Repo link` | Repo artifact created from this row, if any. |
| `Last checked` | Last date Codex or the user reviewed this row. |

## Dropdown Semantics

`Score` options:

- `A+`
- `A`
- `A-`
- `B+`
- `B`
- `B-`
- `C+`
- `C`
- `C-`
- `D+`
- `D`
- `D-`

`available` options:

- `yes`
- `no`

`action` options:

- blank: keep the idea in the Sheet inbox. Codex should not process it when scanning selected rows.
- `research`: process this row through repo candidate review/verification planning when the user explicitly asks Codex.
- `add to monitoring`: final user decision to track the stock in repo monitoring after research/approval.
- `buy candidate`: high-interest idea, but not a trade instruction.
- `bought`: user already bought it or confirms it belongs in current holdings.
- `ignore`: do not pursue this row.
- `rejected`: researched and rejected; treat future resurfacing through the normal rejected cooldown logic.

`Processing status` options:

- `not processed`: no repo processing has been run for the row.
- `in research`: Codex has started processing or verification work.
- `done`: the row has been handled; check `action` and `Repo link` for the outcome.
- `needs fix`: Codex could not process the row until the row data is corrected.

## Repo Bridge

The import bridge is:

```powershell
python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review
```

Default behavior imports only rows whose `action` normalizes to `research`.

The command writes:

- `agents/runs/{run_id}/market_research/sheet_intake.md`
- `agents/runs/{run_id}/market_research/sheet_intake_candidate_leads.json`
- `agents/runs/{run_id}/market_research/candidate_review.md`
- optional human-review queue rows when `--queue-review` is used

It does not add stocks to monitoring, current holdings, or rejected state.

When the user explicitly wants to skip the separate HRQ approval step for the just-created rows and immediately plan verification, use:

```powershell
python -m stock_research sheet-intake selected-rows --rows-json rows.json --write --queue-review --approve-verification --write-verification-plan
```

That writes `candidate_verification_manifest.json` and `candidate_verification_plan.md`, but still does not promote the stock to monitoring or holdings.

## Status Updates After Research

After a selected row is researched:

- If it becomes a monitoring candidate and the user approves promotion, update `action=add to monitoring`, `Processing status=done`, and `Repo link` to the monitoring/company artifact.
- If the user bought it, update `action=bought`, `Processing status=done`, and ensure the current-holdings repo files are updated.
- If it should not be pursued, update `action=ignore` or `action=rejected`, and set `Processing status=done`; use `rejected` when the repo should preserve a cooldown trail.
- If research is underway but not finished, keep `action=research` and set `Processing status=in research`.
- If a row cannot be processed because it lacks ticker/name or already exists in holdings/monitoring, set `Processing status=needs fix` and fix the row or final routing.

## Guardrails

- The Sheet is a capture inbox, not the source of truth.
- Do not treat `buy candidate` as an automatic buy decision.
- Do not promote a row to monitoring without repo verification and an explicit user decision.
- Do not treat `available=no` as blocking research, but it should block buy/promotion decisions until availability changes.
- Keep detailed evidence and conclusions in repo artifacts; keep the Sheet concise and skimmable.
