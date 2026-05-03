from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .config import get_config_value
from .evidence import default_packet_path, new_packet, read_packet, validate_packet, write_packet
from .human import append_human_request, classify_request
from .manifest import build_weekly_manifest, write_manifest
from .provider_runner import read_manifest, run_provider_tasks
from .providers.exa import (
    ExaContentsOptions,
    ExaError,
    ExaSearchOptions,
    build_exa_contents_packet,
    build_exa_search_packet,
    default_exa_run_id,
    resolve_exa_api_key,
)
from .providers.sec_edgar import SecEdgarError, build_sec_company_packet, default_sec_run_id, resolve_sec_user_agent
from .providers.yfinance_provider import YFinanceError, build_yfinance_company_packet, default_yfinance_run_id
from .repo import load_repo_state
from .router import route_request
from .staleness import scan_stale_data
from .validation import validate_repo_state


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="stock-research", description="Deterministic stock research repo tooling.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root or a path inside it.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("summary", help="Print a short repo state summary.")

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

    provider_tasks = subparsers.add_parser("provider-tasks", help="Dry-run or execute provider tasks from a manifest.")
    provider_tasks.add_argument("--manifest", type=Path, required=True)
    provider_tasks.add_argument("--execute", action="store_true", help="Execute tasks. Omit for safe dry-run.")
    provider_tasks.add_argument("--provider", action="append", default=[], help="Filter provider. Repeatable.")
    provider_tasks.add_argument("--task-id", action="append", default=[], help="Filter task id. Repeatable.")
    provider_tasks.add_argument("--limit", type=int)
    provider_tasks.add_argument("--today", help="Override current date as YYYY-MM-DD.")

    args = parser.parse_args(argv)
    state = load_repo_state(args.root)

    if args.command == "summary":
        print_summary(state)
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
