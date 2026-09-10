# Acceptance Criteria & Test Specifications

---

## AC-1: Multi-Format Data Ingestion

### Criteria
```gherkin
GIVEN CSV files with telemetry data
WHEN the agent runs on a directory
THEN all CSV files are discovered and parsed
  AND each row is converted to a structured record
  AND timestamps are parsed correctly
  AND numeric fields are preserved as numbers

GIVEN JSON files with nested structures
WHEN parsing occurs
THEN JSON objects are flattened appropriately
  AND arrays of objects are handled (one record per object)
  AND parsing errors are caught and reported
  AND other files continue processing

GIVEN TXT files with plain-English maintenance notes
WHEN the parser processes them
THEN machine IDs are extracted via regex
  AND timestamps are parsed in multiple formats
  AND downtime values are extracted
  AND partial extraction succeeds even if some fields missing

GIVEN an unsupported file type (e.g., .exe, .png)
WHEN file discovery occurs
THEN the file is catalogued with status UNSUPPORTED_FORMAT
  AND processing continues
  AND no crash or exception halts the pipeline
  AND the file is reported in the output
```

### Test Cases
- `test_csv_parse_valid_data`
- `test_json_parse_nested_objects`
- `test_txt_parse_maintenance_records`
- `test_unsupported_file_handling`
- `test_mixed_formats_in_single_directory`
- `test_malformed_csv_partial_recovery`
- `test_invalid_json_error_reporting`

---

## AC-2: Vendor Schema Normalization

### Criteria
```gherkin
GIVEN telemetry from Vendor A with fields (spindle_temp, vibration_mm_s)
AND telemetry from Vendor B with fields (hydPressure_bar, cycleDuration_s)
WHEN normalization runs
THEN both datasets are mapped to common schema fields
  AND field mappings are accurately applied
  AND unmapped fields are preserved in metadata
  AND vendor_fields dictionary retains originals

GIVEN temperature in Fahrenheit from one source and Celsius from another
WHEN normalization occurs
THEN all are converted to Celsius
  AND original units are noted
  AND conversion formulas are accurate

GIVEN pressure in bar vs. psi vs. Pa
WHEN normalization occurs
THEN all are converted to bar
  AND conversion is accurate
  AND original units are preserved in metadata

GIVEN machines with different field names for the same concept
WHEN vendor mapping is applied
THEN the correct mapping is used
  AND no data is duplicated or lost
  AND mapping is testable via configuration
```

### Test Cases
- `test_vendor_a_to_common_schema`
- `test_vendor_b_to_common_schema`
- `test_temperature_unit_conversion_fahrenheit_to_celsius`
- `test_pressure_unit_conversion_multiple_units`
- `test_unmapped_fields_preserved`
- `test_normalization_deterministic`

---

## AC-3: Maintenance Record Text Extraction

### Criteria
```gherkin
GIVEN a record: "12 March 2026, CNC-004. Bearing replaced. Downtime = 3.4 hours."
WHEN the parser processes it
THEN machine_id = "CNC-004"
  AND timestamp = 2026-03-12
  AND downtime_hours = 3.4
  AND parts_replaced includes "bearing"

GIVEN a record with arithmetic: "Downtime = 1.5 + 0.75 hours"
WHEN parsing occurs
THEN downtime_hours = 2.25 is calculated
  AND evaluation is safe (no unrestricted eval())
  AND simple +, -, *, / operations are supported

GIVEN a record with percentage calculation: "Change = (142 - 117) / 142 × 100"
WHEN parsing occurs
THEN result = 17.6 is calculated
  AND no exceptions occur
  AND result is stored

GIVEN a record with missing optional fields
WHEN extraction occurs
THEN required fields are extracted
  AND optional fields remain None/null
  AND parsing does not fail

GIVEN multiple date formats (DD/MM/YYYY, YYYY-MM-DD, text months)
WHEN parsing occurs
THEN all are correctly identified and normalized
  AND ambiguous dates are flagged
```

### Test Cases
- `test_maintenance_text_basic_extraction`
- `test_maintenance_date_parsing_multiple_formats`
- `test_maintenance_arithmetic_addition`
- `test_maintenance_arithmetic_percentage`
- `test_maintenance_parts_extraction`
- `test_maintenance_missing_fields_handling`
- `test_maintenance_partial_extraction`

---

## AC-4: Anomaly Detection

