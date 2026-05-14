# Memory Reflection: 2026-05-16_weekly

Generated: 2026-05-14

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
- run_metrics_exists: False
- sdk_metric_rows: 0
- sdk_agent_runs: 0
- sdk_tool_calls: 0
- sdk_llm_calls: 0
- sdk_timeout_metrics: 0
- sdk_error_metrics: 0
- sdk_memory_context_ids: []
- sdk_memory_output_ids: []
- issues: 2

## Issues

- [medium] planned_provider_task_without_packet: Manifest task exa_news_company_aapl planned provider exa but no matching evidence packet was found. (agents/runs/2026-05-16_weekly/manifest.json)
- [medium] planned_provider_task_without_packet: Manifest task exa_company_search_company_aapl planned provider exa but no matching evidence packet was found. (agents/runs/2026-05-16_weekly/manifest.json)

## Memory Update Proposals

### proposal-2026-05-14-2026-05-16_weekly-reflection-issues

- action: memory_add
- target_file: evaluation_metrics.md
- reason: Reflection found issues that should be reviewed before the run is considered complete.

```powershell
python -m stock_research memory add --memory-file evaluation_metrics.md --type 'evaluation' --scope 'global' --status 'needs_review' --confidence 'medium' --trigger-source 'post-run reflection for 2026-05-16_weekly' --lesson 'Run 2026-05-16_weekly produced 2 deterministic reflection issue(s). Review `memory_reflection.md`, run summary, quality report, and evidence packets before treating the run as complete.' --use-when 'Reviewing run quality, deciding whether to update operational memory, or planning reruns.' --do-not-use-when 'Making investment conclusions without reviewing underlying evidence.' --evidence '`agents/runs/2026-05-16_weekly/memory_reflection.md`' --owner 'memory and evaluation orchestrator' --next-review '2026-05-14' --today 2026-05-14
```
