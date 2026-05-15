from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .repo import RepoState
from .validation import parse_date
from .model_routing import resolve_model_for_route
from .providers.xai_grok import industry_sentiment_prompt, latest_news_prompt, stock_sentiment_prompt


ACTIVE_HUMAN_REQUEST_STATUSES = {"new", "triaged", "queued_for_weekly_run", "in_progress"}
TRACKED_STOCK_TABLES = ("current_holdings", "monitoring")


def build_weekly_manifest(state: RepoState, today: date | None = None) -> dict[str, Any]:
    current_date = today or date.today()
    run_date = next_saturday(current_date)
    human_requests = active_human_requests(state.human_requests)
    priorities = active_research_priorities(state.research_priorities)

    manifest = {
        "manifest_version": 1,
        "manifest_id": f"weekly_{run_date.isoformat()}",
        "generated_at": datetime.combine(current_date, datetime.min.time()).isoformat(),
        "run_type": "weekly",
        "run_date": run_date.isoformat(),
        "scope": ["US", "Europe"],
        "inputs": {
            "stock_tables": {
                name: {
                    "path": table.path.relative_to(state.root).as_posix(),
                    "rows": len([row for row in table.rows if any(value.strip() for value in row.values())]),
                }
                for name, table in state.stock_tables.items()
            },
            "human_requests": human_requests,
            "research_priorities": priorities,
            "human_review_items": open_review_items(state.human_review_items),
        },
        "tracked_tickers": tracked_tickers(state),
        "cooldown": rejected_cooldown_summary(state, current_date),
        "tasks": build_tasks(human_requests, priorities),
        "provider_tasks": build_provider_tasks(state, human_requests, priorities, run_date),
        "analysis_tasks": build_analysis_tasks(state, human_requests, run_date),
        "outputs": {
            "run_summary": f"agents/runs/{run_date.isoformat()}_weekly/run_summary.md",
            "quality_report": f"agents/runs/{run_date.isoformat()}_weekly/quality_report.md",
            "manifest": f"agents/runs/{run_date.isoformat()}_weekly/manifest.json",
        },
    }
    return manifest


def write_manifest(state: RepoState, manifest: dict[str, Any], output: Path | None = None) -> Path:
    target = output
    if target is None:
        run_date = manifest["run_date"]
        target = state.root / "agents" / "runs" / f"{run_date}_weekly" / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def next_saturday(value: date) -> date:
    days_until_saturday = (5 - value.weekday()) % 7
    return value + timedelta(days=days_until_saturday)