### Criteria
```gherkin
GIVEN telemetry with threshold violations
WHEN anomaly detection runs
THEN measurements exceeding defined thresholds are flagged
  AND threshold values are configurable
  AND severity levels are assigned (alert, critical)

GIVEN numeric telemetry data for a machine
WHEN Z-score anomaly detection runs
THEN mean and standard deviation are computed
  AND values > 2.5σ from mean are flagged
  AND machines with insufficient data are handled gracefully
  AND results are deterministic

GIVEN numeric telemetry for a machine
WHEN IQR anomaly detection runs
THEN Q1, Q3, IQR are computed
  AND outliers outside 1.5*IQR boundaries are identified
  AND results are consistent across runs
```

### Test Cases
- `test_threshold_violation_detection`
- `test_zscore_anomaly_detection`
- `test_zscore_with_insufficient_data`
- `test_iqr_anomaly_detection`
- `test_anomaly_detection_deterministic`

---

## AC-5: Pre-Failure Window Analysis

### Criteria
```gherkin
GIVEN a known failure at timestamp T
WHEN pre-failure analysis runs
THEN telemetry from N hours before T is extracted
  AND "normal" telemetry (non-failure periods) is extracted
  AND pre-failure and normal telemetry are compared
  AND mean, std, percent change calculated for each field

GIVEN failure telemetry with anomalies
WHEN analysis occurs
THEN anomalies present in pre-failure window are identified
  AND timing of anomalies relative to failure is recorded
  AND anomaly is compared against normal periods

GIVEN multiple failures of the same machine
WHEN pattern analysis runs
THEN patterns recurring before multiple failures are noted
  AND confidence is based on frequency
  AND inconsistent patterns are flagged as weak
```

### Test Cases
- `test_pre_failure_window_extraction`
- `test_pre_failure_vs_normal_comparison`
- `test_multi_failure_pattern_analysis`
- `test_insufficient_pre_failure_data_handling`

---

## AC-6: Dashboard RED State Correlation

### Criteria
```gherkin
GIVEN failures and their timestamps
WHEN dashboard correlation analysis runs
THEN count of failures preceded by RED state is recorded
  AND count of RED states NOT followed by failure is counted
  AND sensitivity (% of failures with prior RED) is calculated
  AND false positive rate (RED with no failure) is calculated

GIVEN RED states across all machines
WHEN analysis occurs
THEN frequency of RED before failures is reported
  AND machines with most RED alerts are identified
  AND lead time (RED → failure) is calculated
```

### Test Cases
- `test_dashboard_red_correlation_sensitivity`
- `test_dashboard_red_false_positive_rate`
- `test_dashboard_red_lead_time_calculation`

---

## AC-7: Downtime Metrics Calculation

### Criteria
```gherkin
GIVEN failure records with duration
WHEN downtime metrics are calculated
THEN total downtime hours is accurate
  AND average per incident is correct
  AND incidents per week is computed
  AND machines are ranked by downtime

GIVEN machines with no recorded failures
WHEN metrics are calculated
THEN downtime = 0 is reported correctly
  AND frequency = 0 is reported correctly

GIVEN a cost per hour (optional)
WHEN metrics are calculated
THEN estimated impact can be computed if provided
```

### Test Cases
- `test_downtime_total_calculation`
- `test_downtime_per_incident_average`
- `test_incident_frequency_calculation`
- `test_no_failures_downtime_zero`
- `test_machine_ranking_by_downtime`

---

## AC-8: Data Completeness Reporting

### Criteria
```gherkin
GIVEN a machine with complete telemetry
WHEN data quality analysis runs
THEN completeness = 100% is reported

GIVEN a machine with 70% of expected fields
WHEN data quality runs
THEN completeness = 70% is calculated
  AND machine is flagged as "incomplete"

GIVEN a machine with no telemetry
WHEN analysis occurs
THEN machine is marked "telemetry_unavailable"
  AND it is excluded from pre-failure signal analysis
  AND this decision is noted in report

GIVEN unsupported files in the dataset
WHEN report is generated
THEN list of unsupported files appears in data quality section
```

### Test Cases
- `test_data_completeness_calculation`
- `test_machine_without_telemetry_flagging`
- `test_unsupported_file_reporting`

---

## AC-9: Candidate Factor Confidence Classification

### Criteria
```gherkin
GIVEN an anomaly observed in 80% of failures
WHEN confidence classification runs
THEN factor is marked "Strong candidate"
  AND reason is documented (>60% threshold)

GIVEN an anomaly in 45% of failures
WHEN classification occurs
THEN factor is marked "Moderate candidate"
  AND reason is documented (30-60% range)

GIVEN an anomaly in 15% of failures
WHEN classification occurs
THEN factor is marked "Weak signal"
  AND recommendation for further validation appears

GIVEN a very small sample (e.g., 2 failures total)
WHEN classification occurs
THEN low sample size is noted
  AND confidence is explicitly marked as limited
```

