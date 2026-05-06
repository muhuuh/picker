from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .analysis_runner import run_analysis_tasks
from .company_news_specialist import CompanyNewsSpecialistError, build_company_news_contents_follow_up_packet, build_company_news_specialist_packet
from .config import get_config_value
from .evidence import default_packet_path, new_packet, read_packet, validate_packet, write_packet
from .financial_compare import FinancialCompareError, build_financial_compare_packet
from .financial_specialist import FinancialSpecialistError, build_financial_specialist_packet
from .human import append_human_request, classify_request
from .manifest import build_weekly_manifest, write_manifest
from .memory import (
    ITEM_MEMORY_FILES,
    VALID_MEMORY_CONFIDENCE,
    VALID_MEMORY_SCOPES,
    VALID_MEMORY_STATUSES,
    VALID_MEMORY_TYPES,
    add_memory_item,
    build_memory_context,
    deprecate_memory_item,
    format_memory_context_for_prompt,
    load_memory_state,
    memory_summary,
    validate_memory_state,
)
from .memory_llm_writer import (
    DEFAULT_MEMORY_WRITER_MODEL,
    MemoryWriterError,
    build_memory_writer_prompt,
    build_memory_writer_review,
    memory_writer_prompt_to_dict,
    memory_writer_review_to_dict,
    write_memory_writer_prompt,
)
from .memory_updates import (
    apply_memory_update_draft,
    build_memory_update_draft,
    memory_update_apply_result_to_dict,
    memory_update_draft_to_dict,
    write_memory_update_draft,
)
from .memory_reflection import (
    build_recurring_failure_report,
    build_run_reflection,
    recurring_failure_report_to_dict,
    reflection_to_dict,
    write_recurring_failure_report,
    write_run_reflection,
)
from .provider_runner import read_manifest, run_provider_tasks
from .quality_report import build_quality_report, quality_report_to_dict, write_quality_report
from .providers.exa import (
    ExaContentsOptions,
    ExaError,
    ExaSearchOptions,
    build_exa_contents_packet,
    build_exa_search_packet,
    default_exa_run_id,
    resolve_exa_api_key,
)
from .providers.alpha_vantage import (
    AlphaVantageCompanyOptions,
    AlphaVantageError,
    build_alpha_vantage_company_packet,
    default_alpha_vantage_run_id,
    resolve_alpha_vantage_api_key,
)
from .providers.fmp import FmpCompanyOptions, FmpError, build_fmp_company_packet, default_fmp_run_id, resolve_fmp_api_key
from .providers.polygon_provider import (
    PolygonCompanyOptions,
    PolygonError,
    build_polygon_company_packet,
    default_polygon_run_id,
    resolve_polygon_api_key,
)
from .providers.sec_edgar import SecEdgarError, build_sec_company_packet, default_sec_run_id, resolve_sec_user_agent
from .providers.xai_grok import (
    XaiGrokError,
    XaiXSearchOptions,
    build_xai_x_search_packet,
    default_xai_run_id,
    industry_sentiment_prompt,
    latest_news_prompt,
    resolve_xai_api_key,
    stock_sentiment_prompt,
)
from .providers.yfinance_provider import YFinanceError, build_yfinance_company_packet, default_yfinance_run_id
from .repo import load_repo_state
from .router import route_request
from .run_finalization import finalize_run, finalization_to_dict
from .run_summary import build_run_summary, run_summary_to_dict, write_run_summary
from .scheduled_runner import run_weekly_research_workflow, scheduled_run_result_to_dict
from .staleness import scan_stale_data
from .validation import validate_repo_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stock-research", description="Deterministic stock research repo tooling.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root or a path inside it.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="Print a short repo state summary.")

    memory_parser = subparsers.add_parser("memory", help="Inspect operational agent memory.")
    memory_subparsers = memory_parser.add_subparsers(dest="memory_command", required=True)

    memory_subparsers.add_parser("summary", help="Summarize operational memory files and items.")
    memory_subparsers.add_parser("validate", help="Validate operational memory files and item fields.")
    memory_context = memory_subparsers.add_parser("context", help="Print task-relevant memory context.")
    memory_context.add_argument(
        "--task",
        required=True,
        help="Task kind, e.g. financial, news, sentiment, provider, orchestration, specialist, writer, quality, all.",
    )
    memory_prompt_context = memory_subparsers.add_parser("prompt-context", help="Print prompt-ready task-relevant memory context.")
    memory_prompt_context.add_argument("--task", required=True, help="Task kind for prompt memory context.")
    memory_prompt_context.add_argument("--max-items", type=int, default=20, help="Maximum memory items to include.")
    memory_add = memory_subparsers.add_parser("add", help="Append a schema-valid operational memory item.")
    memory_add.add_argument("--memory-file", choices=ITEM_MEMORY_FILES, help="Target memory file. Defaults from --type/status.")
    memory_add.add_argument("--id", default="", help="Optional explicit memory id. Defaults to generated id.")
    memory_add.add_argument("--type", required=True, choices=sorted(VALID_MEMORY_TYPES))
    memory_add.add_argument("--scope", required=True, choices=sorted(VALID_MEMORY_SCOPES))
    memory_add.add_argument("--status", default="active", choices=sorted(VALID_MEMORY_STATUSES))
    memory_add.add_argument("--confidence", default="medium", choices=sorted(VALID_MEMORY_CONFIDENCE))
    memory_add.add_argument("--trigger-source", required=True)
    memory_add.add_argument("--lesson", required=True)
    memory_add.add_argument("--use-when", required=True)
    memory_add.add_argument("--do-not-use-when", required=True)
    memory_add.add_argument("--evidence", required=True)
    memory_add.add_argument("--owner", required=True)
    memory_add.add_argument("--next-review", required=True)
    memory_add.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_deprecate = memory_subparsers.add_parser("deprecate", help="Mark a memory item deprecated and record why.")
    memory_deprecate.add_argument("--id", required=True)
    memory_deprecate.add_argument("--reason", required=True)
    memory_deprecate.add_argument("--replacement", default="")
    memory_deprecate.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_reflect = memory_subparsers.add_parser("reflect-run", help="Build post-run memory reflection proposals.")
    memory_reflect.add_argument("--run-id", required=True)
    memory_reflect.add_argument("--write", action="store_true", help="Write memory_reflection.json and memory_reflection.md into the run directory.")
    memory_reflect.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_recurring = memory_subparsers.add_parser("recurring-failures", help="Detect recurring issues across memory_reflection.json artifacts.")
    memory_recurring.add_argument("--threshold", type=int, default=2, help="Minimum distinct runs required for a recurring pattern.")
    memory_recurring.add_argument("--write", action="store_true", help="Write recurring_failures.json and recurring_failures.md under agents/memory/.")
    memory_recurring.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_finalize = memory_subparsers.add_parser("finalize-run", help="Finalize a run by writing reflection, recurring-failure, and finalization artifacts.")
    memory_finalize.add_argument("--run-id", required=True)
    memory_finalize.add_argument("--recurring-threshold", type=int, default=2, help="Minimum distinct runs required for recurring-failure patterns.")
    memory_finalize.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_draft_updates = memory_subparsers.add_parser("draft-updates", help="Draft schema-valid memory updates from reflection proposals.")
    memory_draft_updates.add_argument("--run-id", required=True)
    memory_draft_updates.add_argument("--write", action="store_true", help="Write memory_update_drafts.json/md into the run directory.")
    memory_draft_updates.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_apply_updates = memory_subparsers.add_parser("apply-updates", help="Apply approved ready memory update drafts.")
    memory_apply_updates.add_argument("--run-id", required=True)
    memory_apply_updates.add_argument("--proposal-id", action="append", default=[], help="Proposal id to apply. Repeatable.")
    memory_apply_updates.add_argument("--all", action="store_true", help="Apply all ready draft items.")
    memory_apply_updates.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_writer_prompt = memory_subparsers.add_parser("writer-prompt", help="Build the bounded LLM memory-writer prompt for a run.")
    memory_writer_prompt.add_argument("--run-id", required=True)
    memory_writer_prompt.add_argument("--write", action="store_true", help="Write memory_writer_prompt.json/md into the run directory.")
    memory_writer_prompt.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    memory_writer_review = memory_subparsers.add_parser("writer-review", help="Run or simulate the bounded LLM memory writer over memory update drafts.")
    memory_writer_review.add_argument("--run-id", required=True)
    memory_writer_review.add_argument("--execute", action="store_true", help="Call OpenAI Responses API. Without this, run deterministic review only.")
    memory_writer_review.add_argument("--write", action="store_true", help="Write memory_writer_review.json/md into the run directory.")
    memory_writer_review.add_argument("--update-drafts", action="store_true", help="Update memory_update_drafts.json/md from writer recommendations.")
    memory_writer_review.add_argument("--model", default=DEFAULT_MEMORY_WRITER_MODEL)
    memory_writer_review.add_argument("--api-key", help="OpenAI API key. Or set OPENAI_API_KEY.")
    memory_writer_review.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    validate_parser = subparsers.add_parser("validate", help="Validate repo state and CSV schemas.")
    validate_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    stale_parser = subparsers.add_parser("stale", help="Scan stock tracking rows for stale dates.")
    stale_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")
    stale_parser.add_argument("--max-age-days", type=int, default=14)

    manifest_parser = subparsers.add_parser("manifest", help="Build a weekly run manifest.")
    manifest_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")
    manifest_parser.add_argument("--write", action="store_true", help="Write manifest under agents/runs/.")
    manifest_parser.add_argument("--out", type=Path, help="Write manifest to a custom path.")

    classify_parser = subparsers.add_parser("classify-request", help="Classify a human natural-language request.")
    classify_parser.add_argument("request")

    request_parser = subparsers.add_parser("add-request", help="Append a request to the human input queue.")
    request_parser.add_argument("request")
    request_parser.add_argument("--priority", default="medium", choices=["low", "medium", "high", "urgent"])
    request_parser.add_argument("--status", default="new")
    request_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    route_parser = subparsers.add_parser("route-request", help="Append and route a request into durable artifacts.")
    route_parser.add_argument("request")
    route_parser.add_argument("--priority", default="medium", choices=["low", "medium", "high", "urgent"])
    route_parser.add_argument("--status", default="queued_for_weekly_run")
    route_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    evidence_parser = subparsers.add_parser("evidence", help="Create or validate evidence packets.")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command", required=True)

    evidence_new = evidence_subparsers.add_parser("new", help="Create a minimal evidence packet JSON file.")
    evidence_new.add_argument("--provider", required=True)
    evidence_new.add_argument("--subject-type", required=True)
    evidence_new.add_argument("--subject-id", required=True)
    evidence_new.add_argument("--time-window", default="unspecified")
    evidence_new.add_argument("--run-id", required=True)
    evidence_new.add_argument("--today", help="Override current date as YYYY-MM-DD.")
    evidence_new.add_argument("--out", type=Path, help="Write packet to a custom path.")

    evidence_validate = evidence_subparsers.add_parser("validate", help="Validate an evidence packet JSON file.")
    evidence_validate.add_argument("path", type=Path)

    sec_parser = subparsers.add_parser("sec", help="SEC EDGAR provider tools.")
    sec_subparsers = sec_parser.add_subparsers(dest="sec_command", required=True)

    sec_company = sec_subparsers.add_parser("company", help="Fetch SEC submissions and write an evidence packet.")
    sec_company.add_argument("--ticker", required=True)
    sec_company.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-sec.")
    sec_company.add_argument("--user-agent", help="SEC-required User-Agent. Or set SEC_USER_AGENT.")
    sec_company.add_argument("--include-facts", action="store_true", help="Also fetch XBRL companyfacts.")
    sec_company.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    yfinance_parser = subparsers.add_parser("yfinance", help="yfinance market data provider tools.")
    yfinance_subparsers = yfinance_parser.add_subparsers(dest="yfinance_command", required=True)

    yfinance_company = yfinance_subparsers.add_parser("company", help="Fetch yfinance market data and write an evidence packet.")
    yfinance_company.add_argument("--ticker", required=True)
    yfinance_company.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-yfinance.")
    yfinance_company.add_argument("--period", default="5d", help="yfinance history period, e.g. 5d, 1mo, 1y.")
    yfinance_company.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    fmp_parser = subparsers.add_parser("fmp", help="Financial Modeling Prep provider tools.")
    fmp_subparsers = fmp_parser.add_subparsers(dest="fmp_command", required=True)

    fmp_company = fmp_subparsers.add_parser("company", help="Fetch FMP quote/profile/TTM metrics and write an evidence packet.")
    fmp_company.add_argument("--ticker", required=True)
    fmp_company.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-fmp.")
    fmp_company.add_argument("--include-statements", action="store_true", help="Also fetch TTM income, balance sheet, and cash flow statements.")
    fmp_company.add_argument("--api-key", help="FMP API key. Or set FMP_API_KEY.")
    fmp_company.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    polygon_parser = subparsers.add_parser("polygon", help="Polygon/Massive market-data provider tools.")
    polygon_subparsers = polygon_parser.add_subparsers(dest="polygon_command", required=True)

    polygon_company = polygon_subparsers.add_parser("company", help="Fetch ticker details and previous-day OHLC data.")
    polygon_company.add_argument("--ticker", required=True)
    polygon_company.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-polygon.")
    polygon_company.add_argument("--unadjusted", action="store_true", help="Request unadjusted previous-day OHLC data.")
    polygon_company.add_argument("--api-key", help="Polygon/Massive API key. Or set POLYGON_API_KEY.")
    polygon_company.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    alpha_parser = subparsers.add_parser("alpha-vantage", help="Alpha Vantage provider tools.")
    alpha_subparsers = alpha_parser.add_subparsers(dest="alpha_command", required=True)

    alpha_company = alpha_subparsers.add_parser("company", help="Fetch Alpha Vantage Global Quote/Overview and write an evidence packet.")
    alpha_company.add_argument("--ticker", required=True)
    alpha_company.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-alpha-vantage.")
    alpha_company.add_argument("--include-statements", action="store_true", help="Also fetch income, balance sheet, cash flow, and earnings endpoints.")
    alpha_company.add_argument("--api-key", help="Alpha Vantage API key. Or set ALPHA_VANTAGE_API_KEY.")
    alpha_company.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    financial_parser = subparsers.add_parser("financial", help="Deterministic financial evidence analysis.")
    financial_subparsers = financial_parser.add_subparsers(dest="financial_command", required=True)

    financial_compare = financial_subparsers.add_parser("compare", help="Compare financial provider evidence packets for one ticker.")
    financial_compare.add_argument("--ticker", required=True)
    financial_compare.add_argument("--run-id", required=True)
    financial_compare.add_argument("--packet", action="append", type=Path, default=[], help="Optional explicit packet path. Repeatable.")
    financial_compare.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    financial_review = financial_subparsers.add_parser("review", help="Run the deterministic financial-data specialist on a financial_compare packet.")
    financial_review.add_argument("--ticker", required=True)
    financial_review.add_argument("--run-id", required=True)
    financial_review.add_argument("--financial-compare-packet", type=Path, help="Optional explicit financial_compare packet path.")
    financial_review.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    news_parser = subparsers.add_parser("news", help="Deterministic company-news evidence analysis.")
    news_subparsers = news_parser.add_subparsers(dest="news_command", required=True)

    news_review = news_subparsers.add_parser("review", help="Run the deterministic company-news specialist on an Exa news packet.")
    news_review.add_argument("--ticker", required=True)
    news_review.add_argument("--run-id", required=True)
    news_review.add_argument("--exa-news-packet", type=Path, help="Optional explicit Exa company-news packet path.")
    news_review.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    news_contents = news_subparsers.add_parser("contents-follow-up", help="Run Exa contents extraction for high-value company-news URLs.")
    news_contents.add_argument("--ticker", required=True)
    news_contents.add_argument("--run-id", required=True)
    news_contents.add_argument("--exa-news-packet", type=Path, help="Optional explicit Exa company-news packet path.")
    news_contents.add_argument("--max-urls", type=int, default=3)
    news_contents.add_argument("--api-key", help="Exa API key. Or set EXA_API_KEY.")
    news_contents.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    exa_parser = subparsers.add_parser("exa", help="Exa search and contents provider tools.")
    exa_subparsers = exa_parser.add_subparsers(dest="exa_command", required=True)

    exa_search = exa_subparsers.add_parser("search", help="Run Exa search and write an evidence packet.")
    exa_search.add_argument("--query", required=True)
    exa_search.add_argument("--subject-type", required=True, choices=["company", "industry", "theme", "macro", "strategy", "portfolio"])
    exa_search.add_argument("--subject-id", required=True)
    exa_search.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-exa.")
    exa_search.add_argument("--mode", default="general", choices=["general", "company", "news", "industry"])
    exa_search.add_argument("--type", default="auto", choices=["auto", "fast", "instant", "deep-lite", "deep", "deep-reasoning"])
    exa_search.add_argument("--num-results", type=int, default=10)
    exa_search.add_argument("--start-published-date")
    exa_search.add_argument("--end-published-date")
    exa_search.add_argument("--include-domain", action="append", default=[])
    exa_search.add_argument("--exclude-domain", action="append", default=[])
    exa_search.add_argument("--max-age-hours", type=int)
    exa_search.add_argument("--api-key", help="Exa API key. Or set EXA_API_KEY.")
    exa_search.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    exa_contents = exa_subparsers.add_parser("contents", help="Run Exa contents extraction and write an evidence packet.")
    exa_contents.add_argument("--url", action="append", required=True, help="URL to extract. Repeat for multiple URLs.")
    exa_contents.add_argument("--subject-type", required=True, choices=["company", "industry", "theme", "macro", "strategy", "portfolio"])
    exa_contents.add_argument("--subject-id", required=True)
    exa_contents.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-exa.")
    exa_contents.add_argument("--highlights-query", default="")
    exa_contents.add_argument("--text-max-characters", type=int)
    exa_contents.add_argument("--max-age-hours", type=int)
    exa_contents.add_argument("--livecrawl-timeout", type=int, default=12000)
    exa_contents.add_argument("--api-key", help="Exa API key. Or set EXA_API_KEY.")
    exa_contents.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    xai_parser = subparsers.add_parser("xai", help="xAI Grok provider tools.")
    xai_subparsers = xai_parser.add_subparsers(dest="xai_command", required=True)

    xai_x_search = xai_subparsers.add_parser("x-search", help="Use Grok with built-in x_search and write an evidence packet.")
    xai_x_search.add_argument("--prompt", help="Full research prompt. If omitted, use --ticker/--company-name or --topic.")
    xai_x_search.add_argument("--ticker", help="Ticker for stock sentiment prompt.")
    xai_x_search.add_argument("--company-name", default="")
    xai_x_search.add_argument("--topic", help="Industry/theme/news topic for prompt generation.")
    xai_x_search.add_argument("--research-kind", default="x_sentiment", choices=["stock_sentiment", "industry_sentiment", "latest_news", "x_sentiment"])
    xai_x_search.add_argument("--subject-type", required=True, choices=["company", "industry", "theme", "macro", "strategy", "portfolio"])
    xai_x_search.add_argument("--subject-id", required=True)
    xai_x_search.add_argument("--run-id", help="Run ID for output artifacts. Defaults to YYYY-MM-DD_manual-xai.")
    xai_x_search.add_argument("--model", default="grok-4.3")
    xai_x_search.add_argument("--from-date")
    xai_x_search.add_argument("--to-date")
    xai_x_search.add_argument("--allowed-x-handle", action="append", default=[])
    xai_x_search.add_argument("--excluded-x-handle", action="append", default=[])
    xai_x_search.add_argument("--enable-image-understanding", action="store_true")
    xai_x_search.add_argument("--enable-video-understanding", action="store_true")
    xai_x_search.add_argument("--api-key", help="xAI API key. Or set XAI_API_KEY.")
    xai_x_search.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    provider_tasks = subparsers.add_parser("provider-tasks", help="Dry-run or execute provider tasks from a manifest.")
    provider_tasks.add_argument("--manifest", type=Path, required=True)
    provider_tasks.add_argument("--execute", action="store_true", help="Execute tasks. Omit for safe dry-run.")
    provider_tasks.add_argument("--provider", action="append", default=[], help="Filter provider. Repeatable.")
    provider_tasks.add_argument("--task-id", action="append", default=[], help="Filter task id. Repeatable.")
    provider_tasks.add_argument("--limit", type=int)
    provider_tasks.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    analysis_tasks = subparsers.add_parser("analysis-tasks", help="Dry-run or execute analysis tasks from a manifest.")
    analysis_tasks.add_argument("--manifest", type=Path, required=True)
    analysis_tasks.add_argument("--execute", action="store_true", help="Execute tasks. Omit for safe dry-run.")
    analysis_tasks.add_argument("--tool", action="append", default=[], help="Filter analysis tool. Repeatable.")
    analysis_tasks.add_argument("--task-id", action="append", default=[], help="Filter task id. Repeatable.")
    analysis_tasks.add_argument("--limit", type=int)
    analysis_tasks.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    run_summary_parser = subparsers.add_parser("run-summary", help="Build a deterministic run_summary.md from run artifacts.")
    run_summary_parser.add_argument("--run-id", required=True)
    run_summary_parser.add_argument("--write", action="store_true", help="Write run_summary.json and run_summary.md into the run directory.")
    run_summary_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    quality_report_parser = subparsers.add_parser("quality-report", help="Build a deterministic quality_report.md from run artifacts.")
    quality_report_parser.add_argument("--run-id", required=True)
    quality_report_parser.add_argument("--write", action="store_true", help="Write quality_report.json and quality_report.md into the run directory.")
    quality_report_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    run_weekly_parser = subparsers.add_parser("run-weekly", help="Run the deterministic weekly workflow up to the agent-framework decision boundary.")
    run_weekly_parser.add_argument("--write", action="store_true", help="Persist manifest, reports, finalization, memory-writer review, and orchestration report.")
    run_weekly_parser.add_argument("--execute-providers", action="store_true", help="Execute live provider tasks. Omit for safe dry-run.")
    run_weekly_parser.add_argument("--execute-analysis", action="store_true", help="Execute analysis tasks. Omit for safe dry-run.")
    run_weekly_parser.add_argument("--execute-memory-writer", action="store_true", help="Call OpenAI for bounded memory-writer review. Omit for deterministic review.")
    run_weekly_parser.add_argument("--no-update-memory-drafts", action="store_true", help="Do not rewrite memory_update_drafts from memory-writer recommendations.")
    run_weekly_parser.add_argument("--memory-writer-model", default=DEFAULT_MEMORY_WRITER_MODEL)
    run_weekly_parser.add_argument("--recurring-threshold", type=int, default=2)
    run_weekly_parser.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    args = parser.parse_args(argv)
    state = load_repo_state(args.root)

    if args.command == "summary":
        print_summary(state)
        return 0

    if args.command == "memory":
        memory_date = parse_cli_date(getattr(args, "today", None))
        memory_state = load_memory_state(state.root)
        if args.memory_command == "summary":
            print(json.dumps(memory_summary(memory_state), indent=2, sort_keys=True))
            return 0
        if args.memory_command == "validate":
            report = validate_memory_state(memory_state)
            for warning in report.warnings:
                print(f"WARNING: {warning}")
            for error in report.errors:
                print(f"ERROR: {error}")
            print("OK" if report.ok else "FAILED")
            return 0 if report.ok else 1
        if args.memory_command == "context":
            print(json.dumps(build_memory_context(memory_state, args.task), indent=2, sort_keys=True))
            return 0
        if args.memory_command == "prompt-context":
            print(format_memory_context_for_prompt(memory_state, args.task, args.max_items))
            return 0
        if args.memory_command == "add":
            try:
                result = add_memory_item(
                    root=state.root,
                    current_date=memory_date,
                    memory_file=args.memory_file,
                    fields={
                        "id": args.id,
                        "type": args.type,
                        "scope": args.scope,
                        "status": args.status,
                        "confidence": args.confidence,
                        "trigger/source": args.trigger_source,
                        "lesson": args.lesson,
                        "use_when": args.use_when,
                        "do_not_use_when": args.do_not_use_when,
                        "evidence": args.evidence,
                        "owner": args.owner,
                        "next_review": args.next_review,
                    },
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"action": result.action, "item_id": result.item_id, "path": str(result.path)}, indent=2))
            return 0
        if args.memory_command == "deprecate":
            try:
                result = deprecate_memory_item(
                    root=state.root,
                    item_id=args.id,
                    reason=args.reason,
                    replacement=args.replacement,
                    current_date=memory_date,
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"action": result.action, "item_id": result.item_id, "path": str(result.path)}, indent=2))
            return 0
        if args.memory_command == "reflect-run":
            try:
                reflection = build_run_reflection(state.root, args.run_id, memory_date)
                if args.write:
                    paths = write_run_reflection(state.root, reflection)
                    print(json.dumps({"paths": [str(path) for path in paths], "reflection": reflection_to_dict(reflection)}, indent=2, sort_keys=True))
                else:
                    print(json.dumps(reflection_to_dict(reflection), indent=2, sort_keys=True))
            except (FileNotFoundError, ValueError) as exc:
                print(f"ERROR: {exc}")
                return 1
            return 0
        if args.memory_command == "recurring-failures":
            try:
                report = build_recurring_failure_report(state.root, args.threshold, memory_date)
                if args.write:
                    paths = write_recurring_failure_report(state.root, report)
                    print(json.dumps({"paths": [str(path) for path in paths], "report": recurring_failure_report_to_dict(report)}, indent=2, sort_keys=True))
                else:
                    print(json.dumps(recurring_failure_report_to_dict(report), indent=2, sort_keys=True))
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 1
            return 0
        if args.memory_command == "finalize-run":
            try:
                finalization, paths = finalize_run(
                    root=state.root,
                    run_id=args.run_id,
                    current_date=memory_date,
                    recurring_threshold=args.recurring_threshold,
                )
            except (FileNotFoundError, ValueError) as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"paths": [str(path) for path in paths], "finalization": finalization_to_dict(finalization)}, indent=2, sort_keys=True))
            return 0
        if args.memory_command == "draft-updates":
            draft = build_memory_update_draft(state.root, args.run_id, memory_date)
            if args.write:
                paths = write_memory_update_draft(state.root, draft)
                print(json.dumps({"paths": [str(path) for path in paths], "draft": memory_update_draft_to_dict(draft)}, indent=2, sort_keys=True))
            else:
                print(json.dumps(memory_update_draft_to_dict(draft), indent=2, sort_keys=True))
            return 0
        if args.memory_command == "apply-updates":
            try:
                result = apply_memory_update_draft(
                    root=state.root,
                    run_id=args.run_id,
                    proposal_ids=set(args.proposal_id) if args.proposal_id else None,
                    apply_all=args.all,
                    current_date=memory_date,
                )
            except ValueError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps(memory_update_apply_result_to_dict(result), indent=2, sort_keys=True))
            return 0
        if args.memory_command == "writer-prompt":
            prompt = build_memory_writer_prompt(state.root, args.run_id, memory_date)
            if args.write:
                paths = write_memory_writer_prompt(state.root, prompt)
                print(json.dumps({"paths": [str(path) for path in paths], "prompt": memory_writer_prompt_to_dict(prompt)}, indent=2, sort_keys=True))
            else:
                print(json.dumps(memory_writer_prompt_to_dict(prompt), indent=2, sort_keys=True))
            return 0
        if args.memory_command == "writer-review":
            try:
                review, paths = build_memory_writer_review(
                    root=state.root,
                    run_id=args.run_id,
                    current_date=memory_date,
                    execute=args.execute,
                    model=args.model,
                    api_key=args.api_key or get_config_value(state.root, "OPENAI_API_KEY"),
                    update_drafts=args.update_drafts,
                    write_artifacts=args.write or args.update_drafts,
                )
            except MemoryWriterError as exc:
                print(f"ERROR: {exc}")
                return 1
            if args.write or args.update_drafts:
                print(json.dumps({"paths": [str(path) for path in paths], "review": memory_writer_review_to_dict(review)}, indent=2, sort_keys=True))
            else:
                print(json.dumps(memory_writer_review_to_dict(review), indent=2, sort_keys=True))
            return 0

    current_date = parse_cli_date(getattr(args, "today", None))

    if args.command == "validate":
        report = validate_repo_state(state, current_date)
        for warning in report.warnings:
            print(f"WARNING: {warning}")
        for error in report.errors:
            print(f"ERROR: {error}")
        print("OK" if report.ok else "FAILED")
        return 0 if report.ok else 1

    if args.command == "stale":
        stale_items = scan_stale_data(state, current_date, args.max_age_days)
        if not stale_items:
            print("No stale items found.")
            return 0
        for item in stale_items:
            print(f"{item.severity.upper()}: {item.subject}: {item.issue}")
        return 1

    if args.command == "manifest":
        manifest = build_weekly_manifest(state, current_date)
        if args.write or args.out:
            target = write_manifest(state, manifest, args.out)
            print(target)
        else:
            print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0

    if args.command == "classify-request":
        classified = classify_request(args.request)
        print(json.dumps(classified.__dict__, indent=2, sort_keys=True))
        return 0

    if args.command == "add-request":
        request_date = parse_cli_date(args.today)
        request_id = append_human_request(state.root, args.request, args.priority, args.status, request_date)
        print(request_id)
        return 0

    if args.command == "route-request":
        request_date = parse_cli_date(args.today)
        result = route_request(state.root, args.request, args.priority, args.status, request_date)
        print(json.dumps(result.__dict__, indent=2, sort_keys=True))
        return 0

    if args.command == "evidence":
        if args.evidence_command == "new":
            packet_date = parse_cli_date(args.today)
            packet = new_packet(
                provider=args.provider,
                subject_type=args.subject_type,
                subject_id=args.subject_id,
                time_window=args.time_window,
                current_date=packet_date,
            )
            report = validate_packet(packet)
            target = args.out or default_packet_path(state.root, args.run_id, packet)
            write_packet(packet, target)
            for warning in report.warnings:
                print(f"WARNING: {warning}")
            for error in report.errors:
                print(f"ERROR: {error}")
            print(target)
            return 0 if report.ok else 1
        if args.evidence_command == "validate":
            packet = read_packet(args.path)
            report = validate_packet(packet)
            for warning in report.warnings:
                print(f"WARNING: {warning}")
            for error in report.errors:
                print(f"ERROR: {error}")
            print("OK" if report.ok else "FAILED")
            return 0 if report.ok else 1

    if args.command == "sec":
        if args.sec_command == "company":
            request_date = parse_cli_date(args.today)
            run_id = args.run_id or default_sec_run_id(request_date)
            try:
                user_agent = resolve_sec_user_agent(
                    args.user_agent
                    or get_config_value(state.root, "SEC_USER_AGENT")
                    or get_config_value(state.root, "STOCK_RESEARCH_SEC_USER_AGENT")
                )
                packet, paths = build_sec_company_packet(
                    ticker=args.ticker,
                    user_agent=user_agent,
                    run_id=run_id,
                    root=state.root,
                    include_facts=args.include_facts,
                    current_date=request_date,
                )
            except SecEdgarError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0

    if args.command == "yfinance":
        if args.yfinance_command == "company":
            request_date = parse_cli_date(args.today)
            run_id = args.run_id or default_yfinance_run_id(request_date)
            try:
                packet, paths = build_yfinance_company_packet(
                    ticker=args.ticker,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                    period=args.period,
                )
            except YFinanceError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0

    if args.command == "fmp":
        if args.fmp_command == "company":
            request_date = parse_cli_date(args.today)
            run_id = args.run_id or default_fmp_run_id(request_date)
            try:
                api_key = resolve_fmp_api_key(args.api_key or get_config_value(state.root, "FMP_API_KEY") or get_config_value(state.root, "FINANCIAL_MODELING_PREP_API_KEY"))
                packet, paths = build_fmp_company_packet(
                    options=FmpCompanyOptions(ticker=args.ticker, include_statements=args.include_statements),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            except FmpError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0

    if args.command == "polygon":
        if args.polygon_command == "company":
            request_date = parse_cli_date(args.today)
            run_id = args.run_id or default_polygon_run_id(request_date)
            try:
                api_key = resolve_polygon_api_key(args.api_key or get_config_value(state.root, "POLYGON_API_KEY") or get_config_value(state.root, "MASSIVE_API_KEY"))
                packet, paths = build_polygon_company_packet(
                    options=PolygonCompanyOptions(ticker=args.ticker, adjusted=not args.unadjusted),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            except PolygonError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0

    if args.command == "alpha-vantage":
        if args.alpha_command == "company":
            request_date = parse_cli_date(args.today)
            run_id = args.run_id or default_alpha_vantage_run_id(request_date)
            try:
                api_key = resolve_alpha_vantage_api_key(args.api_key or get_config_value(state.root, "ALPHA_VANTAGE_API_KEY"))
                packet, paths = build_alpha_vantage_company_packet(
                    options=AlphaVantageCompanyOptions(ticker=args.ticker, include_statements=args.include_statements),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            except AlphaVantageError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0

    if args.command == "financial":
        if args.financial_command == "compare":
            request_date = parse_cli_date(args.today)
            try:
                packet, paths = build_financial_compare_packet(
                    ticker=args.ticker,
                    run_id=args.run_id,
                    root=state.root,
                    current_date=request_date,
                    packet_paths=args.packet or None,
                )
            except FinancialCompareError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
            return 0
        if args.financial_command == "review":
            request_date = parse_cli_date(args.today)
            try:
                result = build_financial_specialist_packet(
                    ticker=args.ticker,
                    run_id=args.run_id,
                    root=state.root,
                    current_date=request_date,
                    financial_compare_packet_path=args.financial_compare_packet,
                )
            except FinancialSpecialistError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(
                json.dumps(
                    {
                        "packet_id": result.packet.packet_id,
                        "status": result.review["status"],
                        "paths": [str(path) for path in result.paths],
                    },
                    indent=2,
                )
            )
            return 0

    if args.command == "news":
        if args.news_command == "review":
            request_date = parse_cli_date(args.today)
            try:
                result = build_company_news_specialist_packet(
                    ticker=args.ticker,
                    run_id=args.run_id,
                    root=state.root,
                    current_date=request_date,
                    exa_news_packet_path=args.exa_news_packet,
                )
            except CompanyNewsSpecialistError as exc:
                print(f"ERROR: {exc}")
                return 1
            print(
                json.dumps(
                    {
                        "packet_id": result.packet.packet_id,
                        "status": result.review["status"],
                        "paths": [str(path) for path in result.paths],
                    },
                    indent=2,
                )
            )
            return 0
        if args.news_command == "contents-follow-up":
            request_date = parse_cli_date(args.today)
            try:
                api_key = resolve_exa_api_key(args.api_key or get_config_value(state.root, "EXA_API_KEY"))
                result = build_company_news_contents_follow_up_packet(
                    ticker=args.ticker,
                    run_id=args.run_id,
                    root=state.root,
                    api_key=api_key,
                    current_date=request_date,
                    exa_news_packet_path=args.exa_news_packet,
                    max_urls=args.max_urls,
                )
            except (CompanyNewsSpecialistError, ExaError) as exc:
                print(f"ERROR: {exc}")
                return 1
            print(
                json.dumps(
                    {
                        "packet_id": result.packet.packet_id,
                        "urls": result.urls,
                        "paths": [str(path) for path in result.paths],
                    },
                    indent=2,
                )
            )
            return 0

    if args.command == "exa":
        request_date = parse_cli_date(args.today)
        run_id = args.run_id or default_exa_run_id(request_date)
        try:
            api_key = resolve_exa_api_key(args.api_key or get_config_value(state.root, "EXA_API_KEY"))
            if args.exa_command == "search":
                packet, paths = build_exa_search_packet(
                    options=ExaSearchOptions(
                        query=args.query,
                        subject_type=args.subject_type,
                        subject_id=args.subject_id,
                        search_mode=args.mode,
                        search_type=args.type,
                        num_results=args.num_results,
                        start_published_date=args.start_published_date or "",
                        end_published_date=args.end_published_date or "",
                        include_domains=tuple(args.include_domain),
                        exclude_domains=tuple(args.exclude_domain),
                        max_age_hours=args.max_age_hours,
                    ),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            elif args.exa_command == "contents":
                packet, paths = build_exa_contents_packet(
                    options=ExaContentsOptions(
                        urls=tuple(args.url),
                        subject_type=args.subject_type,
                        subject_id=args.subject_id,
                        highlights_query=args.highlights_query,
                        text_max_characters=args.text_max_characters,
                        max_age_hours=args.max_age_hours,
                        livecrawl_timeout=args.livecrawl_timeout,
                    ),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            else:
                return 1
        except ExaError as exc:
            print(f"ERROR: {exc}")
            return 1
        print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
        return 0

    if args.command == "xai":
        request_date = parse_cli_date(args.today)
        run_id = args.run_id or default_xai_run_id(request_date)
        try:
            api_key = resolve_xai_api_key(args.api_key or get_config_value(state.root, "XAI_API_KEY"))
            prompt = resolve_xai_prompt(
                prompt=args.prompt,
                ticker=getattr(args, "ticker", None),
                company_name=getattr(args, "company_name", ""),
                topic=getattr(args, "topic", None),
                research_kind=args.research_kind,
            )
            if args.xai_command == "x-search":
                packet, paths = build_xai_x_search_packet(
                    options=XaiXSearchOptions(
                        prompt=prompt,
                        subject_type=args.subject_type,
                        subject_id=args.subject_id,
                        research_kind=args.research_kind,
                        model=args.model,
                        from_date=args.from_date or "",
                        to_date=args.to_date or "",
                        allowed_x_handles=tuple(args.allowed_x_handle),
                        excluded_x_handles=tuple(args.excluded_x_handle),
                        enable_image_understanding=args.enable_image_understanding,
                        enable_video_understanding=args.enable_video_understanding,
                    ),
                    api_key=api_key,
                    run_id=run_id,
                    root=state.root,
                    current_date=request_date,
                )
            else:
                return 1
        except XaiGrokError as exc:
            print(f"ERROR: {exc}")
            return 1
        print(json.dumps({"packet_id": packet.packet_id, "paths": [str(path) for path in paths]}, indent=2))
        return 0

    if args.command == "provider-tasks":
        request_date = parse_cli_date(args.today)
        manifest = read_manifest(args.manifest)
        result = run_provider_tasks(
            root=state.root,
            manifest=manifest,
            execute=args.execute,
            providers=set(args.provider) if args.provider else None,
            task_ids=set(args.task_id) if args.task_id else None,
            limit=args.limit,
            current_date=request_date,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not result["errors"] else 1

    if args.command == "analysis-tasks":
        request_date = parse_cli_date(args.today)
        manifest = read_manifest(args.manifest)
        result = run_analysis_tasks(
            root=state.root,
            manifest=manifest,
            execute=args.execute,
            tools=set(args.tool) if args.tool else None,
            task_ids=set(args.task_id) if args.task_id else None,
            limit=args.limit,
            current_date=request_date,
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if not result["errors"] and not result["skipped"] else 1

    if args.command == "run-summary":
        request_date = parse_cli_date(args.today)
        try:
            summary = build_run_summary(state.root, args.run_id, request_date)
            if args.write:
                paths = write_run_summary(state.root, summary)
                print(json.dumps({"paths": [str(path) for path in paths], "summary": run_summary_to_dict(summary)}, indent=2, sort_keys=True))
            else:
                print(json.dumps(run_summary_to_dict(summary), indent=2, sort_keys=True))
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 1
        return 0

    if args.command == "quality-report":
        request_date = parse_cli_date(args.today)
        try:
            report = build_quality_report(state.root, args.run_id, request_date)
            if args.write:
                paths = write_quality_report(state.root, report)
                print(json.dumps({"paths": [str(path) for path in paths], "report": quality_report_to_dict(report)}, indent=2, sort_keys=True))
            else:
                print(json.dumps(quality_report_to_dict(report), indent=2, sort_keys=True))
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}")
            return 1
        return 0

    if args.command == "run-weekly":
        request_date = parse_cli_date(args.today)
        try:
            result, paths = run_weekly_research_workflow(
                root=state.root,
                current_date=request_date,
                write=args.write,
                execute_providers=args.execute_providers,
                execute_analysis=args.execute_analysis,
                execute_memory_writer=args.execute_memory_writer,
                update_memory_drafts=not args.no_update_memory_drafts,
                recurring_threshold=args.recurring_threshold,
                memory_writer_model=args.memory_writer_model,
            )
        except Exception as exc:
            print(f"ERROR: {exc}")
            return 1
        payload = scheduled_run_result_to_dict(result)
        if args.write:
            payload = {**payload, "written_paths": [str(path) for path in paths]}
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0 if result.status in {"complete", "dry_run"} else 1

    return 1


def print_summary(state) -> None:
    print(f"Repo root: {state.root}")
    for name, table in state.stock_tables.items():
        non_empty_rows = len([row for row in table.rows if any(value.strip() for value in row.values())])
        print(f"{name}: {non_empty_rows} stock row(s)")
    print(f"human_requests: {len(state.human_requests)} row(s)")
    print(f"research_priorities: {len(state.research_priorities)} row(s)")
    print(f"human_review_items: {len(state.human_review_items)} row(s)")


def parse_cli_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def resolve_xai_prompt(
    prompt: str | None,
    ticker: str | None,
    company_name: str,
    topic: str | None,
    research_kind: str,
) -> str:
    if prompt:
        return prompt
    if ticker:
        return stock_sentiment_prompt(ticker, company_name)
    if topic and research_kind == "latest_news":
        return latest_news_prompt(topic)
    if topic:
        return industry_sentiment_prompt(topic)
    raise XaiGrokError("Provide --prompt, --ticker, or --topic for xAI Grok x-search.")
