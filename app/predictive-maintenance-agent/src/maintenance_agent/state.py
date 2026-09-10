"""
State definition for the LangGraph workflow.
"""

from typing import TypedDict, Optional


class AnalysisState(TypedDict, total=False):
    """
    State dictionary for the predictive maintenance analysis workflow.
    Uses TypedDict for type hints and IDE support.
    """
    # Input
    input_paths: list[str]

    # Discovery & Ingestion
    discovered_files: list[dict]
    ingestion_errors: list[str]

    # Parsing & Normalization
    raw_records: list[dict]
    parsed_records: list[dict]
    normalized_telemetry: list[dict]
    normalized_maintenance: list[dict]
    machine_inventory: list[dict]

    # Analysis
    failures: list[dict]
    anomalies: list[dict]
    patterns: list[dict]
    candidate_factors: list[dict]
    dashboard_correlation: dict
    maintenance_analysis: dict

    # Metrics & Output
    metrics: dict
    data_quality_issues: list[str]
    report: dict

    # Errors
    errors: list[str]
    fatal_error: Optional[str]
