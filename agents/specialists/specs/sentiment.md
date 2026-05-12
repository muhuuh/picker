# xAI Grok Sentiment Specialist Spec

- id: sentiment_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.sentiment`
- output type: `SpecialistResult`
- primary inputs:
  - xAI/Grok `x_search` evidence packets
  - raw xAI/Grok artifact references
  - run summary and quality report
  - operational memory context
- write behavior: no direct company-file writes
- quality floor:
  - must not return only a sentiment label
  - must include concrete X/community narratives, bullish and bearish arguments, notable accounts/posts when present, hype/noise assessment, claims to verify, and investor implications
  - must keep X output labeled as social signal until verified by Exa, filings, transcripts, or financial data
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
