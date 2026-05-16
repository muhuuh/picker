# AGENTS.md

This file is for AI coding agents (Codex, Copilot agents, Cursor, etc.).
It defines the required workflow for every new task in this repo.

## Working Rules (Always)

1. Start every task with a short plan (bullet points) before making edits.
2. Before starting work, identify the topic and read the matching scratchpad to get up to date.
3. Before starting implementation, read `MEMORY.md` for durable project decisions/facts relevant to the task.
4. Before implementation, read `agents/memory/memory_index.md` and the task-relevant operational memory file(s) it points to. For deterministic inspection, use `python -m stock_research memory context --task TASK`; for specialist prompt injection, use `python -m stock_research memory prompt-context --task TASK`.
5. Keep the matching scratchpad updated during the task (after meaningful steps) and at the end.
6. Before implementing, check `docs/descriptions/` for task-relevant description files and read them.
7. If your changes impact behavior/design documented in a relevant description file, update that file before finishing.
8. For complex or long-running topics, create/update a plan file in `docs/plans/` and keep it current. It should contain the goal of the high-level task and an action plan with prioritized checklist steps.
9. After finishing a task, update the scratchpad with the latest decisions, learnings, and next steps. Update the plan file with the latest progress if one exists for this specific task.
10. Keep language simple and concrete.
11. Do not add/change major dependencies or infra without explicitly calling it out.
12. After major changes, verify `README.md` and `SETUP.md` still match reality.
13. Final responses must include a clear outcome judgment: whether the result is good, partial, or bad; whether it matched the expected goal; what is still pending or risky; and the next logical steps from the backlog or from issues discovered during the task.
14. Prefer function-first tooling. Implement reusable behavior as importable Python functions; deterministic workflows and SDK tools should call those functions directly. Add CLI commands only as thin wrappers for manual operation, scheduler entrypoints, validation/debug, provider smoke tests, or approval-gated side effects.

## Stock Research Repository Model

This repo is for automated stock tracking, investment research, and agent workflow development.

The initial market scope is US and Europe. The default recurring deep research cadence is weekly on Saturday, so the user can review outputs on Sunday before planning the trading week.

### Core folders

- `stock_tracking/`: persistent portfolio and watchlist state.
  - `current_holdings/`: positions we currently hold.
  - `monitoring/`: companies we are watching but have not bought.
  - `rejected/`: companies we reviewed and do not want to pursue for now.
  - `stock_info_files/`: detailed per-company markdown files with filings, thesis, sources, developments, risks, and current opinion.
- `agents/`: intelligence and operation layer.
  - `orchestrator/`: main coordinator and deterministic kickoff workflow.
  - `specialists/`: narrow agents for research, sentiment, filings, finance, file updates, and quality review.
  - `memory/`: operational agent memory for workflow lessons, source quality, specialist playbooks, evaluation metrics, and deprecated behavior.
- `market_research/`: industry, macro, theme, and discovery research outputs.
- `strategy/`: high-level investment strategy, criteria, preferred industries, rejection rules, risk appetite, and current priorities.
- `docs/plans/human_research_requests.md`: queue for proactive user requests that should influence manual or automated research.

### Stock tracking rules

- Each category folder in `stock_tracking/current_holdings/`, `stock_tracking/monitoring/`, and `stock_tracking/rejected/` should have:
  - one CSV overview for basic stock metadata,
  - one category-level markdown file for current general state, findings, next steps, risks, and market context.
- Each current holding and monitoring company should have a detailed markdown file under `stock_tracking/stock_info_files/`.
- Rejected companies may have detailed markdown files when the rejection needs explanation, source history, or future review criteria.
- Rejected companies should not resurface as candidates for 6 weeks after rejection unless the user explicitly asks to review them sooner.
- CSV files are for scanning and routing only. Detailed reasoning belongs in company markdown files and category markdown files.
- Every material claim in stock/company files should cite a source or name the internal artifact that produced it.
- Never store secrets, private account data, or broker credentials in stock files.

### Agent workflow rules

- Treat Codex chat as the primary human interface. The user should be able to give natural-language instructions, and agents should translate them into durable repo state.
- Separate human input from human review:
  - human input queue: things the user wants the system to consider,
  - human review queue: decisions or recommendations the system wants the user to approve.
