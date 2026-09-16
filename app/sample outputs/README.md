# Local Manufacturing Predictive Maintenance Analysis Agent

**Version:** 1.0  
**Status:** Phase 1 Prototype  
**Last Updated:** September 2026  

---

## Overview

This is a **local, deterministic analysis tool** for identifying machine failure patterns in manufacturing environments. It combines heterogeneous data (telemetry, maintenance logs, dashboard metrics) to detect pre-failure warning signals **without requiring external APIs, cloud connectivity, or LLM models**.

**Key Features:**
- ✅ Multi-format data ingestion (CSV, JSON, TXT)
- ✅ Vendor-agnostic normalization (FANUC, Haas, Engel, Engel, etc.)
- ✅ Deterministic anomaly detection (thresholds, Z-score, IQR)
- ✅ Pre-failure signal analysis with evidence
- ✅ Maintenance pattern correlation
- ✅ **100% local execution** (no cloud, no external APIs)
- ✅ LangGraph-based workflow orchestration
- ✅ Structured JSON + human-readable Markdown reports

---

## Problem Statement

A Tier-2 automotive manufacturer operates 60+ CNC and injection-moulding machines experiencing:
- **~1 unplanned breakdown every 2 days**
- **~$10M average business impact** per stoppage
- **No systematic pattern analysis** across heterogeneous data sources

### Business Goal
Reduce breakdown frequency and impact by identifying early warning signals from existing machine telemetry, maintenance records, and dashboard metrics.

---

## Architecture

```
input_data/
    ├── vendor_a_telemetry.csv
    ├── vendor_b_export.json
    ├── maintenance_log.txt
    └── dashboard_status.csv
    
         ↓ [LangGraph Workflow]
    
    ┌─────────────────────────────┐
    │ 1. Ingest & Discover Files  │
    │ 2. Detect Format            │
    │ 3. Parse Data               │
    │ 4. Normalize to Common Schema
    │ 5. Validate Data Quality    │
    │ 6. Analyze Telemetry        │
    │ 7. Analyze Maintenance      │
    │ 8. Correlate Events         │
    │ 9. Identify Patterns        │
    │ 10. Calculate Metrics       │
    │ 11. Generate Reports        │
    └─────────────────────────────┘
    
         ↓ [Deterministic Analysis]
    
outputs/
    ├── analysis.json        (structured data)
    └── report.md           (human-readable)
```

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Orchestration** | LangGraph (deterministic StateGraph) |
| **Data Processing** | Pandas, CSV, JSON |
| **Analysis** | Custom Python (thresholds, statistics) |
| **Testing** | pytest |
| **Packaging** | setuptools, pyproject.toml |

### No External Dependencies
- ✅ No cloud services (AWS, Azure, GCP)
- ✅ No LLM APIs (OpenAI, Anthropic, Bedrock)
- ✅ No model downloads
- ✅ No internet required
- ✅ Works on air-gapped networks

---

## Installation

### Requirements
- Python 3.11+
- pip

### Setup

```bash
# Clone or navigate to the project
cd predictive-maintenance-agent

# Install in development mode
pip install -e .

# Install dev dependencies (optional)
pip install -e ".[dev]"
```

### Verify Installation

```bash
# Should print version and help
python -m maintenance_agent analyze --help

# Or if installed as script
maintenance-agent analyze --help
```

---

## Usage

### Basic Analysis

```bash
# Analyze data in a directory
python -m maintenance_agent analyze ./sample_data

# With verbose logging
python -m maintenance_agent analyze ./sample_data --log-level DEBUG

# Specify output directory
python -m maintenance_agent analyze ./sample_data --output-dir ./results
```

### Output Files

After running analysis, check:

