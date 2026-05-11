# Memory Evaluation Orchestrator Spec

- id: memory_evaluation_orchestrator
- role: sub-orchestrator
- runtime module: `stock_research.agent_runtime.orchestrators.memory_evaluation`
- output type: `OrchestratorDecision`
- input packet: `MemoryEvaluationPacket`
- function tools:
  - repo/memory inspection tools
- specialist tools:
  - `quality_reviewer_specialist`
- write behavior: report-only; no direct memory writes
- memory: inject task-relevant operational memory before execution
- guardrails:
  - memory changes remain proposal-first
  - approved writes must go through deterministic `memory apply-updates`
  - do not store raw provider output or secrets in operational memory
