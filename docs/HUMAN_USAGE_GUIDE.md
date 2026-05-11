# Human Usage Guide

Last updated: 2026-05-11

## Short Version

Use Codex chat as the interface.

You do not need to manually edit files for normal use. Open this repo in Codex and ask in plain language:

```text
Research ASML, TSM, AMD, and SAP. Add them to monitoring if useful and summarize what you found.
```

or:

```text
Run market research on European semiconductor equipment suppliers. Include Exa/web and Grok/X sentiment, surface interesting companies, and tell me what needs review.
```

Codex should read the repo context, run the relevant workflow, write durable artifacts, and summarize where the results are.

## What To Ask Codex

### 1. Research Specific Stocks

Ask:

```text
Research ASML, TSM, AMD, and SAP. Add missing names to monitoring, run available company research, and summarize the results.
```

What Codex should do:

- add missing stocks to `stock_tracking/monitoring/monitoring.csv` when appropriate,
- create company files under `stock_tracking/stock_info_files/monitoring/`,
- run available company research if you asked for immediate research,
- summarize findings in chat,
- save deeper outputs under `agents/runs/{run_id}/`.

Where to read later:

- company-level notes: `stock_tracking/stock_info_files/`
- latest run reports: `agents/runs/{run_id}/`
- pending decisions: `agents/human_review_digest.md`

### 2. Research An Industry Or Theme

Ask:

```text
Run market research for grid-scale energy storage in Europe. Use Exa and Grok/X, find candidate stocks, and create review items for anything promising.
```

What Codex should do:

- run the manual market-research workflow,
- use Exa/web for verification-oriented research,
- use Grok/X for hype, sentiment, rumors, and niche leads,
- write a market report,
- create candidate review items when stocks need your decision.

Where to read later:

- market report: `agents/runs/{run_id}/market_research/`
- recurring topic files: `market_research/industries/` or `market_research/themes/`
- candidate decisions: `agents/human_review_digest.md`

### 3. Add A Recurring Research Priority

Ask:

```text
I think nuclear SMRs will matter next year. Add this as a recurring research priority and include it in future market research.
```

What Codex should do:

- update `strategy/research_priorities.md`,
- create or update a theme file under `market_research/themes/`,
- record the request in `docs/plans/human_research_requests.md`,
- tell you whether it needs a strategy-review approval.

### 4. Review What Needs Your Decision

Ask:

```text
Show me my open human review digest and explain what I need to decide.
```

Codex should read:

```text
agents/human_review_digest.md
```

Then it should summarize only the open decisions.

You can answer:

```text
Approve HRQ-0007 for verification, reject HRQ-0008, and leave HRQ-0009 open.
```

Codex should record that decision. Recording a decision does not automatically trade, promote a stock, or edit company files. Follow-up actions stay approval-gated.

Allowed decisions:

- `approve`
- `reject`
- `needs_more_research`
- `leave_open`
- `supersede`

### 5. Get A Portfolio Or Watchlist Update

Ask:

```text
Give me a portfolio review from the latest run. Focus on holdings, monitored stocks, open review items, and what needs attention this week.
```

Codex should use:

- `stock_tracking/current_holdings/`
- `stock_tracking/monitoring/`
- `stock_tracking/rejected/`
- latest `agents/runs/{run_id}/portfolio_review/portfolio_review.md`
- `agents/human_review_digest.md`

The portfolio review report is not your main inbox. It is deeper context. Your main inbox is still `agents/human_review_digest.md`.

### 6. Run The Weekly-Style Workflow Manually

Ask:

```text
Run the weekly research workflow manually for the current repo state. Use fresh providers if possible, then summarize results and open review items.
```

What Codex should do:

- run the weekly workflow from the repo,
- write reports under `agents/runs/{run_id}/`,
- refresh the review digest,
- summarize what changed and what you need to decide.

## Where Results Live

Use this simple map:

| Need | Main place |
| --- | --- |
| What needs my decision? | `agents/human_review_digest.md` |
| Durable review queue | `agents/human_review_queue.md` |
| Latest run outputs | `agents/runs/{run_id}/` |
| Specific company knowledge | `stock_tracking/stock_info_files/` |
| Current holdings overview | `stock_tracking/current_holdings/current_holdings.csv` |
| Monitoring overview | `stock_tracking/monitoring/monitoring.csv` |
| Rejected/cooldown overview | `stock_tracking/rejected/rejected.csv` |
| Industry/theme research | `market_research/industries/`, `market_research/themes/` |
| Strategy and priorities | `strategy/` |
| Your proactive requests | `docs/plans/human_research_requests.md` |

## Normal Human Workflow

1. Open this repo in Codex.
2. Ask a natural-language request.
3. Codex runs or queues the right workflow.
4. Codex summarizes the result in chat.
5. For deeper detail, ask Codex to summarize the relevant run report or company file.
6. For decisions, ask Codex to show `agents/human_review_digest.md`.
7. Tell Codex which HRQ items to approve, reject, mark for more research, or leave open.

## Good Prompts

```text
Research these stocks now: ASML, TSM, AMD, SAP. Create or update monitoring files and tell me what needs human review.
```

```text
Run market research on European defense electronics. Include Exa and Grok/X, surface candidate stocks, and create candidate review items.
```

```text
Show me open human review items. Group them by decision type and recommend what I should look at first.
```

```text
Approve HRQ-0007 for verification and mark HRQ-0008 as needs_more_research because I want more filing evidence.
```

```text
Give me the latest summary for AAPL from our company file and latest run artifacts.
```

```text
Add humanoid robotics as a recurring research theme and explain which files you updated.
```

## Practical Rules

- Tell Codex whether you want immediate research or just to add something for future tracking.
- Do not manually inspect every report unless you want detail. Start with the chat summary and `agents/human_review_digest.md`.
- Use HRQ IDs when making decisions.
- Do not approve vague batches if you are unsure. Ask Codex to explain the evidence for specific HRQ items.
- Research output is not a trade instruction. Buy, sell, and position-size decisions stay human-approved.

## If You Start A New Codex Chat

Start with:

```text
Read AGENTS.md and docs/HUMAN_USAGE_GUIDE.md first. Then show me the current status and open human review digest.
```

For a new task, you can simply ask the task directly. `AGENTS.md` tells Codex to load repo memory, the repo map, relevant scratchpads, and planning files before acting.
