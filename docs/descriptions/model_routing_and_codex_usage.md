# Model Routing And Codex Usage

Last updated: 2026-05-15

## Purpose

This document records where this repo currently uses LLMs, which work can remain deterministic or Codex-driven, and where paid API model calls are actually justified.

The goal is to keep high-quality research output while avoiding unnecessary OpenAI or xAI API spend.

## Current LLM Surfaces

### xAI/Grok API

Used for X.com-native research through xAI Responses API with `x_search`.

Current code paths:

- `stock_research/providers/xai_grok.py`
- `stock_research/provider_runner.py`
- `stock_research/manifest.py`
- `stock_research/market_research_runner.py`
- `stock_research/candidate_followup.py`

Current default model:

- routed through `agents/model_routing.yaml` as `xai_grok_x_search`
- current configured model: `grok-4.3`

Current use:

- stock X sentiment
- latest X narrative shifts
- industry/theme X trend discovery
- hype/noise/rumor mapping
- niche candidate discovery

Recommended routing:

- Keep Grok API for X.com access and X-native insight.
- Use Grok with `x_search` for anything where X.com is the source of edge.
- Do not use Grok as a generic summary model when the input is already in repo artifacts and no X access is needed.

Complexity level:

- Company X sentiment: high
- Industry/theme X discovery: high
- Latest X news pulse: medium-high
- Narrow follow-up on known handles or a known rumor: medium

### OpenAI API Through Agents SDK

Used for live SDK orchestration when `--execute-orchestrator` or `agent-runtime run --execute` is used.

Current code paths:

- `stock_research/agent_runtime/runner.py`
- `stock_research/agent_runtime/registry.py`
- `stock_research/scheduled_runner.py`
- `stock_research/cli.py`

Current model behavior:

- SDK agent runs resolve their model through `stock_research/model_routing.py`.
- The default strong OpenAI route is `gpt-5.5`.
- Balanced, fast, and nano OpenAI routes use `gpt-5.4-mini` to reduce routine autonomous API synthesis cost.
- The CLI still accepts `--model` / `--orchestrator-model`, and explicit overrides win.
- `gpt-4.1` and its 2025-04-14 snapshot are blocked by the model router even if an environment override tries to select them. Older dashboard usage for that model should be treated as pre-routing/legacy SDK usage, not current expected behavior.
- There is no current official `gpt-5.5-mini` route in this repo; `gpt-5.4-mini` is the current lower-cost equivalent selected for non-complex API tasks.

Current use:

- main orchestrator synthesis
- company research sub-orchestrator
- market research sub-orchestrator
- portfolio review sub-orchestrator
- memory/evaluation sub-orchestrator
- specialist-as-tool synthesis agents

Recommended routing:

- Use strong model only for final synthesis, high-stakes thesis/risk synthesis, and complex opportunity assessment.
- Use `gpt-5.4-mini` for source extraction, artifact summarization, quality review, writer proposal drafting, and memory writer review.
- Keep deterministic Python as the default for validation, routing, gating, provider execution, file updates, and artifact hygiene.

### OpenAI API Direct Responses Call

Used for bounded memory-writer review.

Current code path:

- `stock_research/memory_llm_writer.py`

Current default model:

- routed through `agents/model_routing.yaml` as `memory_writer`
- current configured model: `gpt-5.5`

Current use:

- review proposed operational memory updates
- accept, revise, or reject memory drafts

Recommended routing:

- Keep this on a small/cheap model by default.
- Allow escalation only when memory proposals are ambiguous, high-impact, or repeatedly rejected.
- Use Codex chat/automation for manual review and prompt improvement instead of paying an API call when a human-supervised Codex workflow is already running.

Complexity level:

- Low to medium.

### Codex App / Codex Automation

Codex app is the primary human interface and can run repo commands, read reports, summarize outputs, update files, and iterate on prompts using the user's Codex subscription.

Current use:

- human-driven repo work in chat
- manual research requests
- interpreting generated reports
- editing docs, prompts, plans, and tests
- future Codex app automation for weekly/manual runs

Important boundary:

- Python code in this repo cannot directly call "the current Codex chat model" as an internal function.
- Codex can orchestrate the repo from outside by running commands and editing files.
- Codex app/automation can use the user's configured Codex model, currently expected to be GPT-5.5 high in this repo workflow, to run commands, inspect artifacts, summarize results, and improve prompts.
- Programmatic Codex SDK/app-agent control is a separate orchestration surface and should not be mixed into the core stock workflow until tested separately.

Recommended routing:

- Use Codex chat/automation for interactive review, repo maintenance, prompt iteration, command execution, report review, and improvement loops.
- Use Python deterministic commands for repeatable workflow steps.
- Use OpenAI API only when an autonomous Python runtime needs LLM synthesis without a human/Codex chat in the loop.
- Use xAI/Grok API where X.com search is required.

## Complexity-Based Routing Draft

