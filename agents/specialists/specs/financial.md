# Financial Specialist Spec

- id: financial_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.financial`
- output type: `SpecialistResult`
- primary inputs:
  - `financial_compare` evidence packets
  - deterministic financial-data specialist review artifacts
  - run summary and quality report
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
