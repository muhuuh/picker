# Company Research Quality Reviewer Spec

- id: quality_reviewer_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.quality_review`
- output type: `SpecialistResult`
- primary inputs:
  - company research packet
  - evidence packets and reports
  - run summary, quality report, and run metrics
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
