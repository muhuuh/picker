# SEC Filing Specialist Spec

- id: filing_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.filing`
- output type: `SpecialistResult`
- primary inputs:
  - SEC EDGAR evidence packets
  - raw SEC artifact references
  - run summary and quality report
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
