"""
Data models for the Maintenance Analysis Agent.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class MachineType(str, Enum):
    """Supported machine types."""
    CNC = "CNC"
    INJECTION_MOULDING = "Injection Moulding"
    ASSEMBLY = "Assembly"
    TESTING = "Testing"
    OTHER = "Other"


class MaintenanceType(str, Enum):
    """Types of maintenance interventions."""
    PREVENTIVE = "preventive"
    REACTIVE = "reactive"
    INSPECTION = "inspection"
    AUDIT = "audit"


class DashboardStatus(str, Enum):
    """Dashboard status states."""
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


class ConfidenceLevel(str, Enum):
    """Confidence levels for candidate factors."""
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"
    INSUFFICIENT_DATA = "Insufficient Data"


@dataclass
class Machine:
    """Represents a manufacturing machine."""
    machine_id: str
    machine_type: str  # MachineType value
    vendor: Optional[str] = None
    plant: Optional[str] = None
    commissioned_year: Optional[int] = None
    telemetry_available: bool = False
    criticality: Optional[str] = None  # high, medium, low
    last_maintenance_date: Optional[datetime] = None
    source_file: str = ""

    def __hash__(self):
        return hash(self.machine_id)

    def __eq__(self, other):
        if isinstance(other, Machine):
            return self.machine_id == other.machine_id
        return False


@dataclass
class TelemetryEvent:
    """Represents a telemetry measurement from a machine."""
    machine_id: str
    timestamp: datetime
    spindle_temperature: Optional[float] = None  # °C
    pressure: Optional[float] = None  # bar
    vibration: Optional[float] = None  # mm/s
    motor_current: Optional[float] = None  # A
    spindle_load: Optional[float] = None  # %
    cycle_time: Optional[float] = None  # seconds
    error_code: Optional[str] = None
    dashboard_status: Optional[str] = None  # GREEN, AMBER, RED
    vendor_fields: dict = field(default_factory=dict)
    source_file: str = ""


@dataclass
class MaintenanceEvent:
    """Represents a maintenance intervention."""
    maintenance_id: str
    machine_id: str
    timestamp: datetime
    maintenance_type: str  # MaintenanceType value
    description: str = ""
    technician: Optional[str] = None
    parts_replaced: list = field(default_factory=list)
    downtime_hours: Optional[float] = None
    observations: Optional[str] = None
    source_file: str = ""


@dataclass
class FailureEvent:
    """Represents a detected machine failure."""
    failure_id: str
    machine_id: str
    timestamp: datetime
    duration_hours: Optional[float] = None
    pre_failure_telemetry: list = field(default_factory=list)  # TelemetryEvent list
    pre_failure_maintenance: list = field(default_factory=list)  # MaintenanceEvent list
    anomalies_before: list = field(default_factory=list)  # Anomaly dicts
    dashboard_status_at_failure: Optional[str] = None


@dataclass
class Anomaly:
    """Represents an anomaly in telemetry."""
    timestamp: datetime
    machine_id: str
    field_name: str
    value: float
    severity: str  # alert, critical, warning
    reason: str  # threshold, zscore, iqr
    threshold: Optional[float] = None
    zscore: Optional[float] = None
    outlier_reason: str = ""


@dataclass
class CandidateFactor:
    """Represents a candidate contributing factor to failures."""
    factor_id: str
    factor_name: str
    factor_type: str  # telemetry_threshold, statistical_anomaly, dashboard, etc.
    observed_in_failures: int
    total_failures_analyzed: int
    frequency_percent: float
    median_lead_time_minutes: Optional[float] = None
    false_positive_rate: float = 0.0
    confidence_level: str = ConfidenceLevel.WEAK.value
    supporting_evidence: list = field(default_factory=list)  # dicts with details
    rationale: str = ""

    @property
    def strength_summary(self) -> str:
        """Return a summary of the factor's strength."""
        return f"{self.observed_in_failures}/{self.total_failures_analyzed} failures ({self.frequency_percent:.1f}%)"


@dataclass
class DashboardCorrelation:
    """Analysis of dashboard RED state correlation with failures."""
    failures_with_prior_red: int = 0
    total_failures: int = 0
    red_frequency_percent: float = 0.0
    median_lead_time_hours: Optional[float] = None
    false_positive_rate: float = 0.0
    sensitivity_percent: float = 0.0
    machines_with_red_alerts: list = field(default_factory=list)
    red_before_failure_windows: list = field(default_factory=list)  # Details


@dataclass
class MetricsData:
    """Summary metrics from analysis."""
    total_downtime_hours: float = 0.0
    avg_downtime_per_incident: float = 0.0
    incident_frequency_per_week: float = 0.0
    incident_frequency_per_month: float = 0.0
    maintenance_frequency_per_week: float = 0.0
    machines_with_telemetry: int = 0
    machines_without_telemetry: int = 0
    data_completeness_percent: float = 0.0
    machines_ranked_by_downtime: list = field(default_factory=list)  # (machine_id, hours)
    estimated_cost_impact_usd: Optional[float] = None


@dataclass
class DataQualityIssue:
    """Represents a data quality problem."""
    severity: str  # error, warning, info
    category: str  # missing_data, malformed, unsupported, incomplete
    description: str
    affected_items: list = field(default_factory=list)  # File names, machine IDs, etc.


def to_dict(obj) -> dict:
    """Convert dataclass to dict, handling nested dataclasses."""
    if isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__dataclass_fields__'):
        result = {}
        for field_name, field_obj in obj.__dataclass_fields__.items():
            value = getattr(obj, field_name)
            result[field_name] = to_dict(value)
        return result
    elif isinstance(obj, Enum):
        return obj.value
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj
