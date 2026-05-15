# Memory Reflection: 2026-05-16_weekly

Generated: 2026-05-16

## Metrics

- manifest_exists: True
- run_summary_exists: True
- quality_report_exists: True
- provider_tasks_planned: 19
- analysis_tasks_planned: 10
- evidence_packets: 24
- valid_evidence_packets: 24
- invalid_evidence_packets: 0
- provider_packet_counts: {"alpha_vantage": 2, "company_news_specialist": 1, "exa": 5, "financial_compare": 2, "financial_data_specialist": 2, "fmp": 2, "opportunity_assessment_specialist": 1, "polygon": 2, "sec_edgar": 2, "xai_grok": 3, "yfinance": 2}
- claims: 50
- risks: 5
- contradictions: 2
- recommended_updates: 5
- unknowns: 4
- run_metrics_exists: True
- sdk_metric_rows: 19
- sdk_agent_runs: 1
- sdk_tool_calls: 12
- sdk_llm_calls: 3
- sdk_timeout_metrics: 0
- sdk_error_metrics: 0
- sdk_memory_context_ids: ["orch-2026-05-03-deterministic-first", "orch-2026-05-03-direct-x-replaced", "orch-2026-05-03-dry-run-provider-tasks", "orch-2026-05-03-human-input-vs-review", "orch-2026-05-04-after-provider-tasks-and-analysis-tasks-use-pyth", "orch-2026-05-04-analysis-tasks-can-now-be-dry-run-or-executed-fr", "orch-2026-05-04-financial-compare-before-specialist", "orch-2026-05-04-generated-run-json-is-local", "orch-2026-05-04-provider-task-artifact-ids", "orch-2026-05-06-agent-runtime-quality-gates", "orch-2026-05-06-agent-runtime-registry", "orch-2026-05-06-clean-generated-run-artifacts", "orch-2026-05-06-openai-agents-sdk-selected", "orch-2026-05-06-scheduled-sdk-freshness-gate", "orch-2026-05-07-approved-proposal-writer", "orch-2026-05-07-function-first-tooling-boundary", "orch-2026-05-07-guarded-sdk-provider-analysis-tools", "orch-2026-05-07-sdk-proposals-before-file-writes", "orch-2026-05-07-task-specific-sdk-memory-injection", "orch-2026-05-10-candidate-review-bridge", "orch-2026-05-10-company-research-sub-orchestrator", "orch-2026-05-10-grok-required-for-discovery", "orch-2026-05-10-local-sdk-telemetry-hooks", "orch-2026-05-10-manual-market-research-runner", "orch-2026-05-10-scheduled-company-research-fanout", "orch-2026-05-10-sdk-fanout-helper", "orch-2026-05-10-sdk-timeout-error-policy", "orch-2026-05-11-approved-candidate-verification", "orch-2026-05-11-candidate-promotion-gate", "orch-2026-05-11-candidate-verification-result", "orch-2026-05-11-digest-first-human-review", "orch-2026-05-11-human-review-decision-updater", "orch-2026-05-11-human-review-digest", "orch-2026-05-11-main-aggregation-packet", "orch-2026-05-11-memory-evaluation-orchestrator", "orch-2026-05-11-portfolio-review-orchestrator"]
- sdk_memory_output_ids: ["orch-2026-05-03-deterministic-first", "orch-2026-05-06-agent-runtime-registry", "orch-2026-05-10-company-research-sub-orchestrator", "orch-2026-05-11-main-aggregation-packet", "orch-2026-05-11-memory-evaluation-orchestrator", "orch-2026-05-11-portfolio-review-orchestrator"]
- issues: 2

## Issues

- [medium] planned_provider_task_without_packet: Manifest task exa_news_company_aapl planned provider exa but no matching evidence packet was found. (agents/runs/2026-05-16_weekly/manifest.json)
- [medium] planned_provider_task_without_packet: Manifest task exa_company_search_company_aapl planned provider exa but no matching evidence packet was found. (agents/runs/2026-05-16_weekly/manifest.json)

## Memory Update Proposals

### proposal-2026-05-16-2026-05-16_weekly-reflection-issues

- action: memory_add
- target_file: evaluation_metrics.md
- reason: Reflection found issues that should be reviewed before the run is considered complete.

```powershell
python -m stock_research memory add --memory-file evaluation_metrics.md --type 'evaluation' --scope 'global' --status 'needs_review' --confidence 'medium' --trigger-source 'post-run reflection for 2026-05-16_weekly' --lesson 'Run 2026-05-16_weekly produced 2 deterministic reflection issue(s). Review `memory_reflection.md`, run summary, quality report, and evidence packets before treating the run as complete.' --use-when 'Reviewing run quality, deciding whether to update operational memory, or planning reruns.' --do-not-use-when 'Making investment conclusions without reviewing underlying evidence.' --evidence '`agents/runs/2026-05-16_weekly/memory_reflection.md`' --owner 'memory and evaluation orchestrator' --next-review '2026-05-16' --today 2026-05-16
```
