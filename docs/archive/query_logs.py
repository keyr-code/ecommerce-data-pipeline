#!/usr/bin/env python3
"""
Pipeline Log Query Tool

Command-line interface for querying pipeline run logs
"""

import argparse
from pipeline_log_db import PipelineLogDB
from typing import Dict, Any
import json


def format_run_summary(run: Dict[str, Any]) -> str:
    """Format pipeline run for display"""
    return f"""
Run ID: {run['run_id']}
Status: {run['status']}
Start: {run['start_time']}
Duration: {run.get('duration_seconds', 'N/A')}s
Success Rate: {run.get('success_rate', 'N/A')}%
Files: {run.get('loaded_files', 0)}/{run.get('total_files', 0)} loaded
Log Dir: {run['log_directory']}
"""


def main():
    parser = argparse.ArgumentParser(description='Query pipeline logs')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Get specific run
    get_parser = subparsers.add_parser('get', help='Get specific pipeline run')
    get_parser.add_argument('run_id', help='Pipeline run ID')
    
    # List recent runs
    list_parser = subparsers.add_parser('list', help='List recent pipeline runs')
    list_parser.add_argument('--status', help='Filter by status')
    list_parser.add_argument('--min-success', type=float, help='Minimum success rate')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of runs to show')
    
    # Show failed validations
    failed_parser = subparsers.add_parser('failed', help='Show failed validations')
    failed_parser.add_argument('--days', type=int, default=7, help='Days to look back')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    db = PipelineLogDB()
    
    if args.command == 'get':
        run_data = db.get_pipeline_run(args.run_id)
        if not run_data:
            print(f"Run ID {args.run_id} not found")
            return
        
        print("=== PIPELINE RUN DETAILS ===")
        print(format_run_summary(run_data['pipeline_run']))
        
        print("=== DATASET VALIDATIONS ===")
        for validation in run_data['validations']:
            status = "✅ PASS" if validation['passed'] else "❌ FAIL"
            print(f"{status} {validation['filename']}: {validation['severity']} ({validation.get('success_rate', 'N/A')}%)")
        
        print("=== DATABASE OPERATIONS ===")
        for op in run_data['database_operations']:
            status = "✅ SUCCESS" if op['success'] else "❌ FAILED"
            print(f"{status} {op['operation']} - {op['filename']} ({op.get('rows_affected', 'N/A')} rows)")
    
    elif args.command == 'list':
        runs = db.query_runs(
            status=args.status,
            min_success_rate=args.min_success,
            limit=args.limit
        )
        
        print(f"=== RECENT PIPELINE RUNS ({len(runs)}) ===")
        for run in runs:
            print(format_run_summary(run))
    
    elif args.command == 'failed':
        failures = db.get_failed_validations(days=args.days)
        
        print(f"=== FAILED VALIDATIONS (Last {args.days} days) ===")
        for failure in failures:
            print(f"❌ {failure['filename']} - {failure['severity']} severity")
            print(f"   Run: {failure['run_id']} ({failure['start_time']})")
            print(f"   Logs: {failure['log_directory']}")
            print()


if __name__ == "__main__":
    main()