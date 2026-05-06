# Main Orchestrator Spec

- id: main_orchestrator
- role: orchestrator
- runtime module: `stock_research.agent_runtime.orchestrators.main`
- output type: `OrchestratorDecision`
- specialist tools:
  - `company_news_specialist`
- write behavior: proposal-first
- memory: inject task-relevant operational memory before execution
