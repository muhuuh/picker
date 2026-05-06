# Company News Specialist Spec

- id: company_news_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.company_news`
- output type: `SpecialistResult`
- primary inputs:
  - run markdown artifacts
  - Exa company-news review artifacts
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - `Agent.as_tool()` for main orchestrator
