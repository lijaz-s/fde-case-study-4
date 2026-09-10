# Technical Specification
## Local Manufacturing Maintenance Analysis Agent

**Version:** 1.0  
**Date:** September 2026  
**Technology Stack:** Python 3.11+, LangGraph, pandas, Pydantic  

---

## 1. Architecture Overview

### 1.1 Layered Design

```
┌─────────────────────────────────────────────────┐
│          Application Entry Point                │
│  (CLI: analyze <data_path>)                     │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│      LangGraph StateGraph (Orchestration)       │
│  - Deterministic node execution                 │
│  - Typed state management                       │
│  - Error handling & recovery                    │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐ ┌───▼───┐ ┌────▼────┐
    │Ingestion│ │Analysis│ │Reporting│
    └────┬────┘ └───┬───┘ └────┬────┘
         │          │          │
    ┌────▼────┐ ┌───▼───┐ ┌────▼────┐
    │Parser   │ │Anom.  │ │JSON/    │
    │Registry │ │Detect │ │Markdown │
    │         │ │Rules  │ │         │
    └─────────┘ └───────┘ └─────────┘

│ Domain Logic (testable independently)
└─────────────────────────────────────────────────┘
```

### 1.2 Core Components

| Component | Responsibility |
|-----------|-----------------|
| **Ingestion** | Discover files, route to appropriate parser, handle unsupported types |
| **Parsers** | Convert format-specific files to normalized records (CSV, JSON, TXT) |
| **Normalization** | Map vendor schemas to common machine/maintenance schema |
| **Validation** | Check for missing required fields, data type errors, logical inconsistencies |
| **Analysis** | Deterministic algorithms (thresholds, anomaly detection, pattern matching) |
| **Correlation** | Link telemetry events to failures, maintenance to outcomes |
| **Reporting** | Generate JSON output and human-readable Markdown report |

---

## 2. LangGraph Workflow

### 2.1 State Definition

```python
class AnalysisState(TypedDict):
    # Input
    input_paths: list[str]                    # Paths to data directories
    
    # Discovery & Ingestion
    discovered_files: list[dict]              # {path, format, size, status}
    ingestion_errors: list[str]               # Errors during file discovery
    
    # Parsing & Normalization
    raw_records: list[dict]                   # Unprocessed parsed data
    parsed_records: list[dict]                # Parsed + typed records
    normalized_telemetry: list[dict]          # Common machine telemetry schema
    normalized_maintenance: list[dict]        # Common maintenance schema
    machine_inventory: list[dict]             # Master list of machines
    
    # Analysis
    failures: list[dict]                      # Detected failure events
    anomalies: list[dict]                     # Threshold/statistical anomalies
    patterns: list[dict]                      # Recurring conditions before failures
    candidate_factors: list[dict]             # Possible contributing factors
    dashboard_correlation: dict               # RED state analysis
    
    # Metrics & Output
    metrics: dict                             # KPIs (downtime, MTBF, etc.)
    data_quality_issues: list[str]            # Missing data, inconsistencies
    report: dict                              # Final structured findings
    
    # Errors
    errors: list[str]                         # Non-fatal errors for reporting
    fatal_error: str | None                   # Halts pipeline if present
```

### 2.2 Node Definitions

#### START
No-op entry point. Validates input paths exist.

#### `ingest_files`
- Walk input directories
- Identify all files by extension
- Categorize as: `supported`, `unsupported`, `error`
- Build file manifest
- **Output:** `discovered_files`, `ingestion_errors`

#### `detect_format`
- For each discovered file, determine parser
- Validate file headers/structure when possible
- Map file type to parser class
- **Output:** Updated `discovered_files` with format metadata

#### `parse_data`
- For each file with identified parser:
  - Read file
  - Parse into structured records
  - Catch parse errors (malformed JSON, CSV dialect, etc.)
  - Continue with remaining files if one fails
- Separate files by category: telemetry, maintenance, inventory, dashboard, other
- **Output:** `raw_records`, parsing errors appended to `ingestion_errors`

#### `normalize_data`
- For each parsed record:
  - Identify vendor (from metadata or schema inference)
  - Apply vendor-specific normalization rules
  - Map vendor fields to common schema
  - Preserve unmapped fields as metadata
- **Output:** `normalized_telemetry`, `normalized_maintenance`, `machine_inventory`

