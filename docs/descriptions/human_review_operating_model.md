# Human Review Operating Model

Last updated: 2026-05-13

## Goal

Make "needs human review" operationally clear.

The system should be able to run asynchronously, continue all safe independent work, and leave only approval-gated decisions waiting for the user. The user should have one concise place to check what needs a decision, and Codex chat should be the normal way to record those decisions.

## Research Basis

The current design follows common human-in-the-loop workflow patterns:

- OpenAI Agents SDK human-in-the-loop approvals pause sensitive tool calls, surface interruptions, and let the run resume later from serialized state. This supports long approval delays and nested `Agent.as_tool()` approvals: https://openai.github.io/openai-agents-python/human_in_the_loop/
- LangGraph interrupts persist graph state with a checkpointer and resume when external input arrives. The important pattern is durable pause/resume, not keeping a process open while waiting for a person: https://docs.langchain.com/oss/python/langgraph/human-in-the-loop
- Durable workflow systems model human interaction as external events with durable state, timeout handling, status tracking, and duplicate-event protection: https://learn.microsoft.com/en-us/azure/durable-task/common/durable-task-human-interaction
- Gmail API push notifications can watch mailbox changes, but that requires additional infrastructure and should be treated as notification/input ingestion, not the first canonical approval path: https://developers.google.com/workspace/gmail/api/guides/push

## Canonical Review Surfaces

The durable source of truth is:

```text
agents/human_review_queue.md
```

The human-facing summary is:

```text
agents/human_review_digest.md
```

The deeper context is in linked artifacts such as:

```text
agents/runs/{run_id}/portfolio_review/portfolio_review.md
agents/runs/{run_id}/market_research/candidate_review.md
agents/runs/{run_id}/market_research/candidate_verification_result.md
agents/runs/{run_id}/orchestrator_update_proposals.md
agents/runs/{run_id}/memory_evaluation/memory_evaluation.md
```

The user should not need to read every report after every run. The normal path is:

1. Read or ask Codex to summarize `agents/human_review_digest.md`.
2. Decide only the listed open HRQ items.
3. Use linked deeper reports when a decision needs context.
4. Tell Codex the decisions in natural language.
5. Codex records the decisions with the deterministic decision writer.

The digest should explain the difference between review categories:

- `Monitoring Candidate Reviews`: source-backed discovery candidates that may enter the monitoring approval path after the user reads the linked candidate review and market report.
- `Grok/X Candidate Verification`: early social/X leads; approval only starts verification and never adds a stock to monitoring.
- `Candidate Verification`: Exa-only or otherwise incomplete leads; approval starts company/news/financial verification before any monitoring decision.
- `Company File Updates`: scoped proposed edits; multiple rows for one ticker can be valid when they are separate update proposals.
- `Strategy / Workflow`: process or strategy changes that future runs should remember.

Future company-file UX target:

- Low-risk factual updates that are source-backed and do not change thesis/status should be auto-applied by a scoped deterministic writer and summarized at run end.
- Thesis changes, opinion changes, stock moves, strategy changes, and ambiguous edits should remain approval-gated in the digest.

## Who Reads Portfolio Review

`portfolio_review_orchestrator` writes a portfolio review report for two audiences:

- Main orchestrator and Codex: use it as structured input for final synthesis, prioritization, and review-digest generation.
- Human user: read it only when the digest points to a portfolio-level decision, urgent bucket issue, or unresolved ambiguity.

The portfolio review report is not the primary human inbox. The digest is.

## Human Decision Vocabulary

Every review item should make the allowed actions clear:

- `approve`: the user agrees to the proposed next gated action.
- `reject`: the user does not want the system to pursue that item.
- `needs_more_research`: the user wants more evidence before a decision.
- `leave_open`: the user intentionally postpones the decision.
- `supersede`: the item is no longer relevant because another decision or artifact replaced it.

Codex may accept natural language like:

