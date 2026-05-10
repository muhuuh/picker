# Exa Company Search Specialist Spec

- id: company_search_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.company_search`
- output type: `SpecialistResult`
- primary inputs:
  - Exa `company` mode evidence packets
  - Exa `general` mode company-context packets when available
  - raw Exa artifact references
  - run summary and quality report
  - operational memory context
- write behavior: no direct company-file writes
- callable modes:
  - direct code runner
  - company-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