#### `validate_data`
- Type checking: ensure timestamp is datetime, numeric fields are numeric
- Logical validation: end_time > start_time, downtime >= 0
- Completeness check: flag records missing critical fields
- Data quality scoring: completeness % per machine
- **Output:** Validation errors added to `data_quality_issues`

#### `analyze_telemetry`
- For each machine with telemetry:
  - Compute rolling averages (5-min, 30-min, 1-hour windows)
  - Detect threshold violations (e.g., temp > 95°C)
  - Compute z-scores for each numeric field
  - Apply IQR anomaly detection
- **Output:** `anomalies` (with timestamp, machine, field, severity)

#### `analyze_maintenance`
- Aggregate maintenance events by machine
- Calculate maintenance intervals
- Identify frequency patterns
- Flag recently serviced machines (last N days)
- Extract observed outcomes (bearing replaced, filter cleaned, etc.)
- **Output:** Updated `normalized_maintenance` with calculated fields

#### `correlate_events`
- For each known failure, find:
  - Telemetry in N hours before (default 6 hours)
  - Any maintenance within M days before (default 30 days)
  - Dashboard status at time of failure
  - Anomalies in pre-failure window
- **Output:** `failures` with complete context

#### `detect_anomalies`
- Reprocess anomalies in context of failures
- For each anomaly type (spindle temp, pressure, vibration, etc.):
  - Count how many failures had this anomaly in pre-failure window
  - Calculate median lead time (anomaly → failure)
  - Compute false-positive rate (anomaly but no failure)
- **Output:** Updated `anomalies` with statistical context

#### `identify_candidate_patterns`
- For each anomaly type with sufficient data (e.g., >= 3 occurrences):
  - Classify as: Strong Candidate (>60% of failures), Moderate (30-60%), Weak (<30%)
  - Include confidence rationale (sample size, consistency)
  - Reference supporting evidence (machine IDs, dates, maintenance notes)
- **Output:** `candidate_factors` with structured evidence

#### `calculate_metrics`
- **Downtime metrics:**
  - Total downtime hours by machine
  - Average downtime per incident
  - Downtime frequency (incidents per week)
  - Cost estimate if hourly rate provided
- **Maintenance metrics:**
  - Maintenance frequency (incidents per month)
  - Time between maintenance
  - Maintenance coverage % (machines receiving maintenance)
- **Data metrics:**
  - % of machines with complete telemetry
  - % of maintenance records with timestamps
  - Data completeness scoring
- **OUTPUT:** `metrics` dict

#### `generate_report`
- Synthesize all analysis into structured report:
  - Summary statistics
  - Per-machine analysis
  - Candidate pre-failure signals
  - Dashboard RED correlation analysis
  - Data quality summary
  - Limitations and confidence statements
- Export as:
  - `outputs/analysis.json` (machine-readable)
  - `outputs/report.md` (human-readable)
- **Output:** `report` dict with export paths

#### END
Return final `AnalysisState` with all outputs.

---

## 3. Data Models

### 3.1 Machine Record

```python
@dataclass
class Machine:
    machine_id: str                 # Unique identifier (e.g., "CNC-004")
    machine_type: str              # CNC, Injection Moulding, Assembly
    vendor: str | None             # FANUC, Haas, Engel, etc.
    plant: str | None              # Physical location
    commissioned_year: int | None
    telemetry_available: bool
    criticality: str | None        # high, medium, low
    last_maintenance_date: datetime | None
    source_file: str               # Where data came from
```

### 3.2 Telemetry Record

```python
@dataclass
class TelemetryEvent:
    machine_id: str
    timestamp: datetime
    spindle_temperature: float | None  # °C
    pressure: float | None             # bar
    vibration: float | None            # mm/s
    motor_current: float | None        # A
    spindle_load: float | None         # %
    cycle_time: float | None           # seconds
    error_code: str | None
    dashboard_status: str | None       # GREEN, AMBER, RED
    # Preserved vendor-specific fields
    _vendor_fields: dict
    source_file: str
```

### 3.3 Maintenance Record

```python
@dataclass
class MaintenanceEvent:
    maintenance_id: str
    machine_id: str
    timestamp: datetime
    maintenance_type: str              # preventive, reactive, inspection
    description: str                   # Free-text notes
    technician: str | None
    parts_replaced: list[str]          # Extracted from notes
    downtime_hours: float | None
    observations: str | None           # Extracted from description
    source_file: str
```

