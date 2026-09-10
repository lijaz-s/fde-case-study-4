# Implementation Prompt
## Concrete Engineering Tasks for Local Manufacturing Maintenance Analysis Agent

**Status:** Ready for implementation  
**Technology:** Python 3.11+, LangGraph, Pydantic, pandas, pytest  

---

## Task Group 1: Project Setup

### Task 1.1 — Initialize Python Project Structure

**Related Spec:** Section 1.2 (Components)  
**Related Stories:** All  
**Files to Create:**
- `pyproject.toml` with dependencies
- `.gitignore`
- `README.md` (initial skeleton)
- `src/maintenance_agent/__init__.py`
- `src/maintenance_agent/config.py`

**Implementation Approach:**
1. Create `pyproject.toml` with:
   - `python >= 3.11`
   - `langgraph >= 0.1.0`
   - `pandas >= 2.0`
   - `pydantic >= 2.0`
   - `pytest >= 7.0`
   - `pytest-cov` for coverage
2. Set up package structure with `__init__.py` files
3. Create development setup instructions

**Completion Condition:**
- `pip install -e .` installs package without errors
- `python -c "import maintenance_agent"` succeeds
- All dependencies are pinned to specific versions

---

## Task Group 2: Data Models & Schemas

### Task 2.1 — Define Machine, Telemetry, Maintenance Data Classes

**Related Spec:** Section 3 (Data Models)  
**Related Stories:** AC-1, AC-2, AC-3  
**Files to Create:**
- `src/maintenance_agent/models.py`

**Implementation Approach:**
1. Use Pydantic `BaseModel` or Python `@dataclass` with validation
2. Define:
   - `Machine`: machine_id, type, vendor, location, commissioned_year, telemetry_available, criticality, last_maintenance_date
   - `TelemetryEvent`: machine_id, timestamp, all sensor fields, dashboard_status, vendor_fields dict
   - `MaintenanceEvent`: maintenance_id, machine_id, timestamp, type, description, technician, parts_replaced, downtime_hours, observations
   - `FailureEvent`: failure_id, machine_id, timestamp, duration, pre_failure_telemetry list, pre_failure_maintenance list, anomalies
   - `CandidateFactor`: factor_name, frequency, lead_time, confidence_level, evidence list
3. Add validation (e.g., downtime_hours >= 0)
4. Ensure serialization to/from JSON works

**Testing:**
- `test_machine_model_creation`
- `test_telemetry_event_validation`
- `test_maintenance_event_parsing`
- `test_model_json_serialization`

**Completion Condition:**
- All models instantiate and validate correctly
- Invalid data raises appropriate exceptions
- Models serialize/deserialize JSON cleanly

---

### Task 2.2 — Define LangGraph State Structure

**Related Spec:** Section 2.2 (State Definition)  
**Related Stories:** AC-13  
**Files to Create:**
- `src/maintenance_agent/state.py`

**Implementation Approach:**
1. Create `AnalysisState` as `TypedDict` with all required fields
2. Define state field types precisely (list, dict, str, etc.)
3. Add docstrings for each field
4. Ensure state is easily serializable

```python
class AnalysisState(TypedDict):
    input_paths: list[str]
    discovered_files: list[dict]
    # ... rest of fields
```

**Testing:**
- `test_state_structure`
- `test_state_type_hints`

**Completion Condition:**
- State dict has all required fields
- Type hints are complete
- State can be dumped/loaded as JSON for logging

---

### Task 2.3 — Define Configuration Schema

**Related Spec:** Section 8 (Configuration)  
**Related Stories:** All  
**Files to Create:**
- `src/maintenance_agent/config.py` (updated with AnalysisConfig class)

**Implementation Approach:**
1. Create `AnalysisConfig` dataclass with:
   - pre_failure_window_hours
   - maintenance_lookback_days
   - zscore_threshold, iqr_multiplier
   - Strong/moderate pattern thresholds
   - min_failures_for_pattern, min_machines_for_analysis
   - output_dir
   - reasoning_provider
2. Load from environment variables or config file (optional)
3. Provide defaults matching SPEC

**Testing:**
- `test_config_defaults`
- `test_config_environment_override`

**Completion Condition:**
- Config loads with defaults
- All values are reasonable and documented
- Config can be displayed in logs

---

## Task Group 3: Data Ingestion & Parsing

### Task 3.1 — Build Parser Interface & Registry

**Related Spec:** Section 4 (Parser Architecture)  
**Related Stories:** AC-1, AC-9  
**Files to Create:**
- `src/maintenance_agent/ingestion/parser_registry.py`
- `src/maintenance_agent/ingestion/__init__.py`

