"""
Command-line interface for the Maintenance Analysis Agent.
"""

import sys
import logging
import argparse
from pathlib import Path

from .graph import build_graph
from .state import AnalysisState


def setup_logging(level: str = "INFO"):
    """Configure logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Local Manufacturing Predictive Maintenance Analysis Agent'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze maintenance data')
    analyze_parser.add_argument(
        'data_dir',
        type=str,
        help='Directory containing data files (CSV, JSON, TXT)'
    )
    analyze_parser.add_argument(
        '--output-dir',
        type=str,
        default='outputs',
        help='Output directory for reports (default: outputs)'
    )
    analyze_parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    # Validate input directory
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory not found: {args.data_dir}", file=sys.stderr)
        return 1

    if args.command == 'analyze':
        return analyze_command(data_dir, args.output_dir, logger)

    return 0


def analyze_command(data_dir: Path, output_dir: str, logger) -> int:
    """Execute the analyze command."""
    logger.info(f"Starting analysis of {data_dir}")
    logger.info(f"Output will be written to {output_dir}")

    try:
        # Build and execute workflow
        graph = build_graph()

        # Create initial state
        initial_state: AnalysisState = {
            'input_paths': [str(data_dir)],
            'discovered_files': [],
            'ingestion_errors': [],
            'raw_records': [],
            'parsed_records': [],
            'normalized_telemetry': [],
            'normalized_maintenance': [],
            'machine_inventory': [],
            'failures': [],
            'anomalies': [],
            'patterns': [],
            'candidate_factors': [],
            'dashboard_correlation': {},
            'maintenance_analysis': {},
            'metrics': {},
            'data_quality_issues': [],
            'report': {},
            'errors': [],
            'fatal_error': None,
        }

        # Execute workflow
        logger.info("Executing analysis workflow...")
        result = graph.invoke(initial_state)

        # Check for errors
        if result.get('fatal_error'):
            logger.error(f"Fatal error: {result['fatal_error']}")
            return 1

        # Report completion
        logger.info("✅ Analysis complete!")
        logger.info(f"Report generated at outputs/report.md")
        logger.info(f"Analysis data saved at outputs/analysis.json")

        # Print summary
        metrics = result.get('metrics', {})
        print("\n" + "="*60)
        print("ANALYSIS SUMMARY")
        print("="*60)
        print(f"Machines Analyzed: {metrics.get('total_machines', 'N/A')}")
        print(f"Machines with Telemetry: {metrics.get('machines_with_telemetry', 'N/A')}")
        print(f"Failures Identified: {len(result.get('failures', []))}")
        print(f"Total Downtime: {metrics.get('total_downtime_hours', 0):.1f} hours")
        print(f"Candidate Factors: {len(result.get('candidate_factors', []))}")
        print("="*60 + "\n")

        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
