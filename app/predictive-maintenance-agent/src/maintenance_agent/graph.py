"""
LangGraph workflow for the Maintenance Analysis Agent.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

try:
    from langgraph.graph import StateGraph
except ImportError:
    StateGraph = None

from .core import discover_files, ParserRegistry, normalize_record
from .state import AnalysisState
from .config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


# ============================================================================
# GRAPH NODES
# ============================================================================

def ingest_files_node(state: AnalysisState) -> AnalysisState:
    """Discover and categorize files."""
    logger.info("=== INGEST FILES ===")
    input_paths = state.get('input_paths', [])

    if not input_paths:
        state['fatal_error'] = "No input paths provided"
        return state

    discovered = discover_files(input_paths)
    state['discovered_files'] = discovered
    logger.info(f"Discovered {len(discovered)} files")

    return state


def detect_format_node(state: AnalysisState) -> AnalysisState:
    """Detect file format for each discovered file."""
    logger.info("=== DETECT FORMAT ===")
    files = state.get('discovered_files', [])

    registry = ParserRegistry()
    for file_dict in files:
        file_path = file_dict['path']
        parser = registry.get_parser(file_path)
        file_dict['parser'] = type(parser).__name__ if parser else 'UNKNOWN'
        file_dict['supported'] = parser is not None

    logger.info(f"Formatted {len(files)} files")
    return state


def parse_data_node(state: AnalysisState) -> AnalysisState:
    """Parse each file using appropriate parser."""
    logger.info("=== PARSE DATA ===")
    files = state.get('discovered_files', [])
    raw_records = []
    ingestion_errors = []

    registry = ParserRegistry()
    for file_dict in files:
        if not file_dict.get('supported'):
            continue

        file_path = file_dict['path']
        records, error = registry.parse_file(file_path)

        if error:
            ingestion_errors.append(f"{file_path}: {error}")
        else:
            for record in records:
                record['_source_file'] = file_path
            raw_records.extend(records)

    state['raw_records'] = raw_records
    state['ingestion_errors'] = ingestion_errors
    logger.info(f"Parsed {len(raw_records)} total records from all files")

    return state


def normalize_data_node(state: AnalysisState) -> AnalysisState:
    """Normalize parsed records to common schema."""
    logger.info("=== NORMALIZE DATA ===")
    raw_records = state.get('raw_records', [])

    normalized_telemetry = []
    normalized_maintenance = []
    machine_inventory = {}

    for record in raw_records:
        # Detect record type
        if any(k in record for k in ['spindle_temp', 'vibration_mm_s', 'motor_current_a', 'hydPressure_bar', 'cycleDuration_s']):
            # Telemetry
            vendor = 'vendor_b' if 'recordedAt' in record else 'vendor_a'
            normalized = normalize_record(record, vendor, 'telemetry')
            normalized_telemetry.append(normalized)

            # Track machine
            if normalized.get('machine_id'):
                machine_inventory[normalized['machine_id']] = {
                    'machine_id': normalized['machine_id'],
                    'vendor': vendor,
                    'last_seen': normalized.get('timestamp'),
                    'telemetry_available': True
                }

        elif any(k in record for k in ['downtime_hours', 'description', 'parts_replaced', 'timestamp']):
            # Maintenance record
            normalized = normalize_record(record, 'vendor_a', 'maintenance')
            normalized_maintenance.append(normalized)

            if normalized.get('machine_id'):
                if normalized['machine_id'] not in machine_inventory:
                    machine_inventory[normalized['machine_id']] = {}
                machine_inventory[normalized['machine_id']]['last_maintenance'] = normalized.get('timestamp')

    state['normalized_telemetry'] = normalized_telemetry
    state['normalized_maintenance'] = normalized_maintenance
    state['machine_inventory'] = list(machine_inventory.values())

    logger.info(f"Normalized {len(normalized_telemetry)} telemetry + {len(normalized_maintenance)} maintenance records")

    return state


def validate_data_node(state: AnalysisState) -> AnalysisState:
    """Validate data quality."""
    logger.info("=== VALIDATE DATA ===")
    telemetry = state.get('normalized_telemetry', [])
    maintenance = state.get('normalized_maintenance', [])
    quality_issues = []

    # Check completeness
    missing_timestamps = sum(1 for r in telemetry if not r.get('timestamp'))
    if missing_timestamps:
        quality_issues.append(f"WARNING: {missing_timestamps} telemetry records missing timestamps")

    # Check machines
    machines = {r.get('machine_id') for r in telemetry if r.get('machine_id')}
    logger.info(f"Machines with telemetry: {len(machines)}")

    state['data_quality_issues'] = quality_issues
    return state


def analyze_telemetry_node(state: AnalysisState) -> AnalysisState:
    """Analyze telemetry for anomalies."""
    logger.info("=== ANALYZE TELEMETRY ===")
    from .core import detect_threshold_violations

    telemetry = state.get('normalized_telemetry', [])
    config = {
        'temp_alert': DEFAULT_CONFIG.temperature_alert_celsius,
        'temp_critical': DEFAULT_CONFIG.temperature_critical_celsius,
        'pressure_alert': DEFAULT_CONFIG.pressure_alert_bar,
        'pressure_critical': DEFAULT_CONFIG.pressure_critical_bar,
        'vib_alert': DEFAULT_CONFIG.vibration_alert_mm_s,
        'vib_critical': DEFAULT_CONFIG.vibration_critical_mm_s,
    }

    anomalies = detect_threshold_violations(telemetry, config)
    state['anomalies'] = anomalies
    logger.info(f"Found {len(anomalies)} anomalies")

    return state


def analyze_maintenance_node(state: AnalysisState) -> AnalysisState:
    """Analyze maintenance patterns."""
    logger.info("=== ANALYZE MAINTENANCE ===")
    maintenance = state.get('normalized_maintenance', [])

    # Count maintenance by machine
    machine_maintenance = {}
    for event in maintenance:
        machine_id = event.get('machine_id')
        if machine_id:
            machine_maintenance[machine_id] = machine_maintenance.get(machine_id, 0) + 1

    state['maintenance_analysis'] = {
        'total_events': len(maintenance),
        'by_machine': machine_maintenance
    }
    logger.info(f"Analyzed {len(maintenance)} maintenance events")

    return state


def correlate_events_node(state: AnalysisState) -> AnalysisState:
    """Correlate telemetry, maintenance, and failures."""
    logger.info("=== CORRELATE EVENTS ===")

    # Identify failures as RED dashboard states or clusters of anomalies
    telemetry = state.get('normalized_telemetry', [])
    anomalies = state.get('anomalies', [])

    failures = []
    failure_id = 0

    # Find RED dashboard states as failure indicators
    red_states = [t for t in telemetry if t.get('dashboard_status') == 'RED']
    for red_state in red_states[:20]:  # Limit to first 20 for sample data
        failure_id += 1
        failures.append({
            'failure_id': f"FAIL-{failure_id}",
            'machine_id': red_state.get('machine_id'),
            'timestamp': red_state.get('timestamp'),
            'indicator': 'RED_dashboard_state'
        })

    # Also count any critical anomalies as failures
    for anomaly in anomalies:
        if anomaly['severity'] == 'critical':
            failure_id += 1
            failures.append({
                'failure_id': f"FAIL-{failure_id}",
                'machine_id': anomaly['machine_id'],
                'timestamp': anomaly['timestamp'],
                'indicator': 'critical_anomaly',
                'anomaly': anomaly
            })

    state['failures'] = failures
    logger.info(f"Identified {len(failures)} potential failures from RED states and critical anomalies")

    return state


def identify_patterns_node(state: AnalysisState) -> AnalysisState:
    """Identify candidate pre-failure patterns."""
    logger.info("=== IDENTIFY PATTERNS ===")

    failures = state.get('failures', [])
    anomalies = state.get('anomalies', [])

    if not failures:
        state['candidate_factors'] = []
        return state

    # Group anomalies by field
    anomalies_by_field = {}
    for anom in anomalies:
        field = anom['field']
        if field not in anomalies_by_field:
            anomalies_by_field[field] = []
        anomalies_by_field[field].append(anom)

    candidates = []
    for field_name, field_anomalies in anomalies_by_field.items():
        frequency = len(field_anomalies) / max(1, len(failures)) if failures else 0
        confidence = "Strong" if frequency > 0.6 else ("Moderate" if frequency > 0.3 else "Weak")

        candidates.append({
            'factor_id': f"FAC-{field_name}",
            'factor_name': f"Anomaly in {field_name}",
            'field_name': field_name,
            'observed_in_failures': len(field_anomalies),
            'total_failures': len(failures),
            'frequency_percent': frequency * 100,
            'confidence_level': confidence,
            'evidence': field_anomalies[:3]  # First 3 examples
        })

    state['candidate_factors'] = sorted(candidates, key=lambda x: x['frequency_percent'], reverse=True)
    logger.info(f"Identified {len(candidates)} candidate factors")

    return state


def calculate_metrics_node(state: AnalysisState) -> AnalysisState:
    """Calculate summary metrics."""
    logger.info("=== CALCULATE METRICS ===")
    from .core import compute_metrics

    failures = state.get('failures', [])
    maintenance = state.get('normalized_maintenance', [])

    metrics = compute_metrics(failures, maintenance)

    # Add more metrics
    machines = state.get('machine_inventory', [])
    metrics['total_machines'] = len(machines)
    metrics['machines_with_telemetry'] = len([m for m in machines if m.get('telemetry_available', False)])
    metrics['machines_without_telemetry'] = metrics['total_machines'] - metrics['machines_with_telemetry']

    state['metrics'] = metrics
    logger.info(f"Metrics: {metrics['incident_count']} incidents, {metrics['total_downtime_hours']:.1f} hours downtime")

    return state


def generate_report_node(state: AnalysisState) -> AnalysisState:
    """Generate analysis report."""
    logger.info("=== GENERATE REPORT ===")

    report = {
        'generated_at': datetime.now().isoformat(),
        'version': '1.0',
        'status': 'success' if not state.get('fatal_error') else 'error',
        'summary': state.get('metrics', {}),
        'candidate_factors': state.get('candidate_factors', []),
        'data_quality': state.get('data_quality_issues', []),
        'failures_identified': len(state.get('failures', [])),
        'limitations': [
            'Correlation analysis only - no causal proof',
            'Synthetic sample data for demonstration',
            'Deterministic analysis without ML models'
        ]
    }

    state['report'] = report

    # Write JSON report
    os.makedirs('outputs', exist_ok=True)
    with open('outputs/analysis.json', 'w') as f:
        import json
        json.dump(report, f, indent=2)

    # Write Markdown report
    with open('outputs/report.md', 'w') as f:
        f.write(_generate_markdown_report(report))

    logger.info("Reports written to outputs/")
    return state


def _generate_markdown_report(report: dict) -> str:
    """Generate markdown report content."""
    md = f"""# Manufacturing Predictive Maintenance Analysis Report