**Implementation Approach:**
1. Define `DataParser` Protocol with:
   - `parse(file_path: str) -> list[dict]`
   - `detect(file_path: str) -> bool`
2. Implement `ParserRegistry` class with:
   - `register(format_name: str, parser: DataParser)`
   - `get_parser(file_path: str) -> DataParser | None`
   - `parse_file(file_path: str) -> list[dict] | None`
3. Handle errors gracefully (return error details, not exceptions)
4. Add logging for debugging

**Testing:**
- `test_parser_registry_registration`
- `test_parser_selection_by_extension`
- `test_parser_not_found_handling`

**Completion Condition:**
- Registry accepts new parsers
- Parser selection is deterministic
- Errors are captured and reported

---

### Task 3.2 — Implement CSV Parser

**Related Spec:** Section 4.3 (CSV Parser)  
**Related Stories:** AC-1  
**Files to Create:**
- `src/maintenance_agent/ingestion/csv_parser.py`

**Implementation Approach:**
1. Use pandas `read_csv()` with error handling
2. Detect common issues (encoding, delimiter, headers)
3. Convert rows to list of dicts
4. Validate required columns if possible
5. Return partial results on recoverable errors

**Testing:**
- `test_csv_basic_parse`
- `test_csv_dialect_detection`
- `test_csv_missing_columns`
- `test_csv_type_inference`
- `test_csv_malformed_recovery`

**Completion Condition:**
- Parses standard CSV files
- Handles encoding issues
- Returns consistent dict format

---

### Task 3.3 — Implement JSON Parser

**Related Spec:** Section 4.3 (JSON Parser)  
**Related Stories:** AC-1  
**Files to Create:**
- `src/maintenance_agent/ingestion/json_parser.py`

**Implementation Approach:**
1. Load JSON with error messages
2. Handle both array and object formats
3. Flatten nested structures where reasonable
4. Preserve vendor-specific fields
5. Report malformed JSON clearly

**Testing:**
- `test_json_array_parse`
- `test_json_object_parse`
- `test_json_nested_structure_flattening`
- `test_json_malformed_error`
- `test_json_ndjson_format`

**Completion Condition:**
- Parses valid JSON
- Handles both arrays and objects
- Reports errors without crashing

---

### Task 3.4 — Implement Text Parser (Maintenance Records)

**Related Spec:** Section 4.3 (Text Parser), Section 12 (Maintenance Record Schema)  
**Related Stories:** AC-1, AC-3  
**Files to Create:**
- `src/maintenance_agent/ingestion/text_parser.py`
- `src/maintenance_agent/ingestion/text_extractors.py` (helper functions)

**Implementation Approach:**
1. Split text into logical records (by double newline or separator)
2. For each record, extract:
   - **Machine ID:** Use regex patterns like `[A-Z]{3}-\d{3}`, `[A-Z]{3}\d{3}`
   - **Timestamp:** Try multiple date formats (DD/MM/YYYY, YYYY-MM-DD, Month DD YYYY, etc.)
   - **Downtime:** Look for keywords (`downtime =`, `duration =`) and parse numbers
   - **Parts replaced:** Extract after keywords like `replaced`, `installed`, `changed`
   - **Observations:** Capture free-text description
3. Safe arithmetic: Regex to find expressions like `1.5 + 0.75`, evaluate with `eval()` after validation
   - Only allow +, -, *, /, (, ), numbers, decimal point
   - Use `ast.literal_eval()` or similar for safety
4. Return partial records if some fields missing

**Testing:**
- `test_text_machine_id_extraction`
- `test_text_date_parsing_multiple_formats`
- `test_text_downtime_extraction`
- `test_text_arithmetic_evaluation_safe`
- `test_text_partial_extraction`
- `test_text_record_splitting`

**Completion Condition:**
- Extracts machine IDs reliably
- Parses multiple date formats
- Evaluates arithmetic safely
- Graceful partial extraction

---

### Task 3.5 — Build File Discovery & Categorization

**Related Spec:** Section 1.2, Section 4  
**Related Stories:** AC-1  
**Files to Create:**
- `src/maintenance_agent/ingestion/discoverer.py`

**Implementation Approach:**
1. Walk input directory recursively
2. For each file:
   - Get extension
   - Check file size (skip very large files with warning)
   - Attempt to assign category (telemetry, maintenance, inventory, dashboard, other)
   - Try to detect format
3. Return file manifest with metadata
4. Report any issues (unreadable files, etc.)