def active_human_requests(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    active = []
    for row in rows:
        status = row.get("Status", "").strip().lower()
        next_run = row.get("Next Run", "").strip().lower()
        if status in ACTIVE_HUMAN_REQUEST_STATUSES and next_run not in {"no", "false", "n"}:
            active.append(row)
    return active


def active_research_priorities(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("Status", "").strip().lower() in {"active", "watch", "watching"}]


def open_review_items(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("Status", "").strip().lower() in {"open", "needs_more_research"}]


def tracked_tickers(state: RepoState) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, table in state.stock_tables.items():
        result[name] = [row.get("ticker", "").strip() for row in table.rows if row.get("ticker", "").strip()]
    return result


def rejected_cooldown_summary(state: RepoState, today: date) -> dict[str, list[dict[str, str]]]:
    in_cooldown: list[dict[str, str]] = []
    eligible: list[dict[str, str]] = []
    missing_dates: list[dict[str, str]] = []

    for row in state.stock_tables["rejected"].rows:
        ticker = row.get("ticker", "").strip()
        if not ticker:
            continue
        eligible_at = parse_date(row.get("next_eligible_review_date", ""))
        item = {
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "next_eligible_review_date": row.get("next_eligible_review_date", ""),
        }
        if not eligible_at:
            missing_dates.append(item)
        elif eligible_at > today:
            in_cooldown.append(item)
        else:
            eligible.append(item)

    return {"in_cooldown": in_cooldown, "eligible": eligible, "missing_dates": missing_dates}


def build_tasks(human_requests: list[dict[str, str]], priorities: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks = [
        {"id": "validate_repo_state", "kind": "deterministic", "reason": "Always validate repo state before research."},
        {"id": "scan_current_holdings", "kind": "research", "reason": "Weekly tracked-stock alert coverage."},
        {"id": "scan_monitoring", "kind": "research", "reason": "Weekly watchlist alert coverage."},
        {"id": "check_rejected_cooldowns", "kind": "deterministic", "reason": "Rejected stocks can resurface after 6 weeks."},
    ]
    if human_requests:
        tasks.append(
            {
                "id": "process_human_input_queue",
                "kind": "deterministic",
                "reason": f"{len(human_requests)} human request(s) are active for this run.",
            }
        )
    if priorities:
        tasks.append(
            {
                "id": "scan_research_priorities",
                "kind": "research",
                "reason": f"{len(priorities)} active research priority item(s).",
            }
        )
    return tasks


def build_analysis_tasks(state: RepoState, human_requests: list[dict[str, str]], run_date: date) -> list[dict[str, Any]]:
    run_id = f"{run_date.isoformat()}_weekly"
    tasks: list[dict[str, Any]] = []
    seen_task_ids: set[str] = set()

    for bucket in TRACKED_STOCK_TABLES:
        for row in state.stock_tables[bucket].rows:
            ticker = normalize_ticker(row.get("ticker", ""))
            if not ticker:
                continue
            contents_id = f"company_news_contents_follow_up_{slugify(ticker)}"
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=contents_id,
                    tool="company_news_contents_follow_up",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "max_urls": 3},
                    reason=f"Run Exa contents follow-up for high-value company-news URLs for {bucket} ticker {ticker}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    expected_artifacts=["exa_contents_evidence_packet", "exa_contents_raw_json"],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"company_news_review_{slugify(ticker)}",
                    tool="company_news_review",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id},
                    reason=f"Run company-news specialist review for {bucket} ticker {ticker} after Exa contents follow-up.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    depends_on=[contents_id],
                    expected_artifacts=["company_news_specialist_evidence_packet", "company_news_review_json", "company_news_review_markdown"],
                ),
            )
            compare_id = f"financial_compare_{slugify(ticker)}"
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=compare_id,
                    tool="financial_compare",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id},
                    reason=f"Compare financial provider packets for {bucket} ticker {ticker} before synthesis.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"financial_review_{slugify(ticker)}",
                    tool="financial_review",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id},
                    reason=f"Run financial-data specialist review for {bucket} ticker {ticker} after comparison.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    depends_on=[compare_id],
                    expected_artifacts=["financial_specialist_evidence_packet", "financial_review_json", "financial_review_markdown"],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"opportunity_assessment_{slugify(ticker)}",
                    tool="opportunity_assessment",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id},
                    reason=f"Build deterministic opportunity assessment for {bucket} ticker {ticker} from all evidence lanes.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    depends_on=[f"company_news_review_{slugify(ticker)}", f"financial_review_{slugify(ticker)}"],
                    expected_artifacts=[
                        "opportunity_assessment_evidence_packet",
                        "opportunity_assessment_json",
                        "opportunity_assessment_markdown",
                    ],
                ),
            )

    for request in human_requests:
        if request.get("Type", "").strip().lower() != "stock_research":
            continue
        request_id = request.get("ID", "").strip() or "human_request"
        priority = request.get("Priority", "").strip().lower() or "medium"
        for ticker in split_cell_values(request.get("Tickers", "")):
            ticker_upper = normalize_ticker(ticker)
            if not ticker_upper:
                continue
            contents_id = f"company_news_contents_follow_up_human_{slugify(request_id)}_{slugify(ticker_upper)}"
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=contents_id,
                    tool="company_news_contents_follow_up",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id, "max_urls": 3},
                    reason=f"Run Exa contents follow-up for human stock research request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    expected_artifacts=["exa_contents_evidence_packet", "exa_contents_raw_json"],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"company_news_review_human_{slugify(request_id)}_{slugify(ticker_upper)}",
                    tool="company_news_review",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id},
                    reason=f"Run company-news specialist review for human stock research request {request_id} after Exa contents follow-up.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    depends_on=[contents_id],
                    expected_artifacts=["company_news_specialist_evidence_packet", "company_news_review_json", "company_news_review_markdown"],
                ),
            )
            compare_id = f"financial_compare_human_{slugify(request_id)}_{slugify(ticker_upper)}"
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=compare_id,
                    tool="financial_compare",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id},
                    reason=f"Compare financial provider packets for human stock research request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"financial_review_human_{slugify(request_id)}_{slugify(ticker_upper)}",
                    tool="financial_review",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id},
                    reason=f"Run financial-data specialist review for human stock research request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    depends_on=[compare_id],
                    expected_artifacts=["financial_specialist_evidence_packet", "financial_review_json", "financial_review_markdown"],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                analysis_task(
                    task_id=f"opportunity_assessment_human_{slugify(request_id)}_{slugify(ticker_upper)}",
                    tool="opportunity_assessment",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id},
                    reason=f"Build deterministic opportunity assessment for human stock research request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    depends_on=[
                        f"company_news_review_human_{slugify(request_id)}_{slugify(ticker_upper)}",
                        f"financial_review_human_{slugify(request_id)}_{slugify(ticker_upper)}",
                    ],
                    expected_artifacts=[
                        "opportunity_assessment_evidence_packet",
                        "opportunity_assessment_json",
                        "opportunity_assessment_markdown",
                    ],
                ),
            )

    return tasks


