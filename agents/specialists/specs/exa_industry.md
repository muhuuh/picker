# Exa Industry Research Specialist Spec

- id: exa_industry_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.exa_industry`
- output type: `SpecialistResult`
- primary inputs:
  - Exa industry/general/news/company evidence packets
  - Exa contents artifacts when available
  - research priorities and human input queue items
  - strategy files
  - operational memory context
- write behavior: no direct writes
- callable modes:
  - market-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