**Testing:**
- `test_file_discovery_basic`
- `test_file_categorization`
- `test_unsupported_file_handling`
- `test_large_file_warning`

**Completion Condition:**
- Discovers all files recursively
- Categorizes by extension
- Handles errors gracefully

---

## Task Group 4: Data Normalization

### Task 4.1 — Implement Vendor Mapping Configuration

**Related Spec:** Section 5 (Normalization Rules)  
**Related Stories:** AC-2  
**Files to Create:**
- `src/maintenance_agent/normalization/vendor_mappings.py`

**Implementation Approach:**
1. Define vendor schemas as dicts mapping vendor names to field mappings
2. Example:
```python
VENDOR_MAPPINGS = {
    "vendor_a": {
        "spindle_temp": "spindle_temperature",
        "vibration_mm_s": "vibration",
        "motor_current_a": "motor_current",
        ...
    },
    "vendor_b": {
        "equipmentCode": "machine_id",
        "recordedAt": "timestamp",
        "hydPressure_bar": "pressure",
        ...
    }
}
```
3. Support multiple vendor names for same vendor (e.g., "FANUC", "Fanuc", "fanuc")
4. Store unit information for conversion

**Testing:**
- `test_vendor_mapping_lookup`
- `test_vendor_name_normalization`

**Completion Condition:**
- All major vendors defined
- Easy to add new vendors
- Mappings are complete and tested

---

### Task 4.2 — Implement Field Mapping & Normalization

**Related Spec:** Section 5 (Normalization Rules)  
**Related Stories:** AC-2  
**Files to Create:**
- `src/maintenance_agent/normalization/normalizer.py`

**Implementation Approach:**
1. Create `Normalizer` class that:
   - Takes parsed record (dict), vendor name, record type
   - Maps vendor fields to common schema
   - Preserves unmapped fields in `_vendor_fields`
   - Returns normalized `TelemetryEvent` or `MaintenanceEvent`
2. Handle missing fields (leave as None)
3. Apply unit conversions if needed

**Testing:**
- `test_telemetry_normalization_vendor_a`
- `test_telemetry_normalization_vendor_b`
- `test_maintenance_normalization`
- `test_missing_fields_handling`
- `test_unit_conversion_temperature`
- `test_unit_conversion_pressure`

**Completion Condition:**
- Normalizes records consistently
- Preserves vendor fields
- Handles missing data gracefully

---

### Task 4.3 — Implement Unit Conversion Utilities

**Related Spec:** Section 5.2  
**Related Stories:** AC-2  
**Files to Create:**
- `src/maintenance_agent/normalization/units.py`

**Implementation Approach:**
1. Create conversion functions:
   - `celsius_to_fahrenheit()`, `fahrenheit_to_celsius()`
   - `bar_to_psi()`, `psi_to_bar()`, `pa_to_bar()`, `bar_to_pa()`
   - `mm_s_to_in_s()`, similar for vibration
2. Add unit detection (try to guess from value range)
3. Return converted value + metadata

**Testing:**
- `test_temperature_conversions`
- `test_pressure_conversions`
- `test_vibration_conversions`
- `test_invalid_conversion_handling`

**Completion Condition:**
- All conversions accurate
- Reversible (F→C→F equals original)
- Handles edge cases

---

## Task Group 5: Data Validation

### Task 5.1 — Implement Validation Logic

**Related Spec:** Section 2.2 (validate_data node)  
**Related Stories:** AC-4, AC-8  
**Files to Create:**
- `src/maintenance_agent/ingestion/validator.py`

**Implementation Approach:**
1. Create validation functions:
   - Type checking (timestamp is datetime, numeric fields are float/int)
   - Logical validation (end_time > start_time, downtime >= 0)
   - Completeness checking (required fields present)
   - Range checking (pressure within physics bounds, temperature reasonable)
2. Return validation report with issues and severity
3. Don't fail on issues, just report them

**Testing:**
- `test_type_validation`
- `test_logical_validation`
- `test_completeness_checking`
- `test_range_checking`

**Completion Condition:**
- Detects all major issues
- Reports with severity
- Doesn't stop processing

---

## Task Group 6: Deterministic Analysis

### Task 6.1 — Implement Anomaly Detection (Thresholds)

**Related Spec:** Section 6.1, Section 6.2  
**Related Stories:** AC-4, AC-5  
**Files to Create:**
- `src/maintenance_agent/analysis/anomaly_detection.py`

**Implementation Approach:**
1. Define threshold dict for each machine type (CNC, Injection Moulding, etc.)
2. For each telemetry record, check if any field exceeds threshold
3. Assign severity (alert, critical)
4. Return list of anomalies with timing

