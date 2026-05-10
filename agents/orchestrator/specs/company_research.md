# Company Research Orchestrator Spec

- agent_id: `company_research_orchestrator`
- role: sub-orchestrator
- subject: one ticker/company
- output: `OrchestratorDecision`

## Responsibilities

- Aggregate one-ticker evidence across financials, company news, filings, sentiment, Exa search, risks, and update proposals.
- Use code-level fanout for independent specialist tasks when available.
- Preserve partial failures and missing lanes as next-run tasks.
- Produce reviewable alerts, file update proposals, human review items, and next-run tasks.

## Boundaries

- No direct stock trades.
- No direct company-file writes.
- No direct memory writes.
- Provider or analysis execution must go through guarded tools and runtime permissions.
- Company-file edits must flow through proposal review and approved deterministic writer.

## Current Specialist Coverage

- SDK specialist available: `company_news_specialist`.
- Deterministic artifact lanes available: financial review, SEC provider packets, xAI/Grok sentiment packets, Exa packets.
- Future SDK specialists should be added for financials, filings, sentiment, Exa company search, writer, and quality review.
