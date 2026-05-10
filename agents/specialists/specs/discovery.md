# Candidate Discovery Specialist Spec

- id: discovery_specialist
- role: specialist
- runtime module: `stock_research.agent_runtime.specialists.discovery`
- output type: `SpecialistResult`
- primary inputs:
  - Exa verified web/company evidence
  - Grok/X trend, hype, rumor, and sentiment evidence
  - strategy files
  - rejected cooldown state
  - operational memory context
- write behavior: no direct writes
- callable modes:
  - market-research sub-orchestrator fanout
  - `Agent.as_tool()` for orchestrator use
- guardrail: do not promote Grok/X-only leads or rejected-cooldown names without human review.