Example thresholds:
```python
THRESHOLDS = {
    "CNC": {
        "spindle_temperature": {"alert": 90, "critical": 100},
        "pressure": {"alert": 150, "critical": 160},
        "vibration": {"alert": 4.0, "critical": 5.0}
    }
}
```

**Testing:**
- `test_threshold_violation_detection`
- `test_severity_classification`
- `test_no_anomalies_normal_operation`

**Completion Condition:**
- Detects threshold violations
- Assigns severity correctly

---

### Task 6.2 — Implement Z-Score Anomaly Detection

**Related Spec:** Section 6.3  
**Related Stories:** AC-4  
**Files to Create:**
- `src/maintenance_agent/analysis/statistical_anomalies.py`

**Implementation Approach:**
1. For each numeric field per machine:
   - Compute mean and standard deviation (exclude obvious outliers first)
   - For each value, compute z-score: `(value - mean) / std`
   - Flag values where `|zscore| > threshold` (default 2.5)
2. Handle edge cases:
   - Machines with < 10 data points: skip
   - All values identical: skip
   - Return results with confidence

**Testing:**
- `test_zscore_calculation`
- `test_zscore_anomaly_flagging`
- `test_zscore_insufficient_data_handling`
- `test_zscore_constant_data_handling`

**Completion Condition:**
- Z-scores calculated correctly
- Handles edge cases
- Deterministic results

---

### Task 6.3 — Implement IQR Anomaly Detection

**Related Spec:** Section 6.4  
**Related Stories:** AC-4  
**Files to Create:**
- `src/maintenance_agent/analysis/statistical_anomalies.py` (update)

**Implementation Approach:**
1. For each numeric field per machine:
   - Compute Q1 (25th percentile), Q3 (75th percentile)
   - Compute IQR = Q3 - Q1
   - Lower bound = Q1 - 1.5 * IQR
   - Upper bound = Q3 + 1.5 * IQR
   - Flag values outside bounds
2. Handle edge cases (small sample sizes)

**Testing:**
- `test_iqr_calculation`
- `test_iqr_outlier_detection`
- `test_iqr_small_sample_handling`

**Completion Condition:**
- IQR calculated correctly
- Outliers identified
- Handles edge cases

---

### Task 6.4 — Implement Pre-Failure Window Analysis

**Related Spec:** Section 6.5  
**Related Stories:** AC-5  
**Files to Create:**
- `src/maintenance_agent/analysis/failure_analysis.py`

**Implementation Approach:**
1. Identify failures (records marked as failures or downtime events)
2. For each failure at timestamp T:
   - Extract telemetry from N hours before T
   - Extract "normal" telemetry (same machine, non-failure periods)
   - Compare statistics: mean, std, percent change for each field
   - Identify anomalies in pre-failure window
3. Return detailed comparison

**Testing:**
- `test_pre_failure_window_extraction`
- `test_pre_failure_normal_comparison`
- `test_insufficient_pre_failure_data_flagging`

**Completion Condition:**
- Extracts pre-failure telemetry accurately
- Compares against normal operations
- Reports with confidence levels

---

### Task 6.5 — Implement Pattern Frequency Analysis

**Related Spec:** Section 6.6  
**Related Stories:** AC-4, AC-5, AC-9  
**Files to Create:**
- `src/maintenance_agent/analysis/pattern_analysis.py`

**Implementation Approach:**
1. For each anomaly type:
   - Count: how many failures had this anomaly in pre-failure window
   - Frequency: failures_with_anomaly / total_failures
   - Lead time: time from anomaly to failure (median)
   - False positives: anomaly occurred but no failure followed
   - Confidence: strong (>60%), moderate (30-60%), weak (<30%)
2. Rank by frequency and lead time consistency
3. Return structured candidate factors

**Testing:**
- `test_pattern_frequency_calculation`
- `test_confidence_classification_strong`
- `test_confidence_classification_moderate`
- `test_confidence_classification_weak`
- `test_lead_time_calculation`

**Completion Condition:**
- Frequencies calculated accurately
- Confidence classification correct
- Lead times reasonable

---

### Task 6.6 — Implement Dashboard RED Correlation

**Related Spec:** Section 6.7  
**Related Stories:** AC-6  
**Files to Create:**
- `src/maintenance_agent/analysis/dashboard_analysis.py`

**Implementation Approach:**
1. For RED dashboard states:
   - Count failures preceded by RED state within time window
   - Count RED states not followed by failure (false positives)
   - Calculate sensitivity (% of failures with prior RED)
   - Calculate false positive rate (% RED with no failure)
   - Calculate lead time (RED → failure)