### 3.4 Failure Record

```python
@dataclass
class FailureEvent:
    failure_id: str
    machine_id: str
    timestamp: datetime
    duration_hours: float | None       # How long the machine was down
    pre_failure_telemetry: list[TelemetryEvent]  # N hours before
    pre_failure_maintenance: list[MaintenanceEvent]  # M days before
    anomalies_before: list[dict]       # What was abnormal
    dashboard_status_at_failure: str | None
```

### 3.5 Candidate Factor

```python
@dataclass
class CandidateFactor:
    factor_name: str                   # e.g., "Spindle temperature increase"
    factor_type: str                   # e.g., "telemetry_threshold"
    observed_in_failures: int          # e.g., 8 failures
    total_failures_analyzed: int       # e.g., 10
    frequency_percent: float           # e.g., 80.0%
    median_lead_time_minutes: float | None  # Time before failure
    false_positive_rate: float         # % anomalies with no failure
    confidence_level: str              # Strong, Moderate, Weak
    supporting_evidence: list[dict]    # {machine_id, dates, details}
    rationale: str                     # Why this is a candidate
```

---

## 4. Parser Architecture

### 4.1 Parser Interface

```python
class DataParser(Protocol):
    def parse(self, file_path: str) -> list[dict]:
        """Parse file and return list of normalized records."""
        ...
    
    def detect(self, file_path: str) -> bool:
        """Return True if this parser can handle the file."""
        ...
```

### 4.2 Parser Registry

```python
class ParserRegistry:
    def __init__(self):
        self._parsers: dict[str, DataParser] = {}
    
    def register(self, format_name: str, parser: DataParser):
        """Register a parser for a file format."""
        self._parsers[format_name] = parser
    
    def get_parser(self, file_path: str) -> DataParser | None:
        """Return appropriate parser or None."""
        ...
    
    def parse_file(self, file_path: str) -> list[dict]:
        """Parse file with auto-detection or raise error."""
        ...
```

### 4.3 Built-in Parsers

#### CSV Parser
- Detect: `.csv` extension, validate headers
- Parse: Use pandas, handle dialect auto-detection
- Output: List of dicts (one per row)
- Error handling: Skip malformed rows, report issues

#### JSON Parser
- Detect: `.json` extension, valid JSON structure
- Parse: Load JSON, handle both array and object-per-line
- Output: Flatten nested structures where possible
- Error handling: Report JSON errors, skip invalid records

#### Text Parser (Maintenance Records)
- Detect: `.txt` extension
- Parse: Regex + keyword extraction
  - Date extraction: Support common formats (DD/MM/YYYY, YYYY-MM-DD, etc.)
  - Machine ID: Regex patterns like `CNC-\d{3}`, `IMM-\d{3}`
  - Downtime extraction: Look for `downtime =`, `duration =`, time formats
  - Arithmetic: Safe evaluation of simple expressions
- Output: Structured maintenance records
- Error handling: Partial extraction (missing fields stay null)

#### Image Parser (Placeholder)
- Detect: `.png`, `.jpg`, `.jpeg` extensions
- Parse: Return metadata (filename, size)
- Output: Record status as `UNSUPPORTED_IMAGE`
- Note: Semantic interpretation deferred to future

#### Excel Parser (Optional v1)
- Detect: `.xlsx`, `.xls` extensions
- Parse: Use openpyxl, handle multiple sheets
- Output: Flatten each sheet as separate record set
- Error handling: Skip unreadable sheets

---

## 5. Normalization Rules

### 5.1 Vendor Mapping Example

#### Vendor A (FANUC-style)
```json
{
  "timestamp": "2026-03-15T14:32:00Z",
  "machine_id": "CNC-004",
  "spindle_temp": 94.2,
  "vibration_mm_s": 3.1,
  "motor_current_a": 28.5,
  "status": "FAULT"
}
```

#### Vendor B (Engel-style)
```json
{
  "recordedAt": "2026-03-15T14:32:00",
  "equipmentCode": "IMM-002",
  "hydPressure_bar": 142.0,
  "cycleDuration_s": 45.2,
  "alarmState": "RED"
}
```