def analysis_task(
    task_id: str,
    tool: str,
    subject_id: str,
    args: dict[str, Any],
    reason: str,
    priority: str = "medium",
    source_bucket: str = "",
    depends_on: list[str] | None = None,
    expected_artifacts: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "phase": "post_provider_analysis",
        "tool": tool,
        "subject_type": "company",
        "subject_id": subject_id,
        "args": args,
        "priority": normalize_priority(priority),
        "source_bucket": source_bucket,
        "reason": reason,
        "expected_artifacts": expected_artifacts or ["raw_financial_comparison_json", "evidence_packet"],
        "depends_on": depends_on or ["provider_tasks"],
    }


def build_provider_tasks(
    state: RepoState,
    human_requests: list[dict[str, str]],
    priorities: list[dict[str, str]],
    run_date: date,
) -> list[dict[str, Any]]:
    run_id = f"{run_date.isoformat()}_weekly"
    xai_stock_model = resolve_model_for_route(state.root, "xai_stock_sentiment").model
    xai_industry_model = resolve_model_for_route(state.root, "xai_industry_discovery").model
    xai_latest_news_model = resolve_model_for_route(state.root, "xai_latest_news").model
    tasks: list[dict[str, Any]] = []
    seen_task_ids: set[str] = set()

    for bucket in TRACKED_STOCK_TABLES:
        for row in state.stock_tables[bucket].rows:
            ticker = normalize_ticker(row.get("ticker", ""))
            if not ticker:
                continue
            company = row.get("company_name", "").strip()
            label = company_label(ticker, company)
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"yfinance_company_{slugify(ticker)}",
                    provider="yfinance",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "period": "5d"},
                    reason=f"Weekly market-data snapshot for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"fmp_company_{slugify(ticker)}",
                    provider="fmp",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "include_statements": False},
                    reason=f"FMP market-data/fundamentals cross-check for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"alpha_vantage_company_{slugify(ticker)}",
                    provider="alpha_vantage",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "include_statements": False},
                    reason=f"Alpha Vantage quote/overview cross-check for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    conditions=["Watch Alpha Vantage rate limits, especially on free keys."],
                ),
            )
            if is_us_market_candidate(row):
                add_task(
                    tasks,
                    seen_task_ids,
                    provider_task(
                        task_id=f"polygon_company_{slugify(ticker)}",
                        provider="polygon",
                        tool="company",
                        subject_type="company",
                        subject_id=ticker,
                        args={"ticker": ticker, "run_id": run_id, "adjusted": True},
                        reason=f"Polygon/Massive U.S. ticker reference and OHLC cross-check for {bucket} ticker {label}.",
                        priority="high" if bucket == "current_holdings" else "medium",
                        source_bucket=bucket,
                    ),
                )
            if is_sec_candidate(row):
                add_task(
                    tasks,
                    seen_task_ids,
                    provider_task(
                        task_id=f"sec_company_{slugify(ticker)}",
                        provider="sec_edgar",
                        tool="company",
                        subject_type="company",
                        subject_id=ticker,
                        args={"ticker": ticker, "run_id": run_id, "include_facts": False},
                        reason=f"Weekly SEC filings check for {bucket} ticker {label}.",
                        priority="high" if bucket == "current_holdings" else "medium",
                        source_bucket=bucket,
                        conditions=["Run only if the ticker resolves in SEC company tickers."],
                    ),
                )
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"exa_news_company_{slugify(ticker)}",
                    provider="exa",
                    tool="search",
                    subject_type="company",
                    subject_id=ticker,
                    args={
                        "mode": "news",
                        "query": company_news_query(ticker, company),
                        "run_id": run_id,
                        "num_results": 8 if bucket == "current_holdings" else 5,
                    },
                    reason=f"Default Exa company-news scan for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    follow_up=["Use Exa contents on high-value results before orchestrator synthesis."],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"exa_company_search_company_{slugify(ticker)}",
                    provider="exa",
                    tool="search",
                    subject_type="company",
                    subject_id=ticker,
                    args={
                        "mode": "company",
                        "query": company_search_query(ticker, company),
                        "run_id": run_id,
                        "num_results": 5,
                    },
                    reason=f"Default Exa company-search context scan for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                    follow_up=["Use Exa contents for high-value company/source-discovery results before company-file updates."],
                ),
            )
            add_task(
                tasks,
                seen_task_ids,
                provider_task(
                    task_id=f"xai_x_search_company_{slugify(ticker)}",
                    provider="xai_grok",
                    tool="x_search",
                    subject_type="company",
                    subject_id=ticker,
                    args={
                        "prompt": stock_sentiment_prompt(ticker, company),
                        "run_id": run_id,
                        "research_kind": "stock_sentiment",
                        "model": xai_stock_model,
                        **x_search_window_args(run_date, days=14),
                    },
                    reason=f"Default Grok x_search community-sentiment scan for {bucket} ticker {label}.",
                    priority="high" if bucket == "current_holdings" else "medium",
                    source_bucket=bucket,
                ),
            )

    for priority in priorities:
        topic = priority.get("Topic", "").strip()
        priority_type = priority.get("Type", "").strip().lower()
        if not topic:
            continue
        subject_type = subject_type_for_priority(priority_type)
        subject_id = slugify(topic)
        add_task(
            tasks,
            seen_task_ids,
            provider_task(
                task_id=f"exa_research_priority_{subject_id}",
                provider="exa",
                tool="search",
                subject_type=subject_type,
                subject_id=subject_id,
                args={
                    "mode": "industry" if subject_type == "industry" else "general",
                    "query": research_priority_query(priority),
                    "run_id": run_id,
                    "num_results": 8,
                },
                reason=f"Default Exa scan for active research priority: {topic}.",
                priority=priority.get("Priority", "").strip().lower() or "medium",
                source_bucket="research_priorities",
                follow_up=["Use Exa company search when the priority implies candidate discovery."],
            ),
        )
        add_task(
            tasks,
            seen_task_ids,
            provider_task(
                task_id=f"exa_discovery_priority_{subject_id}",
                provider="exa",
                tool="search",
                subject_type=subject_type,
                subject_id=subject_id,
                args={
                    "mode": "company",
                    "query": discovery_query(topic, priority.get("Geography", "")),
                    "run_id": run_id,
                    "num_results": 10,
                },
                reason=f"Default Exa company-discovery scan for active research priority: {topic}.",
                priority=priority.get("Priority", "").strip().lower() or "medium",
                source_bucket="research_priorities",
            ),
        )
        add_task(
            tasks,
            seen_task_ids,
            provider_task(
                task_id=f"xai_x_search_priority_{subject_id}",
                provider="xai_grok",
                tool="x_search",
                subject_type=subject_type,
                subject_id=subject_id,
                    args={
                        "prompt": industry_sentiment_prompt(topic),
                        "run_id": run_id,
                        "research_kind": "industry_sentiment",
                        "model": xai_industry_model,
                        **x_search_window_args(run_date, days=21),
                        "enable_image_understanding": True,
                    },
                reason=f"Default Grok x_search sentiment scan for active research priority: {topic}.",
                priority=priority.get("Priority", "").strip().lower() or "medium",
                source_bucket="research_priorities",
            ),
        )

    for request in human_requests:
        for task in provider_tasks_for_human_request(
            request,
            run_id,
            xai_stock_model=xai_stock_model,
            xai_industry_model=xai_industry_model,
            xai_latest_news_model=xai_latest_news_model,
        ):
            add_task(tasks, seen_task_ids, task)

    return tasks