**`outputs/analysis.json`** — Machine-readable structured data
```json
{
  "generated_at": "2026-09-15T10:30:00",
  "summary": {
    "total_machines": 13,
    "machines_with_telemetry": 11,
    "failures_identified": 14,
    "total_downtime_hours": 42.3
  },
  "candidate_factors": [
    {
      "factor_name": "Spindle temperature increase",
      "observed_in_failures": 8,
      "total_failures": 10,
      "frequency_percent": 80.0,
      "confidence_level": "Strong"
    }
  ]
}
```

**`outputs/report.md`** — Human-readable summary
```markdown
# Manufacturing Predictive Maintenance Analysis Report

## Executive Summary
- Machines Analyzed: 13
- Failures Identified: 14
- Total Downtime: 42.3 hours

## Candidate Pre-Failure Signals

### Spindle temperature increase
- Observed in: 8/10 failures (80%)
- Confidence: Strong
```

---

## Supported Data Formats

### CSV (Telemetry & Metrics)
```csv
timestamp,machine_id,spindle_temp,vibration_mm_s,motor_current_a,status
2026-01-15T00:00:00,CNC-001,72.5,1.5,25.0,GREEN
2026-01-15T01:00:00,CNC-001,73.2,1.6,25.1,GREEN
```

### JSON (Vendor-Specific Exports)
```json
[
  {
    "recordedAt": "2026-01-15T00:00:00",
    "equipmentCode": "IMM-001",
    "hydPressure_bar": 140.0,
    "cycleDuration_s": 45.2,
    "alarmState": "GREEN"
  }
]
```

### TXT (Maintenance Logs)
```text
12 March 2026, CNC-004.
Machine stopped at 11:15.
Spindle temperature reached 94C.
Bearing replaced.
Downtime = 3.4 hours.
Technician: John Smith.
```

---

## Workflow & Analysis Pipeline

### LangGraph Workflow

```python
START
  ↓
[ingest_files]           - Discover all files in input directory
  ↓
[detect_format]          - Identify parser for each file
  ↓
[parse_data]             - Convert to structured records
  ↓
[normalize_data]         - Map to common schema (handles vendor differences)
  ↓
[validate_data]          - Type checking, logical validation
  ↓
[analyze_telemetry]      - Threshold, Z-score, IQR anomalies
  ↓
[analyze_maintenance]    - Pattern & frequency analysis
  ↓
[correlate_events]       - Link telemetry to failures, maintenance to outcomes
  ↓
[identify_patterns]      - Rank by frequency & confidence
  ↓
[calculate_metrics]      - Downtime, MTBF, uptime summaries
  ↓
[generate_report]        - Create JSON & Markdown outputs
  ↓
END
```

### Deterministic Analysis (No Models)

1. **Threshold Detection**
   - Spindle temp > 90°C (alert), > 100°C (critical)
   - Pressure > 150 bar (alert), > 160 bar (critical)
   - Vibration > 4.0 mm/s (alert), > 5.0 mm/s (critical)

2. **Statistical Anomaly Detection**
   - Z-score (values > 2.5σ from mean)
   - IQR method (values outside Q1-1.5IQR to Q3+1.5IQR)

3. **Pre-Failure Window Analysis**
   - Compare telemetry in N hours before failure (default: 6 hours)
   - Against normal operating telemetry
   - Identify conditions that change consistently

4. **Pattern Frequency**
   - For each anomaly: count failures where it appeared
   - Calculate frequency: anomalies / total_failures
   - Classify: Strong (>60%), Moderate (30-60%), Weak (<30%)

5. **Evidence-Based Reporting**
   - Never claim causation ("Spindle temperature IS the problem")
   - Instead report: "Observed before 8 of 10 failures" with supporting data
   - Clear confidence classifications

---

## Sample Data

The project includes **synthetic but realistic sample data** in `sample_data/`:

```
sample_data/
├── machines.csv              - Machine inventory (13 machines)
├── vendor_a_telemetry.csv    - 60 days hourly telemetry (5 CNC machines, 2 vendors)
├── vendor_b_export.json      - 60 days 5-min intervals (3 Injection Moulding)
├── maintenance_log.txt       - 30+ maintenance records in plain English
├── maintenance_contract.csv  - Third-party maintenance schedule
├── dashboard_status.csv      - Hourly GREEN/AMBER/RED status
└── graphs/                   - Sample graph images (PNG)
```