| Task | Current implementation | Complexity | Recommended model/runtime |
| --- | --- | --- | --- |
| Provider API calls: SEC, Exa, yfinance, FMP, Polygon/Massive, Alpha Vantage | deterministic Python | low | no LLM |
| Financial compare | deterministic Python | low-medium | no LLM |
| Financial specialist over existing packets | SDK specialist / deterministic review artifacts | medium | cheap/fast OpenAI or Codex-run synthesis |
| Company news specialist over Exa artifacts | SDK specialist / deterministic review artifacts | medium | cheap/fast OpenAI or Codex-run synthesis |
| Filing specialist over SEC packets | SDK specialist | medium | cheap/fast OpenAI |
| Stock X sentiment collection | xAI/Grok provider | high | Grok 4.3 with `x_search` |
| Industry/theme X discovery | xAI/Grok provider | high | Grok 4.3 with `x_search` |
| Grok discovery synthesis from raw output | SDK specialist / report formatter | medium-high | cheap/fast OpenAI if raw Grok is rich; strong OpenAI only if synthesis quality is poor |
| Market research final report | deterministic formatter plus optional SDK | high | `gpt-5.5` for autonomous API mode; Codex GPT-5.5 high review loop for manual mode; Grok remains source provider |
| Opportunity assessment | deterministic synthesis plus optional SDK specialist | high | `gpt-5.5` for live autonomous runs; Codex GPT-5.5 high review loop for manual runs |
| Main orchestrator final synthesis | OpenAI Agents SDK | high | `gpt-5.5` |
| Portfolio review | SDK sub-orchestrator | medium | cheap/fast OpenAI or deterministic/Codex summary |
| Memory/evaluation review | deterministic plus optional LLM | low-medium | cheap/fast OpenAI or deterministic only |
| Memory writer review | direct OpenAI Responses API | low-medium | cheap/fast OpenAI |
| Human-review digest | deterministic Python | low | no LLM |
| Category state updates | deterministic Python | low | no LLM |
| Artifact hygiene/archive | deterministic Python | low | no LLM |

## Proposed Runtime Modes

### Manual Codex Mode

Best while iterating.

Flow:

1. Codex chat runs deterministic provider/research commands.
2. Provider APIs collect Exa/Grok/financial/filing evidence.
3. Python writes reports and digests.
4. Codex chat reads artifacts and helps improve prompts/reports.
5. OpenAI Agents SDK live calls are optional, not required.

Cost posture:

- Uses paid provider APIs only where needed.
- Avoids OpenAI API synthesis unless explicitly requested.
- Uses already-paid Codex interaction for review and iteration.

### Autonomous API Mode

Best later for unattended scheduled runs.

Flow:

1. Scheduled command runs deterministic provider/analysis tasks.
2. OpenAI Agents SDK runs synthesis agents with configured model routing.
3. Reports, digests, memory reflection, and review items are written automatically.
4. Codex/email/app notification summarizes review items.

Cost posture:

- Uses OpenAI API for autonomous synthesis.
- Requires model routing config to control spend.

## Implemented Routing

The repo now has explicit model routing instead of passing ad hoc model strings everywhere.

Config file:

```text
agents/model_routing.yaml
```

Current shape:

```yaml
defaults:
  openai_strong: gpt-5.5
  openai_balanced: gpt-5.4-mini
  openai_fast: gpt-5.4-mini
  openai_nano: gpt-5.4-mini
  xai_grok_x_search: grok-4.3
  codex_manual_model: gpt-5.5
  codex_manual_reasoning: high

routes:
  main_orchestrator:
    complexity: high
    provider: openai
    model_tier: strong
  company_research_orchestrator:
    complexity: high
    provider: openai
    model_tier: strong
  market_research_orchestrator:
    complexity: high
    provider: openai
    model_tier: strong
  portfolio_review_orchestrator:
    complexity: medium
    provider: openai
    model_tier: fast
  memory_evaluation_orchestrator:
    complexity: medium
    provider: openai
    model_tier: fast
  memory_writer:
    complexity: low_medium
    provider: openai
    model_tier: fast
  xai_stock_sentiment:
    complexity: high
    provider: xai
    model_tier: grok_x_search
  xai_industry_discovery:
    complexity: high
    provider: xai
    model_tier: grok_x_search
```

Implemented code paths:

- `stock_research/model_routing.py`
- OpenAI Agents SDK `RunConfig.model` routing in `stock_research/agent_runtime/runner.py`
- bounded memory-writer model routing in `stock_research/memory_llm_writer.py`
- xAI/Grok provider-task and manual-market routing in manifests/runners
- CLI inspection through `python -m stock_research model-routing show --route ROUTE_OR_TASK`
- tests for strong/fast/xAI routes and override precedence
- guard test that rejects legacy `gpt-4.1` overrides

Override precedence:

1. explicit CLI/function model override
2. route-specific environment variable, e.g. `STOCK_RESEARCH_MODEL_MAIN_ORCHESTRATOR`
3. tier environment variable, e.g. `STOCK_RESEARCH_OPENAI_STRONG_MODEL` or `STOCK_RESEARCH_XAI_GROK_MODEL`
4. `agents/model_routing.yaml`
5. built-in fallback in `stock_research/model_routing.py`

Operational rule:

- In manual Codex mode, prefer Codex app/automation with GPT-5.5 high for report review, prompt iteration, repo edits, and synthesis critique.
- In autonomous API mode, use the routed OpenAI API model because Python must call an API model when no Codex chat is actively supervising.
- Use Grok API only where X.com access is the edge.
- Use no LLM for deterministic provider execution, validation, artifact hygiene, state updates, and human-review digest generation.

## Sources Checked

- OpenAI Agents SDK model docs: per-agent and per-run model configuration, mixing models, Responses API default.
- OpenAI Agents SDK config docs: `OPENAI_API_KEY`, default client, and base URL behavior.
- Codex SDK docs: Codex can be controlled programmatically from the local app/CLI environment.
- xAI X Search docs: `x_search` supports handle filters, date filters, image/video understanding, and Responses API usage.
- xAI model docs: current default general recommendation is Grok 4.3; older Grok text model slugs retire/redirect on 2026-05-15.