def provider_tasks_for_human_request(
    request: dict[str, str],
    run_id: str,
    *,
    xai_stock_model: str = "grok-4.3",
    xai_industry_model: str = "grok-4.3",
    xai_latest_news_model: str = "grok-4.3",
) -> list[dict[str, Any]]:
    request_id = request.get("ID", "").strip() or "human_request"
    request_type = request.get("Type", "").strip().lower()
    request_text = request.get("Request", "").strip()
    priority = request.get("Priority", "").strip().lower() or "medium"
    tasks: list[dict[str, Any]] = []

    if request_type == "stock_research":
        for ticker in split_cell_values(request.get("Tickers", "")):
            ticker_upper = normalize_ticker(ticker)
            if not ticker_upper:
                continue
            tasks.append(
                provider_task(
                    task_id=f"fmp_human_{slugify(request_id)}_company_{slugify(ticker_upper)}",
                    provider="fmp",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id, "include_statements": False},
                    reason=f"Human input queue FMP stock research cross-check request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                )
            )
            tasks.append(
                provider_task(
                    task_id=f"alpha_vantage_human_{slugify(request_id)}_company_{slugify(ticker_upper)}",
                    provider="alpha_vantage",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker_upper,
                    args={"ticker": ticker_upper, "run_id": run_id, "include_statements": False},
                    reason=f"Human input queue Alpha Vantage stock research cross-check request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    conditions=["Watch Alpha Vantage rate limits, especially on free keys."],
                )
            )
            tasks.append(
                provider_task(
                    task_id=f"exa_human_{slugify(request_id)}_news_{slugify(ticker_upper)}",
                    provider="exa",
                    tool="search",
                    subject_type="company",
                    subject_id=ticker_upper,
                    args={
                        "mode": "news",
                        "query": f"{ticker_upper} latest material company news earnings guidance risk stock",
                        "run_id": run_id,
                        "num_results": 8,
                    },
                    reason=f"Human input queue stock research request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    follow_up=["Use Exa contents for high-value result follow-up."],
                )
            )
            tasks.append(
                provider_task(
                    task_id=f"exa_human_{slugify(request_id)}_company_search_{slugify(ticker_upper)}",
                    provider="exa",
                    tool="search",
                    subject_type="company",
                    subject_id=ticker_upper,
                    args={
                        "mode": "company",
                        "query": company_search_query(ticker_upper, ""),
                        "run_id": run_id,
                        "num_results": 5,
                    },
                    reason=f"Human input queue Exa company-search context request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                    follow_up=["Use Exa contents for high-value company/source-discovery result follow-up."],
                )
            )
            tasks.append(
                provider_task(
                    task_id=f"xai_human_{slugify(request_id)}_x_search_{slugify(ticker_upper)}",
                    provider="xai_grok",
                    tool="x_search",
                    subject_type="company",
                    subject_id=ticker_upper,
                    args={
                        "prompt": stock_sentiment_prompt(ticker_upper),
                        "run_id": run_id,
                        "research_kind": "stock_sentiment",
                        "model": xai_stock_model,
                        **x_search_window_args_from_run_id(run_id, days=14),
                    },
                    reason=f"Human input queue Grok x_search stock sentiment request {request_id}.",
                    priority=priority,
                    source_bucket="human_input_queue",
                )
            )
    elif request_type == "industry_research":
        for topic in split_cell_values(request.get("Industries / Themes", "")) or [request_text]:
            subject_id = slugify(topic)
            tasks.extend(
                [
                    provider_task(
                        task_id=f"exa_human_{slugify(request_id)}_industry_{subject_id}",
                        provider="exa",
                        tool="search",
                        subject_type="industry",
                        subject_id=subject_id,
                        args={"mode": "industry", "query": topic, "run_id": run_id, "num_results": 8},
                        reason=f"Human input queue industry request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                    provider_task(
                        task_id=f"exa_human_{slugify(request_id)}_company_{subject_id}",
                        provider="exa",
                        tool="search",
                        subject_type="industry",
                        subject_id=subject_id,
                        args={"mode": "company", "query": discovery_query(topic, ""), "run_id": run_id, "num_results": 10},
                        reason=f"Human input queue industry discovery request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                    provider_task(
                        task_id=f"xai_human_{slugify(request_id)}_x_search_{subject_id}",
                        provider="xai_grok",
                        tool="x_search",
                        subject_type="industry",
                        subject_id=subject_id,
                        args={
                            "prompt": industry_sentiment_prompt(topic),
                            "run_id": run_id,
                            "research_kind": "industry_sentiment",
                            "model": xai_industry_model,
                            **x_search_window_args_from_run_id(run_id, days=21),
                            "enable_image_understanding": True,
                        },
                        reason=f"Human input queue Grok x_search industry sentiment request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                ]
            )
    elif request_type == "theme_tracking":
        for topic in split_cell_values(request.get("Industries / Themes", "")) or [request_text]:
            subject_id = slugify(topic)
            tasks.extend(
                [
                    provider_task(
                        task_id=f"exa_human_{slugify(request_id)}_general_{subject_id}",
                        provider="exa",
                        tool="search",
                        subject_type="theme",
                        subject_id=subject_id,
                        args={"mode": "general", "query": topic, "run_id": run_id, "num_results": 8},
                        reason=f"Human input queue theme request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                    provider_task(
                        task_id=f"exa_human_{slugify(request_id)}_news_{subject_id}",
                        provider="exa",
                        tool="search",
                        subject_type="theme",
                        subject_id=subject_id,
                        args={
                            "mode": "news",
                            "query": f"{topic} latest news public companies investment implications",
                            "run_id": run_id,
                            "num_results": 8,
                        },
                        reason=f"Human input queue theme-news request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                    provider_task(
                        task_id=f"xai_human_{slugify(request_id)}_x_search_{subject_id}",
                        provider="xai_grok",
                        tool="x_search",
                        subject_type="theme",
                        subject_id=subject_id,
                        args={
                            "prompt": latest_news_prompt(topic),
                            "run_id": run_id,
                            "research_kind": "latest_news",
                            "model": xai_latest_news_model,
                            **x_search_window_args_from_run_id(run_id, days=14),
                            "enable_image_understanding": True,
                        },
                        reason=f"Human input queue Grok x_search theme/news request {request_id}.",
                        priority=priority,
                        source_bucket="human_input_queue",
                    ),
                ]
            )
    return tasks


def provider_task(
    task_id: str,
    provider: str,
    tool: str,
    subject_type: str,
    subject_id: str,
    args: dict[str, Any],
    reason: str,
    priority: str = "medium",
    source_bucket: str = "",
    conditions: list[str] | None = None,
    follow_up: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "phase": "deterministic_kickoff",
        "provider": provider,
        "tool": tool,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "args": args,
        "priority": normalize_priority(priority),
        "source_bucket": source_bucket,
        "reason": reason,
        "conditions": conditions or [],
        "follow_up": follow_up or [],
        "expected_artifacts": ["raw_provider_json", "evidence_packet"],
    }


def add_task(tasks: list[dict[str, Any]], seen_task_ids: set[str], task: dict[str, Any]) -> None:
    task_id = task["id"]
    if task_id in seen_task_ids:
        return
    tasks.append(task)
    seen_task_ids.add(task_id)


def normalize_ticker(value: str) -> str:
    return value.strip().upper()


def company_label(ticker: str, company: str) -> str:
    return f"{ticker} {company}".strip()


def company_news_query(ticker: str, company: str) -> str:
    label = company_label(ticker, company)
    return f"{label} latest material company news earnings guidance regulation litigation customers stock"


def company_search_query(ticker: str, company: str) -> str:
    label = company_label(ticker, company)
    return f"{label} public company business model products competitors suppliers investor relations filings official sources"


def research_priority_query(priority: dict[str, str]) -> str:
    topic = priority.get("Topic", "").strip()
    geography = priority.get("Geography", "").strip()
    reason = priority.get("Why It Matters", "").strip()
    parts = [topic, geography, reason, "latest developments public companies investment implications"]
    return " ".join(part for part in parts if part)


def discovery_query(topic: str, geography: str) -> str:
    scope = geography.strip() or "US and Europe"
    return f"{topic} {scope} public companies listed stocks suppliers competitors high growth investment candidates"


def subject_type_for_priority(priority_type: str) -> str:
    if priority_type in {"industry", "sector"}:
        return "industry"
    if priority_type in {"theme", "technology", "geography"}:
        return "theme"
    if priority_type == "macro":
        return "macro"
    return "theme"


def is_sec_candidate(row: dict[str, str]) -> bool:
    country = row.get("country", "").strip().lower()
    exchange = row.get("exchange", "").strip().lower()
    if country in {"us", "usa", "united states", "united states of america"}:
        return True
    if exchange in {"nyse", "nasdaq", "amex", "arca", "otc"}:
        return True
    return not country and exchange in {"", "nms", "ngm"}


def is_us_market_candidate(row: dict[str, str]) -> bool:
    country = row.get("country", "").strip().lower()
    exchange = row.get("exchange", "").strip().lower()
    if country in {"us", "usa", "united states", "united states of america"}:
        return True
    return exchange in {"nyse", "nasdaq", "amex", "arca", "otc", "nms", "ngm"}


def split_cell_values(value: str) -> list[str]:
    normalized = value.replace(";", ",")
    return [item.strip().strip("`") for item in normalized.split(",") if item.strip()]


def normalize_priority(value: str) -> str:
    normalized = value.strip().lower()
    if normalized in {"low", "medium", "high", "urgent"}:
        return normalized
    return "medium"


def x_search_window_args(run_date: date, days: int) -> dict[str, str]:
    start = run_date - timedelta(days=days)
    return {"from_date": start.isoformat(), "to_date": run_date.isoformat()}


def x_search_window_args_from_run_id(run_id: str, days: int) -> dict[str, str]:
    try:
        run_date = date.fromisoformat(run_id.split("_", 1)[0])
    except ValueError:
        return {}
    return x_search_window_args(run_date, days)


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "unknown"