### Sample Failures (Seeded for Testing)
- **CNC-004**: 7 failures with clear spindle temperature precursor
- **IMM-002**: 4 failures with hydraulic pressure drop pattern
- **CNC-007**: 3 failures with weak/no precursor signals

Analysis should identify strong signals for CNC-004 & IMM-002, weak signals for CNC-007.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/maintenance_agent --cov-report=html

# Run specific test
pytest tests/test_core.py::TestCSVParser -v
```

### Test Coverage

- ✅ Parser tests (CSV, JSON, TXT)
- ✅ Normalization tests (vendor mapping)
- ✅ Anomaly detection tests (thresholds, Z-score, IQR)
- ✅ Metrics calculation tests
- ✅ End-to-end workflow tests

---

## Key Limitations

### What This Tool CAN Do
✅ Identify **correlation patterns** in telemetry before failures  
✅ Rank conditions by frequency and confidence  
✅ Detect threshold violations and statistical anomalies  
✅ Aggregate downtime and maintenance history  
✅ Flag data quality issues  
✅ Run **completely offline** on air-gapped networks  

### What This Tool CANNOT Do
❌ Prove **causation** (correlation ≠ causation)  
❌ Predict **exact failure times**  
❌ Handle 100% missing telemetry (needs data to analyze)  
❌ Automatically control machines or schedule maintenance  
❌ Guarantee accuracy without validation by maintenance team  

### Data Requirements
- Minimum 3 machines with telemetry for meaningful patterns
- Minimum 6 hours of pre-failure telemetry for pattern detection
- Machines without telemetry are flagged but don't block analysis

---

## Future Enhancements (v2+)

### AI/LLM Integration
The architecture is designed to **inject AI reasoning later** without rewriting ingestion/analysis:

```python
# v1: Deterministic
reasoning = RuleBasedReasoningProvider()
insights = reasoning.analyze(context)

# v2+: With LLM (Claude, GPT-4, etc.)
reasoning = AIReasoningProvider(model="claude-3")
insights = reasoning.analyze(context)  # Same interface
```

### New Data Formats
- PDF extraction (maintenance manuals, reports)
- Image analysis (graph screenshots, equipment photos)
- PLC historian exports
- Cloud data sources (when network available)

### Machine Learning
- Predictive models (once patterns validated)
- Anomaly detection (isolation forests, autoencoders)
- Time-series forecasting
- Supervised models trained on validated root causes

### User Interface
- Web dashboard (Flask/FastAPI)
- Interactive Streamlit UI
- Mobile app
- Real-time alerts

### Deployment
- Docker containerization
- Kubernetes orchestration (if needed)
- Cloud sync (optional, with local-first mode default)
- Multi-plant aggregation

---

## Configuration

Edit `src/maintenance_agent/config.py` to customize:

```python
@dataclass
class AnalysisConfig:
    pre_failure_window_hours: int = 6          # How far back to look
    zscore_threshold: float = 2.5              # Statistical threshold
    strong_pattern_threshold: float = 0.60     # > 60% confidence
    temperature_alert_celsius: float = 90.0    # Alert threshold
    # ... more settings