```text
Approve HRQ-0007 for verification, reject HRQ-0008, and leave HRQ-0009 open.
```

Codex should translate that into:

```powershell
python -m stock_research human-review decide --set HRQ-0007=approved --set HRQ-0008=rejected --set HRQ-0009=open --note "User decision via Codex chat." --write
```

Recording a decision does not perform side effects by itself. Follow-up commands remain separate and approval-gated.

## Asynchronous Run Behavior

Runs should not block the whole workflow while waiting for human review.

When approval is needed:

1. Write an HRQ row.
2. Refresh the digest.
3. Continue independent safe work.
4. Mark only the gated branch as `waiting_for_human`.
5. Do not apply file writes, stock moves, strategy changes, memory changes, or monitoring promotion until the required approval exists.

Examples:

- A discovery candidate can be queued for review while other candidate checks continue.
- A company-file update proposal can wait while run summary, memory evaluation, and portfolio review finish.
- A missing approval should not prevent quality reports or memory reflection from running.

## Notification Policy

Near term:

- Codex chat and repo artifacts are the canonical review interface.
- Manual or Codex automation runs should end by summarizing the current review digest.
- The user can ask Codex: "show my open review items" or "approve HRQ-0007 for verification."

Later:

- Add Codex app automation or email notification that sends a concise digest when new high-priority review items appear.
- Email should initially be notification only, with decisions recorded through Codex chat.
- Email reply ingestion can be evaluated later if the review digest is stable and the approval grammar is strict enough.

Reason:

- Email reply ingestion needs duplicate detection, identity verification, parsing, error handling, and durable resume logic.
- A notification-only email keeps the user informed without making email the approval source of truth.

## Approval-Gated Follow-Up

Each approved review type maps to a separate deterministic action:

| Review type | Approval means | Follow-up action |
| --- | --- | --- |
| Candidate verification | user wants deeper research | `market-research candidate-followup`, provider tasks, analysis tasks, `candidate-verification-result` |
| Monitoring candidate | user may want tracking after verification | `market-research candidate-promote` only after approval and required verification |
| Company-file proposal | user approves one proposed edit | `agent-runtime apply-proposal` for one proposal id |
| Memory update | user approves one memory draft | `memory apply-updates` for one proposal id |
| Strategy change | user approves strategy adjustment | deterministic strategy file update or explicit Codex edit |
| Stock move | user approves status change | scoped CSV/category/company-file update |

## Automation Plan

When scheduled automation is introduced:

1. Saturday run executes deterministic and SDK-safe work.
2. Run writes reports, review queue rows, and digest.
3. Automation sends the digest summary if new or high-priority items exist.
4. Human reviews later in Codex chat.
5. Next manual or automated run consumes approved HRQ rows and executes only the matching approved follow-up actions.

This keeps asynchronous approval robust: the system does not require the human to be online during the run, and it does not silently act on unreviewed recommendations.

## Guardrails

- Do not treat an email notification as approval unless a future explicit email-ingestion workflow is built and tested.
- Do not promote discovery candidates from Grok-only or rumor-only evidence.
- Do not apply company-file proposals from open, rejected, or missing HRQ rows.
- Do not apply memory updates outside the deterministic schema validation path.
- Do not let expired or duplicate HRQ items create duplicate follow-up work.
- Every digest item should include the HRQ id, decision type, suggested user action, status, confidence or verification state, and linked evidence artifact.
- Human-facing reports should not contain visible truncation markers (`...` or `[...]`), dead source ids without links, duplicated narrative sections, or internal workflow/status prose in the executive read.

## Open Implementation Gaps

- Add a run-end summary step that always prints or writes the open-review digest after manual/weekly runs.
- Add notification automation after digest quality is stable.
- Add optional email digest delivery later.
- Evaluate strict email-reply ingestion only after notifications are stable.
- Add tests for duplicate HRQ decisions, stale approvals, and unsupported review statuses.