- Before responding to user research requests, read `docs/descriptions/repo_map.md` and `docs/descriptions/human_interaction_workflow.md` when present.
- Prefer deterministic kickoff steps for recurring runs: load repo state, check planned tasks, gather latest filings/news/sentiment/market context, validate stale records, then pass structured results to the orchestrator.
- For local Codex app automation, prefer Codex-supervised mode: run deterministic provider/analysis/finalization steps, read `agents/runs/{run_id}/codex_supervised_review_pack.md`, and let Codex GPT-5.5 high write the final human-facing synthesis/review. Do not add `--execute-orchestrator` to scheduled Codex automation unless the user explicitly asks for API-mode benchmarking or remote/headless simulation.
- Preserve the API SDK workflow as an optional mode for remote workers, structured traces, specialist fanout debugging, and benchmarks. API mode is not the default local scheduled workflow.
- Use the orchestrator for synthesis, prioritization, routing, and final recommendations.
- Produce both tracked-stock change alerts and new-stock discovery alerts when candidates match the strategy.
- Use specialist agents for bounded work: xAI/Grok X sentiment, industry sentiment, Exa/web search, SEC filing review, financial analysis, stock file updates, market discovery, strategy impact review, and quality control.
- Keep the orchestrator from directly editing detailed company files when a file-update specialist can do a narrower, auditable update.
- All write actions should produce a short change summary with source links and confidence level.
- Any buy/sell/position-size recommendation should be treated as research output for human review, not an automatic trade instruction.
- Agent runs should update relevant scratchpads and plan files with what worked, what failed, useful prompts/tools, stale data risks, and next actions.
- Agent runs should use `agents/memory/` for operational lessons and should not store raw provider output, secrets, or ordinary company facts there.
- Codex-supervised runs must still preserve the learning loop: review run summary, quality report, memory reflection, memory update drafts, finalization, category state updates, artifact hygiene, and human-review digest; update scratchpads/backlog/memory when there is a durable operational lesson.
- After run reflection/finalization proposes memory updates, convert them into reviewable drafts with `python -m stock_research memory draft-updates --run-id RUN_ID --write`, optionally review/refine them through `python -m stock_research memory writer-review --run-id RUN_ID --write`, and apply only approved ready drafts with `python -m stock_research memory apply-updates --run-id RUN_ID --proposal-id PROPOSAL_ID`.
- The bounded LLM memory writer may propose accept/revise/reject decisions, but it must not directly edit `agents/memory/*.md`; memory writes must go through deterministic schema validation and `memory apply-updates`.

## Scratchpads (Topic Memory)

Use the scratchpad that matches the task topic:

If no fitting scratchpad exists, create one from `docs/scratchpads/agent_scratchpad_template.md`.

### Scratchpad Rules (Must Follow)

- Keep entries short and scannable (bullet points, no long essays).
- Capture:
  - what you learned
  - decisions made and why
  - open questions
  - next steps
  - risks/gotchas
  - useful commands/env notes
- Never store secrets (tokens, API keys, passwords, private customer data).

## Plan Files (Only for Complex/Long Topics)

Use plan files when the work is expected to span multiple chats/iterations or has multiple dependent steps.

Plan files should contain:

- goal and scope
- prioritized action steps, with checkboxes to track progress
- done/pending status per step
- key decisions and date-stamped updates
- any other section or information that is relevant to keep track to complete the task

The overall goal is to have an action plan that is clear with clear steps and priorities on how to complete the tasks so that we can keep track of the progress and our goal over several sessions of work.

## Done Checklist

Before finishing any task:

- [ ] Relevant checks/tests were run, or state why not.
- [ ] Scratchpad updated with latest decisions, learnings, and next steps.
- [ ] `MEMORY.md` reviewed and updated when durable/high-impact decisions or facts changed.
- [ ] `agents/memory/` reviewed and updated when operational lessons, source-quality lessons, or deprecated behavior changed.
- [ ] Relevant description file(s) in `docs/descriptions/` checked and updated if impacted.
- [ ] If the topic is complex/long-running: relevant plan file in `docs/plans/` updated.
- [ ] Risky changes are clearly called out.

## Final Response Requirements

At the end of each task, do not only list files changed. Give the user a concise but useful conclusion:

- Outcome quality: say whether the result is good, partial, or bad.
- Expectation check: say whether the result achieved what we expected at the start of the task.
- Verification: list the checks/tests run, or say why they were not run.
- Remaining gaps: mention anything still pending, weak, risky, or not yet automated.
- Next steps: name the next backlog-driven step and any new step discovered during the task.

Keep this short and concrete. The user should not need to ask again whether the work succeeded or what to do next.