```

---

## Troubleshooting

### "No parser for file"
- Check file extension (.csv, .json, .txt)
- Use correct format for your data type
- Unsupported formats are logged but don't stop analysis

### "No data points for analysis"
- Ensure input directory path is correct
- Verify files are readable
- Check that machines.csv exists (machine inventory)

### "Insufficient telemetry for machine X"
- This is expected for ~20% of machines in typical plants
- Analysis continues with available data
- Machines without telemetry are clearly marked in reports

### Slow performance
- Current implementation designed for <20 machines, 6-month datasets
- For larger datasets, consider:
  - Filtering by machine or date range
  - Running analysis per plant
  - Optimizing in future releases

---

## Understanding the Reports

### Confidence Levels

| Level | Criteria | Interpretation |
|-------|----------|-----------------|
| **Strong** | > 60% of failures | Highly repeatable signal, strong candidate |
| **Moderate** | 30-60% of failures | Worth investigating further |
| **Weak** | < 30% of failures | Insufficient evidence, needs validation |
| **Insufficient Data** | < 3 failure examples | Not enough data for pattern |

### Evidence-Based Claims

❌ **Wrong:** "Spindle temperature is the root cause"  
✅ **Right:** "Spindle temperature increased before 8/10 failures (median 93 min lead time)"

This tool provides **observed patterns**, not **causal proof**. Validation by maintenance team is essential.

---

## Project Structure

```
predictive-maintenance-agent/
├── README.md                          (this file)
├── pyproject.toml                     (dependencies, metadata)
├── .gitignore
│
├── docs/
│   ├── PRD.md                         (product requirements)
│   ├── SPEC.md                        (technical specification)
│   ├── STORIES.md                     (user stories)
│   ├── ACCEPTANCE_CRITERIA.md
│   └── IMPLEMENTATION_PROMPT.md
│
├── sample_data/
│   ├── machines.csv
│   ├── vendor_a_telemetry.csv
│   ├── vendor_b_export.json
│   ├── maintenance_log.txt
│   ├── maintenance_contract.csv
│   ├── dashboard_status.csv
│   └── graphs/
│
├── src/maintenance_agent/
│   ├── __init__.py
│   ├── __main__.py                    (CLI entry point)
│   ├── cli.py                         (command-line interface)
│   ├── config.py                      (configuration)
│   ├── state.py                       (LangGraph state)
│   ├── models.py                      (data models)
│   ├── core.py                        (parsers, normalization, analysis)
│   ├── graph.py                       (LangGraph workflow)
│   │
│   ├── ingestion/
│   ├── normalization/
│   ├── analysis/
│   ├── reporting/
│   ├── nodes/
│   └── integrations/
│       └── ai.py                      (future LLM integration)
│
├── outputs/
│   ├── analysis.json                  (generated)
│   └── report.md                      (generated)
│
└── tests/
    ├── __init__.py
    ├── test_core.py                   (parser, normalization, analysis tests)
    └── conftest.py                    (pytest fixtures)
```

---

## Contributing

### Adding Support for New Machine Vendors

1. Add vendor mapping to `VENDOR_MAPPINGS` in `core.py`:
```python
VENDOR_MAPPINGS = {
    'vendor_new': {
        'field_in_vendor_data': 'common_schema_field',
        # ...
    }
}
```

2. Create test data with new vendor format

3. Test normalization: `pytest tests/test_core.py::TestNormalization`

### Adding New Analysis Algorithms

1. Add function to `core.py` or new module in `analysis/`
2. Create unit tests
3. Call function from appropriate graph node
4. Document in report generation

---

## References

- **Problem Frame:** See `docs/PRD.md` for business context
- **Architecture:** See `docs/SPEC.md` for technical design
- **Requirements:** See `docs/STORIES.md` and `docs/ACCEPTANCE_CRITERIA.md`
- **Implementation:** See `docs/IMPLEMENTATION_PROMPT.md`

---

## License

MIT License (see LICENSE file for details)

---

## Questions?

This prototype was built following Spec-Driven Development (SDD):
1. PRD (product requirements)
2. SPEC (technical specification)
3. User Stories
4. Acceptance Criteria
5. Implementation Prompt
6. Code & Tests

All documentation is in the `docs/` directory. Start there for comprehensive understanding of design decisions, assumptions, and roadmap.

---

**Generated:** September 2026  
**Version:** 1.0  
**Status:** Phase 1 - Local Deterministic Prototype