#### Normalized Common Schema
```python
TelemetryEvent(
    machine_id="CNC-004" | "IMM-002",
    timestamp=datetime(...),
    spindle_temperature=94.2 | None,
    pressure=142.0 | None,
    vibration=3.1 | None,
    motor_current=28.5 | None,
    spindle_load=None,
    cycle_time=45.2 | None,
    error_code=None,
    dashboard_status="FAULT" | "RED",
    _vendor_fields={...}  # Preserve extras
)
```

### 5.2 Unit Conversion (If Needed)
- Temperature: Support °C, °F, K (store as °C)
- Pressure: Support bar, psi, Pa (store as bar)
- Vibration: Support mm/s, in/s, g (store as mm/s)
- Time: Always normalize to seconds or hours

### 5.3 Missing Data Policy
- **Explicit:** Use Python `None` or Pydantic `Optional`
- **Never fabricate:** Missing sensor readings remain missing
- **Flag completeness:** Track which machines are missing which fields
- **Graceful degradation:** Analysis proceeds even with partial data

---

## 6. Deterministic Analysis Algorithms

### 6.1 Threshold Detection
```python
def detect_threshold_violations(telemetry: list[TelemetryEvent]) -> list[dict]:
    """
    Check each measurement against safety ranges.
    
    Example thresholds:
      - spindle_temperature: alert if > 90°C, critical if > 100°C
      - pressure: alert if > 150 bar or < 20 bar
      - vibration: alert if > 5.0 mm/s
    
    Return: List of {machine_id, timestamp, field, value, threshold, severity}
    """
```

### 6.2 Rolling Statistics
```python
def compute_rolling_stats(
    telemetry: list[TelemetryEvent],
    windows: list[timedelta] = [5min, 30min, 1hour]
) -> dict[str, DataFrame]:
    """
    For each numeric field, compute rolling mean, std, min, max.
    Useful for detecting trends.
    """
```

### 6.3 Z-Score Anomaly Detection
```python
def detect_zscore_anomalies(
    telemetry: list[TelemetryEvent],
    threshold: float = 2.5  # 2.5 σ
) -> list[dict]:
    """
    For each numeric field per machine:
      1. Compute mean and std (exclude obvious outliers)
      2. Flag values > threshold * σ away from mean
      3. Handle machines with insufficient data
    
    Return: List of {machine_id, timestamp, field, value, zscore}
    """
```

### 6.4 IQR Anomaly Detection
```python
def detect_iqr_anomalies(
    telemetry: list[TelemetryEvent],
    k: float = 1.5  # Standard IQR multiplier
) -> list[dict]:
    """
    For each numeric field per machine:
      1. Compute Q1, Q3, IQR
      2. Flag values < Q1 - k*IQR or > Q3 + k*IQR
      3. Handle small sample sizes
    
    Return: List of {machine_id, timestamp, field, value, quartile_distance}
    """
```

### 6.5 Pre-Failure Window Analysis
```python
def analyze_pre_failure_telemetry(
    failure: FailureEvent,
    all_telemetry: list[TelemetryEvent],
    window_hours: int = 6
) -> dict[str, dict]:
    """
    For a known failure:
      1. Extract telemetry N hours before failure
      2. Extract normal telemetry (other time periods, same machine)
      3. Compare: pre-failure vs. normal
        - Mean, std deviation
        - % change in each field
        - Anomalies present before failure
    
    Return: {
        field_name: {
            pre_failure_mean: float,
            normal_mean: float,
            percent_change: float,
            anomalies_detected: list
        }
    }
    """
```

### 6.6 Pattern Frequency Analysis
```python
def analyze_pattern_frequency(
    failures: list[FailureEvent],
    anomalies: list[dict]
) -> list[CandidateFactor]:
    """
    For each anomaly type:
      1. Count failures where this anomaly appeared pre-failure
      2. Calculate frequency: N failures / total failures
      3. Calculate median lead time: when did anomaly occur before failure?
      4. Calculate false positive rate: anomaly but no failure
      5. Classify confidence: Strong (>60%), Moderate (30-60%), Weak (<30%)
    
    Return: List of CandidateFactor with evidence
    """
```

