#!/usr/bin/env python3
"""
MongoDB Pipeline Log Query CLI
"""

import argparse
from mongo_log_ingester import MongoLogDB, PipelineLogIngester
from datetime import datetime
import json


def format_log_entry(log: dict) -> str:
    """Format log entry for display"""
    timestamp = log.get('timestamp', 'Unknown')
    log_type = log.get('log_type', 'Unknown')
    
    output = f"\n[{timestamp}] {log_type.upper()}"
    
    if log.get('filename'):
        output += f" - {log['filename']}"
    
    content = log.get('content', {})
    if log_type == 'validation_report':
        output += f"\n  Passed: {content.get('passed')}"
        output += f"\n  Severity: {content.get('severity')}"
        output += f"\n  Success Rate: {content.get('success_rate')}%"
    elif log_type == 'application_log':
        output += f"\n  Level: {content.get('level')}"
        output += f"\n  Message: {content.get('message')}"
    elif log_type == 'database_operation':
        output += f"\n  Success: {content.get('success')}"
        output += f"\n  Operation: {content.get('operation')}"
        output += f"\n  Rows: {content.get('rows_affected')}"
    elif log_type == 'pipeline_summary':
        output += f"\n  Duration: {content.get('duration_seconds', 'N/A')} seconds"
        output += f"\n  Success Rate: {content.get('success_rate', 'N/A')}%"
        output += f"\n  Total Files: {content.get('total_files', 'N/A')}"
        output += f"\n  Loaded Files: {content.get('loaded_files', 'N/A')}"
        # Show the full summary in raw_text
        raw_text = log.get('raw_text', '')
        if raw_text:
            output += f"\n\n{raw_text}"
    
    return output


def setup_mongodb():
    """Setup MongoDB and ingest existing logs"""
    print("Setting up MongoDB for pipeline logs...")
    
    db = MongoLogDB()
    print("✅ MongoDB connection established")
    
    ingester = PipelineLogIngester(db)
    ingester.ingest_all_runs("pipeline_logs")
    
    print("🚀 MongoDB setup complete!")


def query_run(run_id: str):
    """Query logs for specific run"""
    db = MongoLogDB()
    logs = db.get_run_logs(run_id)
    
    if not logs:
        print(f"No logs found for run ID: {run_id}")
        return
    
    print(f"\n=== LOGS FOR RUN {run_id} ===")
    for log in logs:
        print(format_log_entry(log))
        print("-" * 50)


def search_logs(term: str, days: int = 7):
    """Search logs by term"""
    db = MongoLogDB()
    results = db.search_logs(term, days)
    
    print(f"\n=== SEARCH RESULTS FOR '{term}' (Last {days} days) ===")
    print(f"Found {len(results)} matching logs")
    
    for result in results[:20]:  # Limit to first 20 results
        print(format_log_entry(result))
        print("-" * 30)


def show_failed_validations(days: int = 7):
    """Show failed validations"""
    db = MongoLogDB()
    failures = db.get_failed_validations(days)
    
    print(f"\n=== FAILED VALIDATIONS (Last {days} days) ===")
    print(f"Found {len(failures)} failed validations")
    
    for failure in failures:
        content = failure.get('content', {})
        print(f"\n❌ {failure.get('filename')} - {content.get('severity')} severity")
        print(f"   Run: {failure['run_id']}")
        print(f"   Time: {failure['timestamp']}")
        print(f"   Success Rate: {content.get('success_rate')}%")


def show_stats(days: int = 30):
    """Show pipeline statistics"""
    db = MongoLogDB()
    stats = db.get_pipeline_stats(days)
    
    print(f"\n=== PIPELINE STATISTICS (Last {days} days) ===")
    if stats:
        print(f"Total Runs: {stats.get('total_runs', 0)}")
        print(f"Failed Runs: {stats.get('failed_runs', 0)}")
        print(f"Average Success Rate: {stats.get('avg_success_rate', 0):.1f}%")
        print(f"Average Duration: {stats.get('avg_duration', 0):.1f} seconds")
    else:
        print("No statistics available")


def list_recent_runs(limit: int = 10):
    """List recent pipeline runs"""
    db = MongoLogDB()
    
    # Get recent runs from pipeline_runs collection
    runs = list(db.runs.find().sort("start_time", -1).limit(limit))
    
    print(f"\n=== RECENT PIPELINE RUNS (Last {limit}) ===")
    for run in runs:
        print(f"\nRun ID: {run['run_id']}")
        print(f"Success Rate: {run.get('success_rate', 'N/A')}%")
        print(f"Duration: {run.get('duration_seconds', 'N/A')} seconds")
        print(f"Files: {run.get('loaded_files', 0)}/{run.get('total_files', 0)}")
        print(f"Directory: {run.get('log_directory', 'N/A')}")


def main():
    parser = argparse.ArgumentParser(description='MongoDB Pipeline Log Query Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Setup MongoDB and ingest existing logs')
    
    # Query run command
    run_parser = subparsers.add_parser('run', help='Query logs for specific run')
    run_parser.add_argument('run_id', help='Pipeline run ID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs by term')
    search_parser.add_argument('term', help='Search term')
    search_parser.add_argument('--days', type=int, default=7, help='Days to search back')
    
    # Failed validations command
    failed_parser = subparsers.add_parser('failed', help='Show failed validations')
    failed_parser.add_argument('--days', type=int, default=7, help='Days to look back')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show pipeline statistics')
    stats_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    
    # List runs command
    list_parser = subparsers.add_parser('list', help='List recent pipeline runs')
    list_parser.add_argument('--limit', type=int, default=10, help='Number of runs to show')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest logs from directory')
    ingest_parser.add_argument('directory', help='Log directory path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'setup':
            setup_mongodb()
        
        elif args.command == 'run':
            query_run(args.run_id)
        
        elif args.command == 'search':
            search_logs(args.term, args.days)
        
        elif args.command == 'failed':
            show_failed_validations(args.days)
        
        elif args.command == 'stats':
            show_stats(args.days)
        
        elif args.command == 'list':
            list_recent_runs(args.limit)
        
        elif args.command == 'ingest':
            db = MongoLogDB()
            ingester = PipelineLogIngester(db)
            ingester.ingest_all_runs(args.directory)
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()