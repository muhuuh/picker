# Codex-Supervised Review: 2026-05-16 Weekly

Status: `needs_review`

## Bottom Line

The deterministic provider and analysis workflow is now usable for the 10 current holdings. The run produced 131 evidence packets, 10 opportunity assessments, 10 company-news reviews, 10 financial reviews, a final digest, company-file factual updates, memory/finalization artifacts, and a refreshed human-review digest.

The run still needs review because several financial reviews have material conflicts or low-confidence metrics. That is a review gate, not a provider execution failure.

## Attention Ranking

| Rank | Ticker | Read | Risk | Why it matters now |
| --- | --- | --- | --- | --- |
| 1 | NBIS | interesting, 72/100 | medium | X/Grok and source-backed evidence point to sold-out AI-cloud capacity, hyperscaler/customer leverage, and strong post-earnings momentum; verify loss quality and revaluation gains before increasing confidence. |
| 2 | AMBA | constructive_but_watch, 68/100 | medium | X narrative is unusually specific around low-power edge inference for humanoids/ADAS; valuation is demanding, so June earnings/design-win evidence matters. |
| 3 | KRKNF | constructive_but_watch, 62/100 | medium | Subsea defense/autonomy narrative is active on X with specific catalysts; coverage is thinner, so verify backlog, Covelya close, and Anduril-related claims. |
| 4 | GOOGL | constructive_but_watch, 59/100 | high | AI integration and Anthropic/Google ecosystem evidence are relevant, but financial review still needs human review before thesis changes. |
| 5 | MU | constructive_but_watch, 59/100 | high | X narrative has shifted toward structurally constrained AI memory/HBM; financial review conflicts keep this gated. |
| 6 | TE | neutral, 55/100 | high | U.S. solar manufacturing narrative is live, but the setup is still high-risk and needs financial verification. |
| 7 | AVAV | neutral, 48/100 | high | Defense/drone catalysts are source-backed, but financial conflicts and execution risk dominate. |
| 8 | OSS | neutral, 48/100 | high | Edge AI/defense-compute chatter is interesting after a Q1 beat, but coverage and financial confidence remain weak. |
| 9 | AXTI | weak_or_risky, 44/100 | high | Photonics/InP bottleneck narrative is strong on X, but valuation/execution/export-control risk is high. |
| 10 | IREN | weak_or_risky, 44/100 | high | BTC-to-AI infrastructure pivot is actively discussed, but financial quality and execution risk remain too high for a clean positive read. |

## Material Narrative Shifts

- Grok/X is now surfacing the useful layer again: NBIS AI-cloud capacity scarcity, AMBA edge-inference robotics positioning, MU HBM/AI-memory scarcity, AXTI InP photonics bottleneck, and KRKNF subsea defense/autonomy catalysts.
- The strongest current social signals are NBIS and AMBA. KRKNF is interesting but needs more verification because it is smaller and less covered.
- High-risk names should not be promoted by narrative alone. AXTI, IREN, OSS, AVAV, TE, MU, and GOOGL all need financial-review gates resolved before any thesis/status change.

## File And State Updates

- Low-risk factual company-file updates were applied/refreshed for all 10 current holdings.
- Category state files were already updated for `current_holdings`, `monitoring`, and `rejected`.
- `agents/human_review_digest.md` currently summarizes 20 open deduped review items, mostly older candidate-verification rows plus legacy AAPL FYI rows.

## Quality Review

- Provider errors: 0.
- Deterministic quality findings: 0.
- Human-facing markdown validation passed for the final digest, human-review digest, and all 10 opportunity assessments.
- Important fix from this run: FMP subscription/tier failures and Alpha Vantage rate limits now become explicit coverage-gap packets instead of missing-provider errors.

## Human Review

Read first:

- `agents/runs/2026-05-16_weekly/final_digest.md`
- `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/NBIS_opportunity_assessment.md`
- `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/AMBA_opportunity_assessment.md`
- `agents/runs/2026-05-16_weekly/reports/opportunity_assessment/KRKNF_opportunity_assessment.md`
- `agents/human_review_digest.md`

Allowed decisions remain: approve, reject, needs_more_research, or leave open by HRQ id. Do not treat this report as a trade instruction.

## Remaining Risks

- Financial-provider coverage is not equal across all holdings. Small/OTC and less-covered names have weaker analyst/forward-valuation data.
- Some source titles still contain publisher-side ellipses in the source bibliography; these are source labels, not report truncation.
- The workflow still needs a safer incremental report-regeneration command so report formatting fixes can be rerun without touching provider artifacts.