2. Return correlation metrics

**Testing:**
- `test_red_correlation_sensitivity`
- `test_red_false_positive_rate`
- `test_red_lead_time_calculation`

**Completion Condition:**
- Correlations calculated
- Metrics are reasonable
- False positives tracked

---

### Task 6.7 — Implement Downtime Metrics Calculation

**Related Spec:** Section 6.8  
**Related Stories:** AC-7  
**Files to Create:**
- `src/maintenance_agent/analysis/metrics.py`

**Implementation Approach:**
1. Calculate:
   - Total downtime hours across all machines
   - Average downtime per incident
   - Incident frequency (per week, per month)
   - Machines ranked by downtime
   - Data completeness scoring
2. Optional: cost impact if hourly rate provided

**Testing:**
- `test_total_downtime_calculation`
- `test_average_per_incident`
- `test_incident_frequency`
- `test_machine_ranking`

**Completion Condition:**
- Metrics calculated accurately
- Rankings are correct
- Handles zero data gracefully

---

## Task Group 7: LangGraph Workflow

### Task 7.1 — Build LangGraph StateGraph

**Related Spec:** Section 2 (LangGraph Workflow)  
**Related Stories:** AC-13  
**Files to Create:**
- `src/maintenance_agent/graph.py`

**Implementation Approach:**
1. Import `StateGraph` from langgraph
2. Create graph with `AnalysisState` type
3. Add 17 nodes (one per step in workflow)
4. Connect nodes in correct order
5. Add error handling per node
6. Compile to runnable chain

```python
from langgraph.graph import StateGraph

graph = StateGraph(AnalysisState)
graph.add_node("ingest_files", ingest_files_node)
graph.add_node("detect_format", detect_format_node)
# ... more nodes
graph.add_edge("START", "ingest_files")
graph.add_edge("ingest_files", "detect_format")
# ... more edges
chain = graph.compile()
```

**Testing:**
- `test_graph_node_count`
- `test_graph_connections`
- `test_graph_execution_order`

**Completion Condition:**
- Graph has all nodes
- Edges connect in correct order
- Graph compiles without errors

---

### Task 7.2 — Implement Individual Graph Nodes

**Related Spec:** Section 2.2 (Node Definitions)  
**Related Stories:** All  
**Files to Create:**
- `src/maintenance_agent/nodes/` (directory)
- `src/maintenance_agent/nodes/__init__.py`
- `src/maintenance_agent/nodes/ingestion_nodes.py`
- `src/maintenance_agent/nodes/normalization_nodes.py`
- `src/maintenance_agent/nodes/analysis_nodes.py`
- `src/maintenance_agent/nodes/reporting_nodes.py`

**Implementation Approach:**
1. Each node is a Python function taking `state: AnalysisState` and returning updated state
2. Node responsibilities (from SPEC Section 2.2):
   - `ingest_files`: Walk directories, build file manifest
   - `detect_format`: Identify parser for each file
   - `parse_data`: Call parsers, collect raw records
   - `normalize_data`: Apply vendor mappings, create normalized objects
   - `validate_data`: Type/logic checking, flag issues
   - `analyze_telemetry`: Threshold, Z-score, IQR anomalies
   - `analyze_maintenance`: Aggregate maintenance events
   - `correlate_events`: Link telemetry to failures, maintenance to outcomes
   - `detect_anomalies`: Reprocess anomalies in failure context
   - `identify_candidate_patterns`: Confidence classification
   - `calculate_metrics`: Downtime, frequency, completeness
   - `generate_report`: Create JSON and Markdown output
3. Each node logs its work
4. Error handling: try/except, append to errors list, continue

**Testing:**
Each node has its own test file (e.g., `test_ingestion_nodes.py`)

**Completion Condition:**
- All nodes implemented
- Each tested individually
- State passes correctly between nodes

---

## Task Group 8: Reporting

### Task 8.1 — Implement JSON Report Generation

**Related Spec:** Section 9.1 (JSON Output)  
**Related Stories:** AC-10  
**Files to Create:**
- `src/maintenance_agent/reporting/json_reporter.py`

**Implementation Approach:**
1. Create `JSONReporter` class with method `generate(state: AnalysisState) -> dict`
2. Build dict with sections:
   - metadata (timestamps, versions, disclaimers)
   - summary (machines, downtime, incidents)
   - machines (list with stats per machine)
   - candidate_factors (with evidence)
   - dashboard_correlation
   - data_quality
   - limitations
3. Serialize to JSON file

