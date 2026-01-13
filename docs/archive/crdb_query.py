#!/usr/bin/env python3
"""
CockroachDB Log Query CLI

Command-line interface for querying pipeline logs stored in CockroachDB
"""

import argparse
from cockroach_log_ingester import CockroachLogDB, PipelineLogIngester
import json
from pathlib import Path


def setup_cockroach():
    """Setup CockroachDB for pipeline logs"""
    print("Setting up CockroachDB for pipeline logs...")
    
    # Initialize database
    db = CockroachLogDB()
    print("✅ Database schema created")
    
    # Ingest existing logs
    log_dir = Path("pipeline_logs")
    if log_dir.exists():
        ingester = PipelineLogIngester(db)
        ingester.ingest_all_runs(str(log_dir))
        print("✅ Existing logs ingested")
    
    print("🚀 CockroachDB setup complete!")


def query_run(run_id: str):
    """Query logs for specific run"""
    db = CockroachLogDB()
    logs = db.query_run_logs(run_id)
    
    if not logs:
        print(f"No logs found for run ID: {run_id}")
        return
    
    print(f"\n=== LOGS FOR RUN {run_id} ===")
    for log in logs:
        print(f"\n[{log['timestamp']}] {log['log_type'].upper()}")
        if log['filename']:
            print(f"File: {log['filename']}")
        
        if log['content']:
            content = json.loads(log['content']) if isinstance(log['content'], str) else log['content']
            if log['log_type'] == 'validation_report':
                print(f"Passed: {content.get('passed')}")
                print(f"Severity: {content.get('severity')}")
                print(f"Success Rate: {content.get('success_rate')}%")
            elif log['log_type'] == 'application_log':
                print(f"Level: {content.get('level')}")
                print(f"Message: {content.get('message')}")
        
        print("-" * 50)


def search_logs(term: str, days: int = 7):
    """Search logs by term"""
    db = CockroachLogDB()
    results = db.search_logs(term, days)
    
    print(f"\n=== SEARCH RESULTS FOR '{term}' (Last {days} days) ===")
    for result in results:
        print(f"\n[{result['timestamp']}] {result['run_id']}")
        print(f"Type: {result['log_type']}")
        if result['filename']:
            print(f"File: {result['filename']}")
        
        # Show matching line
        lines = result['raw_text'].split('\n')
        for line in lines:
            if term.lower() in line.lower():
                print(f"Match: {line.strip()}")
                break
        
        print("-" * 30)


def main():
    parser = argparse.ArgumentParser(description='CockroachDB Pipeline Log Query Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup command
    subparsers.add_parser('setup', help='Setup CockroachDB and ingest existing logs')
    
    # Query run command
    run_parser = subparsers.add_parser('run', help='Query logs for specific run')
    run_parser.add_argument('run_id', help='Pipeline run ID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search logs by term')
    search_parser.add_argument('term', help='Search term')
    search_parser.add_argument('--days', type=int, default=7, help='Days to search back')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest logs from directory')
    ingest_parser.add_argument('directory', help='Log directory path')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'setup':
            setup_cockroach()
        
        elif args.command == 'run':
            query_run(args.run_id)
        
        elif args.command == 'search':
            search_logs(args.term, args.days)
        
        elif args.command == 'ingest':
            db = CockroachLogDB()
            ingester = PipelineLogIngester(db)
            ingester.ingest_all_runs(args.directory)
            print(f"✅ Ingested logs from {args.directory}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()