### 6.7 Dashboard RED Correlation
```python
def analyze_dashboard_correlation(
    failures: list[FailureEvent],
    all_telemetry: list[TelemetryEvent]
) -> dict:
    """
    For RED dashboard states:
      1. Count: how many failures were preceded by RED state
      2. Lead time: how long before failure did RED appear
      3. False positives: RED states with no subsequent failure
      4. Sensitivity: % of failures with prior RED
      5. False positive rate: % of RED states causing no failure
    
    Return: {
        failures_with_prior_red: int,
        total_failures: int,
        red_frequency_percent: float,
        median_lead_time_hours: float,
        false_positive_rate: float,
        machines_with_red_alerts: list[str]
    }
    """
```

### 6.8 Downtime Metrics
```python
def calculate_downtime_metrics(
    failures: list[FailureEvent],
    maintenance: list[MaintenanceEvent]
) -> dict:
    """
    Return: {
        total_downtime_hours: float,
        avg_downtime_per_incident: float,
        incident_frequency_per_week: float,
        machines_ranked_by_downtime: list,
        estimated_cost_impact: float (if hourly rate provided)
    }
    """
```

---

## 7. Reasoning Provider Interface

### 7.1 Protocol Definition

```python
from typing import Protocol

class ReasoningProvider(Protocol):
    """Abstract interface for adding reasoning to analysis."""
    
    def analyze(self, context: dict) -> dict:
        """
        Given analysis context, return enhanced insights.
        
        Args:
            context: Dict with keys like:
                - failures: list[FailureEvent]
                - anomalies: list[dict]
                - patterns: list[CandidateFactor]
                - metrics: dict
                - data_quality: list[str]
        
        Returns:
            Dict with enhanced reasoning:
                - root_cause_analysis: str
                - recommended_actions: list[str]
                - confidence_scores: dict
        """
        ...
```

### 7.2 Deterministic Implementation

```python
class RuleBasedReasoningProvider:
    """
    v1 implementation using deterministic rules.
    No LLM, no external calls.
    """
    
    def analyze(self, context: dict) -> dict:
        # Apply rule-based reasoning
        recommendations = []
        for factor in context.get('patterns', []):
            if factor.confidence_level == 'Strong':
                recommendations.append(
                    f"Investigate {factor.factor_name} "
                    f"(observed in {factor.frequency_percent}% of failures)"
                )
        return {
            'root_cause_analysis': self._synthesize_analysis(context),
            'recommended_actions': recommendations,
            'confidence': 'deterministic (no model)'
        }
```

### 7.3 Future AI Implementation (Placeholder)

```python
class AIReasoningProvider:
    """
    Placeholder for future LLM integration.
    Will replace RuleBasedReasoningProvider when LLM available.
    """
    
    def analyze(self, context: dict) -> dict:
        raise NotImplementedError(
            "AI reasoning not available in v1. "
            "Set REASONING_PROVIDER=rule_based in config."
        )
```

---

## 8. Configuration

### 8.1 Config Schema

```python
@dataclass
class AnalysisConfig:
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
    
    # Output paths
    output_dir: str = "outputs"
    
    # Reasoning
    reasoning_provider: str = "rule_based"  # Future: "ai"
```

---

## 9. Output Schemas

### 9.1 JSON Analysis Output

```json
{
  "metadata": {
    "generated_at": "2026-09-15T10:30:00Z",
    "version": "1.0",
    "input_files": [...],
    "notes": "Synthetic data - not real plant information"
  },
  "summary": {
    "machines_analyzed": 12,
    "machines_with_telemetry": 10,
    "total_downtime_hours": 87.3,
    "incidents_identified": 23,
    "avg_incident_frequency_per_week": 1.2
  },
  "machines": [
    {
      "machine_id": "CNC-004",
      "machine_type": "CNC",
      "vendor": "FANUC",
      "telemetry_available": true,
      "incidents": 3,
      "downtime_hours": 8.5,
      "last_maintenance": "2026-03-14",
      "data_completeness": 0.95
    }
  ],
  "candidate_factors": [
    {
      "factor_name": "Spindle temperature increase",
      "observed_in_failures": 8,
      "total_failures": 10,
      "frequency_percent": 80.0,
      "median_lead_time_minutes": 93,
      "confidence_level": "Strong",
      "supporting_evidence": [
        {"machine_id": "CNC-004", "date": "2026-03-15", "details": "..."}
      ]
    }
  ],
  "dashboard_correlation": {
    "red_before_failure_count": 5,
    "total_failures": 10,
    "sensitivity_percent": 50.0,
    "false_positive_rate": 0.15
  },
  "data_quality": {
    "machines_with_insufficient_data": ["CNC-012"],
    "completeness_issues": ["Machine X missing temperature sensor"],
    "unsupported_files": ["graph_image.png"]
  },
  "limitations": [
    "Correlation analysis only, no causal proof",
    "20% of machines lack telemetry",
    "Image graphs catalogued but not interpreted"
  ]
}
```