**Testing:**
- `test_json_report_structure`
- `test_json_report_completeness`
- `test_json_serialization`

**Completion Condition:**
- JSON output valid
- All sections present
- Deterministic generation

---

### Task 8.2 — Implement Markdown Report Generation

**Related Spec:** Section 9.2 (Markdown Output)  
**Related Stories:** AC-10  
**Files to Create:**
- `src/maintenance_agent/reporting/markdown_reporter.py`

**Implementation Approach:**
1. Create `MarkdownReporter` class
2. Build Markdown with sections:
   - Header with metadata
   - Executive Summary
   - Machine Breakdown Summary (table)
   - Candidate Pre-Failure Signals (for each: evidence, assessment)
   - Data Quality Issues
   - Dashboard Alert Analysis
   - Limitations
3. Include examples and supporting evidence
4. Use clear formatting (headers, tables, lists)

**Testing:**
- `test_markdown_structure`
- `test_markdown_readability`
- `test_markdown_evidence_inclusion`

**Completion Condition:**
- Markdown renders cleanly
- Sections are clear
- Evidence is included

---

### Task 8.3 — Implement Report Writer

**Related Spec:** Section 9  
**Related Stories:** AC-10  
**Files to Create:**
- `src/maintenance_agent/reporting/writer.py`

**Implementation Approach:**
1. Create function `write_reports(state: AnalysisState, output_dir: str)`
2. Generate JSON report
3. Generate Markdown report
4. Write both to output_dir
5. Log paths and verification

**Testing:**
- `test_report_file_creation`
- `test_report_file_paths`
- `test_report_readability`

**Completion Condition:**
- Both reports written
- Files readable
- Paths logged

---

## Task Group 9: Synthetic Sample Data

### Task 9.1 — Generate Machine Inventory

**Related Spec:** Section 15-22  
**Related Stories:** AC-15  
**Files to Create:**
- `sample_data/machines.csv`

**Implementation Approach:**
1. Create ~12-15 machines:
   - 8-10 with telemetry
   - 2-3 without telemetry
   - Mix of CNC and Injection Moulding
   - Different vendors (FANUC, Haas, Engel, etc.)
   - Different plants
2. Include fields: machine_id, type, vendor, plant, commissioned_year, telemetry_available, criticality, last_maintenance_date

**Data Quality:**
- Mix of high/medium/low criticality
- Some recently serviced, some not
- Realistic years (2015-2023)

---

### Task 9.2 — Generate Vendor A Telemetry (CSV)

**Related Spec:** Section 16  
**Related Stories:** AC-1, AC-2  
**Files to Create:**
- `sample_data/vendor_a_telemetry.csv`

**Implementation Approach:**
1. Generate 60 days of hourly telemetry for ~6 CNC machines
2. Fields: timestamp, machine_id, spindle_temp, vibration_mm_s, motor_current_a, status
3. Seed realistic patterns:
   - Normal operation: spindle 60-85°C, vibration 1-2 mm/s
   - Before 8 failures: temperature rises from 71→94°C over 2 hours
   - Before 3 failures: vibration spikes to 3.5-4.5 mm/s
   - Some failures have weak precursors, some none
4. Include occasional RED status

---

### Task 9.3 — Generate Vendor B Telemetry (JSON)

**Related Spec:** Section 17  
**Related Stories:** AC-1, AC-2  
**Files to Create:**
- `sample_data/vendor_b_export.json`

**Implementation Approach:**
1. Generate telemetry for ~4 Injection Moulding machines
2. Use different field names: equipmentCode, recordedAt, hydPressure_bar, cycleDuration_s, alarmState
3. 60 days of data (less frequent, every 5 minutes for production cycles)
4. Seed patterns:
   - Before 6 failures: hydraulic pressure drops 15-20%
   - Before 4 failures: cycle time increases
   - Some RED alerts with failures, some false positives

---

### Task 9.4 — Generate Maintenance Records (Text)

**Related Spec:** Section 18  
**Related Stories:** AC-1, AC-3  
**Files to Create:**
- `sample_data/maintenance_log.txt`

**Implementation Approach:**
1. Write ~30-40 maintenance records in plain English
2. Realistic styles:
   - "15 March 2026, CNC-004. Spindle bearing replaced. Downtime = 3.4 hours."
   - "22 March 2026, IMM-002. Hydraulic pressure dropped 17% before shutdown. Filter replaced. Duration: 2.1 hours."
   - "28 March 2026, CNC-007. Routine preventive maintenance performed. Spindle oil changed, bearings inspected. Downtime = 1.5 + 0.25 hours."
