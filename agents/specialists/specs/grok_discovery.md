# xAI Grok X Discovery Specialist Spec

- id: grok_discovery_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.grok_discovery`
- output type: `SpecialistResult`
- primary inputs:
  - xAI/Grok `x_search` evidence packets
  - X citations surfaced by Grok
  - research priorities and human industry/theme requests
  - source-quality and direct-X deprecation memory
- write behavior: no direct writes
- callable modes:
  - market-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
- guardrail: Grok/X output is social signal and lead generation only; verify material claims elsewhere.