### 9.2 Markdown Report

```markdown
# Manufacturing Predictive Maintenance Analysis Report

**Generated:** 2026-09-15 10:30 UTC  
**Data Source:** Sample plant data (synthetic for demonstration)

## Executive Summary
- Machines analyzed: 12 (10 with telemetry)
- Average breakdown frequency: ~1 incident per week
- Total identified downtime: 87.3 hours
- Candidate pre-failure signals identified: 3

## Machine Breakdown Summary
[Table with machines, failure counts, downtime]

## Candidate Pre-Failure Signals

### Strong Candidate: Spindle Temperature Increase
- **Observed before:** 8 of 10 failures (80%)
- **Median lead time:** 93 minutes
- **False positive rate:** 15%
- **Machines affected:** CNC-004, CNC-007, CNC-009
- **Example:** On 2026-03-15, CNC-004 temperature rose from 71°C to 94°C over 2 hours; failure occurred 93 minutes later
- **Assessment:** This is a strong candidate signal. The pattern is repeatable and appears before most failures with consistent lead time.

### Moderate Candidate: Hydraulic Pressure Drop
...

## Data Quality Issues
- 1 machine (CNC-012) lacks telemetry
- 1 graph image present but not interpreted
- Maintenance records 85% complete

## Limitations
- **Correlation ≠ Causation:** This analysis identifies patterns, not root causes
- **Limited Sample:** 10 machines with telemetry over 60 days
- **No Causal Proof:** Temperature increase may be symptom, not cause

## Next Steps
1. Validate findings with maintenance team
2. Collect additional telemetry data
3. Implement targeted monitoring for candidate signals
4. Track outcomes of maintenance interventions
```

---

## 10. Integration Points for Future Enhancement

### 10.1 AI/LLM Integration
- Inject `AIReasoningProvider` replacing `RuleBasedReasoningProvider`
- No changes to ingestion, normalization, or analysis pipeline
- Add configuration to select provider

### 10.2 New Format Support
- Implement new parser class
- Register in `ParserRegistry`
- No changes to downstream analysis

### 10.3 Image Analysis
- Create `ImageParser` implementation
- Optionally integrate vision model
- Provide extracted data to standard analysis pipeline

### 10.4 Cloud Integration (Future)
- Keep all local logic unchanged
- Add optional cloud sync layer
- Maintain offline-first operation

---

## 11. Error Handling & Recovery

### 11.1 Failure Modes
- **Ingestion failure:** Skip file, log error, continue
- **Parse error:** Partial data extraction, report validity
- **Normalization failure:** Preserve raw record, mark as unmapped
- **Analysis error:** Log and continue with other machines
- **Reporting error:** Output partial report, document issues

### 11.2 Logging Strategy
- Debug: Detailed parsing, normalization steps
- Info: File processing, analysis progress
- Warning: Data quality issues, skipped records
- Error: Non-recoverable failures per file

---

## 12. Performance Considerations

### 12.1 Scalability
- Prototype assumes <20 machines, 6 months data
- No database required (in-memory processing)
- Pandas operations expected < 5 seconds per dataset

### 12.2 Future Optimization
- Streaming ingestion for large datasets
- Incremental analysis
- Database backend for production deployment

---

## 13. Testing Strategy

### 13.1 Unit Tests
- Parser tests: CSV, JSON, TXT with edge cases
- Normalization tests: Vendor schema mapping
- Analysis tests: Threshold, Z-score, IQR algorithms
- Arithmetic parser tests: Safe expression evaluation

### 13.2 Integration Tests
- End-to-end: Files → Normalized → Analysis → Report
- Error recovery: Invalid files don't stop pipeline
- Format variety: Mixed vendor data

### 13.3 Acceptance Tests
- All user stories pass acceptance criteria
- Findings derive from actual data (not hard-coded)
- Report accurately represents analysis