**Generated:** {report['generated_at']}
**Version:** {report['version']}
**Status:** {report['status']}

## Executive Summary

- **Machines Analyzed:** {report['summary'].get('total_machines', 'N/A')}
- **Machines with Telemetry:** {report['summary'].get('machines_with_telemetry', 'N/A')}
- **Failures Identified:** {report['failures_identified']}
- **Total Downtime:** {report['summary'].get('total_downtime_hours', 0):.1f} hours
- **Average Downtime per Incident:** {report['summary'].get('avg_downtime_per_incident', 0):.1f} hours

## Candidate Pre-Failure Signals

"""
    for factor in report.get('candidate_factors', [])[:5]:
        md += f"""### {factor['factor_name']}

- **Observed in:** {factor['observed_in_failures']}/{factor['total_failures']} failures ({factor['frequency_percent']:.1f}%)
- **Confidence:** {factor['confidence_level']}

"""

    md += """## Data Quality

"""
    if report.get('data_quality'):
        for issue in report['data_quality']:
            md += f"- {issue}\n"
    else:
        md += "- No major data quality issues detected\n"

    md += """
## Important Limitations

"""
    for limitation in report.get('limitations', []):
        md += f"- {limitation}\n"

    return md


# ============================================================================
# BUILD GRAPH
# ============================================================================

def build_graph():
    """Build and compile the analysis workflow."""
    if StateGraph is None:
        raise ImportError("langgraph not installed. Install with: pip install langgraph")

    graph = StateGraph(AnalysisState)

    # Add nodes
    graph.add_node("ingest_files", ingest_files_node)
    graph.add_node("detect_format", detect_format_node)
    graph.add_node("parse_data", parse_data_node)
    graph.add_node("normalize_data", normalize_data_node)
    graph.add_node("validate_data", validate_data_node)
    graph.add_node("analyze_telemetry", analyze_telemetry_node)
    graph.add_node("analyze_maintenance", analyze_maintenance_node)
    graph.add_node("correlate_events", correlate_events_node)
    graph.add_node("identify_patterns", identify_patterns_node)
    graph.add_node("calculate_metrics", calculate_metrics_node)
    graph.add_node("generate_report", generate_report_node)

    # Add edges - set entry point instead of START
    graph.set_entry_point("ingest_files")
    graph.add_edge("ingest_files", "detect_format")
    graph.add_edge("detect_format", "parse_data")
    graph.add_edge("parse_data", "normalize_data")
    graph.add_edge("normalize_data", "validate_data")
    graph.add_edge("validate_data", "analyze_telemetry")
    graph.add_edge("analyze_telemetry", "analyze_maintenance")
    graph.add_edge("analyze_maintenance", "correlate_events")
    graph.add_edge("correlate_events", "identify_patterns")
    graph.add_edge("identify_patterns", "calculate_metrics")
    graph.add_edge("calculate_metrics", "generate_report")
    graph.set_finish_point("generate_report")

    compiled = graph.compile()
    logger.info("Graph compiled successfully")
    return compiled