3. Include arithmetic expressions
4. Mix of preventive and reactive maintenance
5. Include some records with unclear dates or partial information

---

### Task 9.5 — Generate Maintenance Contract Data

**Related Spec:** Section 19  
**Related Stories:** AC-2  
**Files to Create:**
- `sample_data/maintenance_contract.csv`

**Implementation Approach:**
1. Create records for third-party maintenance provider
2. Fields: service_id, machines_serviced, service_date, service_type, parts_replaced, provider, observations
3. ~6-8 service visits over 60 days
4. Some machines get multiple services, some none
5. Seed so that recently serviced machines have fewer incidents in analysis

---

### Task 9.6 — Generate Dashboard Status Data

**Related Spec:** Section 20  
**Related Stories:** AC-6  
**Files to Create:**
- `sample_data/dashboard_status.csv`

**Implementation Approach:**
1. Hourly dashboard status for all machines over 60 days
2. Fields: timestamp, machine_id, status (GREEN, AMBER, RED)
3. Normal: mostly GREEN with occasional AMBER
4. Seed:
   - Some RED states 2-6 hours before failures (strong correlation)
   - Some RED states with NO failure (false positives)
   - Some failures with NO prior RED (weak signal)

---

### Task 9.7 — Generate Sample Graphs (Optional)

**Related Spec:** Section 22  
**Related Stories:** AC-8  
**Files to Create:**
- `sample_data/graphs/CNC-004_temperature.png` (etc.)

**Implementation Approach:**
1. Create simple line plots using matplotlib showing:
   - Temperature over time with spike before failure
   - Pressure drop
   - Vibration increase
2. Save as PNG images
3. Keep corresponding CSV data in sample_data for analysis

---

## Task Group 10: Testing

### Task 10.1 — Create Test Infrastructure

**Related Spec:** Section 13  
**Files to Create:**
- `tests/conftest.py` (pytest fixtures)
- `tests/__init__.py`

**Implementation Approach:**
1. Create fixtures for:
   - Sample telemetry data
   - Sample maintenance records
   - Sample state dict
   - Temporary directories
2. Mock data generators for testing
3. Utilities for assertion helpers

---

### Task 10.2 — Write Unit Tests for Parsers

**Related Spec:** Section 13.1  
**Related Stories:** AC-1, AC-2, AC-3  
**Files to Create:**
- `tests/test_csv_parser.py`
- `tests/test_json_parser.py`
- `tests/test_text_parser.py`

**Test Coverage:**
- Valid inputs
- Malformed/corrupted inputs
- Edge cases (empty files, missing columns)
- Type conversions
- Determinism

---

### Task 10.3 — Write Unit Tests for Normalization

**Related Spec:** Section 13.1  
**Related Stories:** AC-2  
**Files to Create:**
- `tests/test_normalization.py`

**Test Coverage:**
- Vendor A → common schema
- Vendor B → common schema
- Unit conversions (temperature, pressure)
- Missing fields
- Determinism

---

### Task 10.4 — Write Unit Tests for Analysis

**Related Spec:** Section 13.1  
**Related Stories:** AC-4, AC-5, AC-6, AC-7  
**Files to Create:**
- `tests/test_anomaly_detection.py`
- `tests/test_statistical_analysis.py`
- `tests/test_pattern_analysis.py`
- `tests/test_metrics.py`

**Test Coverage:**
- Threshold detection
- Z-score calculations
- IQR calculations
- Pre-failure window analysis
- Pattern frequency
- Confidence classification

---

### Task 10.5 — Write Integration Tests

**Related Spec:** Section 13.2  
**Related Stories:** AC-15  
**Files to Create:**
- `tests/test_integration.py`

**Test Coverage:**
- End-to-end: sample_data → analysis → report
- Error recovery: bad files don't stop pipeline
- Format variety: mixed vendor data
- Report generation
- Determinism

---

### Task 10.6 — Add Coverage & CI Configuration

**Files to Create:**
- `.github/workflows/test.yml` (or similar)
- `pytest.ini` or `pyproject.toml` test config

**Target:** >= 80% code coverage

---

## Task Group 11: Application Entry Point

### Task 11.1 — Create CLI Entry Point

**Related Spec:** Section 1.2  
**Related Stories:** All  
**Files to Create:**
- `src/maintenance_agent/__main__.py`
- `src/maintenance_agent/cli.py`

**Implementation Approach:**
1. Create `analyze` command:
   ```
   python -m maintenance_agent analyze <data_dir>
   ```
