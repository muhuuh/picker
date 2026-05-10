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
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