### Test Cases
- `test_strong_candidate_classification`
- `test_moderate_candidate_classification`
- `test_weak_signal_classification`
- `test_small_sample_size_handling`

---

## AC-10: Report Generation

### Criteria
```gherkin
GIVEN completed analysis
WHEN report generation runs
THEN JSON output is produced at outputs/analysis.json
  AND Markdown output is produced at outputs/report.md
  AND JSON contains machine-readable data
  AND Markdown is human-readable with sections and examples

GIVEN candidate factors
WHEN report is generated
THEN each factor includes:
  - Number of failures where observed
  - Frequency percentage
  - Median lead time
  - Supporting evidence (machine IDs, dates)
  - Confidence classification
  - False positive rate

GIVEN data quality issues
WHEN report is generated
THEN "Data Quality" section lists:
  - Machines with insufficient telemetry
  - Files not supported for analysis
  - Data completeness per machine
  - Recommendations for improvement

GIVEN the analysis
WHEN report is generated
THEN "Limitations" section includes:
  - "Correlation ≠ Causation"
  - Sample size and time period
  - Excluded machines/data
  - Confidence levels
```

### Test Cases
- `test_json_report_generation`
- `test_markdown_report_generation`
- `test_report_completeness`
- `test_report_evidence_inclusion`

---

## AC-11: Deterministic Output

### Criteria
```gherkin
GIVEN the same input dataset
WHEN analysis is run twice
THEN all outputs are identical
  AND no randomness in algorithms
  AND same JSON, same Markdown

GIVEN different run dates/times
WHEN analysis is run
THEN output is identical except for metadata timestamps
  AND core findings are unchanged
```

### Test Cases
- `test_deterministic_analysis_runs`
- `test_identical_outputs_same_input`

---

## AC-12: Local Execution (No External Dependencies)

### Criteria
```gherkin
GIVEN an air-gapped network
WHEN the application runs
THEN no external API calls are made
  AND no cloud connectivity required
  AND all core functionality works locally

GIVEN missing network connectivity
WHEN analysis executes
THEN no timeouts or network errors occur
  AND analysis completes successfully
```

### Test Cases
- `test_no_external_api_calls`
- `test_offline_execution`

---

## AC-13: LangGraph Workflow Integration

### Criteria
```gherkin
GIVEN analysis inputs (data paths)
WHEN LangGraph workflow executes
THEN each node runs in sequence
  AND state is passed correctly between nodes
  AND errors in one node are logged but don't halt pipeline
  AND final state contains all analysis results

GIVEN complex analysis
WHEN workflow runs
THEN execution completes successfully
  AND all intermediate states are available
  AND type checking is enforced on state dict
```

### Test Cases
- `test_langgraph_node_execution_sequence`
- `test_state_passing_between_nodes`
- `test_error_recovery_in_nodes`

---

## AC-14: Error Handling & Recovery

### Criteria
```gherkin
GIVEN one malformed file in a directory of good files
WHEN ingestion runs
THEN error is logged
  AND good files continue processing
  AND analysis includes data from good files
  AND error is reported in final report

GIVEN a failure with insufficient pre-failure data
WHEN analysis occurs
THEN failure is flagged as "insufficient pre-failure telemetry"
  AND analysis continues for other failures
```

### Test Cases
- `test_malformed_file_recovery`
- `test_insufficient_data_graceful_handling`

---

## AC-15: End-to-End Workflow

### Criteria
```gherkin
GIVEN sample_data/ directory with:
  - vendor_a_telemetry.csv
  - vendor_b_export.json
  - maintenance_log.txt
  - machines.csv
  - dashboard_status.csv

WHEN python -m maintenance_agent analyze sample_data/ runs

THEN:
  - All files are discovered and categorized
  - Each is parsed into normalized records
  - Analysis identifies failures, anomalies, patterns
  - Candidate pre-failure signals are ranked
  - Report is generated at outputs/analysis.json
  - Report is generated at outputs/report.md
  - Findings are derived from actual data (not hard-coded)
  - All findings are reproducible
  - Execution completes < 30 seconds
```

### Test Cases
- `test_end_to_end_full_pipeline`
- `test_output_file_creation`
- `test_finding_accuracy_against_sample_data`