2. Parse arguments (input directory, config overrides, output directory)
3. Initialize config
4. Load and compile LangGraph workflow
5. Execute workflow with input paths
6. Report completion and output paths
7. Handle errors gracefully

**Testing:**
- `test_cli_basic_invocation`
- `test_cli_help_message`
- `test_cli_error_handling`

---

## Task Group 12: Documentation

### Task 12.1 — Create Comprehensive README

**Related Spec:** Section 35  
**Related Stories:** All  
**Files to Create:**
- `README.md`

**Content:**
- Problem statement
- Solution overview
- Architecture diagram (ASCII or reference to SPEC)
- LangGraph workflow summary
- Sample data overview
- Installation instructions
- Usage examples
- Testing instructions
- Known limitations
- Future LLM integration path
- Contributing guidelines

---

### Task 12.2 — Add Docstrings to All Functions

**Related Spec:** Throughout  
**All Python files**

**Approach:**
- Module-level docstring
- Function docstrings (Args, Returns, Raises)
- Class docstrings
- Inline comments for complex logic

---

## Summary of Files to Create/Modify

**Total new files:** ~60  
**Total lines of code:** ~3,000-4,000  
**Test lines:** ~2,000-3,000  

### Core Application
- `src/maintenance_agent/` (package)
- `src/maintenance_agent/models.py`
- `src/maintenance_agent/state.py`
- `src/maintenance_agent/config.py`
- `src/maintenance_agent/__main__.py`
- `src/maintenance_agent/cli.py`
- `src/maintenance_agent/graph.py`

### Ingestion
- `src/maintenance_agent/ingestion/parser_registry.py`
- `src/maintenance_agent/ingestion/csv_parser.py`
- `src/maintenance_agent/ingestion/json_parser.py`
- `src/maintenance_agent/ingestion/text_parser.py`
- `src/maintenance_agent/ingestion/discoverer.py`
- `src/maintenance_agent/ingestion/validator.py`

### Normalization
- `src/maintenance_agent/normalization/normalizer.py`
- `src/maintenance_agent/normalization/vendor_mappings.py`
- `src/maintenance_agent/normalization/units.py`

### Analysis
- `src/maintenance_agent/analysis/anomaly_detection.py`
- `src/maintenance_agent/analysis/statistical_anomalies.py`
- `src/maintenance_agent/analysis/failure_analysis.py`
- `src/maintenance_agent/analysis/pattern_analysis.py`
- `src/maintenance_agent/analysis/dashboard_analysis.py`
- `src/maintenance_agent/analysis/metrics.py`

### Nodes
- `src/maintenance_agent/nodes/ingestion_nodes.py`
- `src/maintenance_agent/nodes/normalization_nodes.py`
- `src/maintenance_agent/nodes/analysis_nodes.py`
- `src/maintenance_agent/nodes/reporting_nodes.py`

### Reporting
- `src/maintenance_agent/reporting/json_reporter.py`
- `src/maintenance_agent/reporting/markdown_reporter.py`
- `src/maintenance_agent/reporting/writer.py`

### Integrations (Future)
- `src/maintenance_agent/integrations/ai.py`

### Tests
- `tests/test_*.py` (~15 test files)
- `tests/conftest.py`

### Sample Data
- `sample_data/machines.csv`
- `sample_data/vendor_a_telemetry.csv`
- `sample_data/vendor_b_export.json`
- `sample_data/maintenance_log.txt`
- `sample_data/maintenance_contract.csv`
- `sample_data/dashboard_status.csv`
- `sample_data/graphs/*.png` (optional)

### Configuration & Project Files
- `pyproject.toml`
- `.gitignore`
- `README.md`

---

## Execution Order

Follow the task groups in this order:
1. Project Setup (1.0-1.1)
2. Data Models (2.0-2.3)
3. Ingestion & Parsing (3.0-3.5)
4. Normalization (4.0-4.3)
5. Validation (5.0-5.1)
6. Analysis (6.0-6.7)
7. LangGraph (7.0-7.2)
8. Reporting (8.0-8.3)
9. Sample Data (9.0-9.7)
10. Testing (10.0-10.6)
11. CLI & Entry Point (11.0-11.1)
12. Documentation (12.0-12.2)

---

## Definition of Done

For this implementation prompt to be complete:
- [ ] All task groups executed
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Sample data generated
- [ ] End-to-end workflow runs: `python -m maintenance_agent analyze sample_data`
- [ ] Output files created: `outputs/analysis.json`, `outputs/report.md`
- [ ] Findings are derived from sample data (not hard-coded)
- [ ] README explains all aspects
- [ ] No external APIs called
- [ ] All local execution verified

