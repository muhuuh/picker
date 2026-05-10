# Stock File Proposal Specialist Spec

- id: writer_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.writer`
- output type: `SpecialistResult`
- primary inputs:
  - company research packet
  - exact `stock_info_file` target
  - source-backed evidence packets and reports
  - run summary and quality report
  - operational memory context
- write behavior: proposal-only; no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
