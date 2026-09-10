"""
Configuration for the Maintenance Analysis Agent.
"""

from dataclasses import dataclass
import os


@dataclass
class AnalysisConfig:
    """Configuration parameters for analysis."""

    # Analysis parameters
    pre_failure_window_hours: int = 6
    maintenance_lookback_days: int = 30
    zscore_threshold: float = 2.5
    iqr_multiplier: float = 1.5

    # Confidence thresholds
    strong_pattern_threshold: float = 0.60  # > 60%
    moderate_pattern_threshold: float = 0.30  # 30-60%

    # Data requirements
    min_failures_for_pattern: int = 3
    min_machines_for_analysis: int = 2
    min_telemetry_points: int = 10

    # Output paths
    output_dir: str = "outputs"

    # Reasoning provider
    reasoning_provider: str = "rule_based"  # Future: "ai"

    # Logging
    log_level: str = "INFO"

    # Thresholds (machine-type specific, can be enhanced)
    temperature_alert_celsius: float = 90.0
    temperature_critical_celsius: float = 100.0
    pressure_alert_bar: float = 150.0
    pressure_critical_bar: float = 160.0
    vibration_alert_mm_s: float = 4.0
    vibration_critical_mm_s: float = 5.0

    @classmethod
    def from_env(cls) -> "AnalysisConfig":
        """Load config from environment variables."""
        return cls(
            pre_failure_window_hours=int(os.getenv("PRE_FAILURE_WINDOW_HOURS", "6")),
            output_dir=os.getenv("OUTPUT_DIR", "outputs"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )


# Default config instance
DEFAULT_CONFIG = AnalysisConfig()
