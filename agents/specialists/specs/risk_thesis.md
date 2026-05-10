# Risk Thesis Specialist Spec

- id: risk_thesis_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.risk_thesis`
- output type: `SpecialistResult`
- primary inputs:
  - company research packet
  - current company file
  - latest evidence packets
  - run summary and quality report
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
