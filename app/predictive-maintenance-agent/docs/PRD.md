# Product Requirements Document
## Local Manufacturing Maintenance Analysis Agent

**Version:** 1.0  
**Date:** September 2026  
**Status:** Phase 1 Prototype  

---

## 1. Executive Summary

This prototype addresses a critical manufacturing problem: unplanned machine stoppages occurring approximately **once every two days** across a Tier-2 automotive component manufacturer's plant, resulting in an estimated **$10M average business impact**.

The solution is a **local, deterministic analysis agent** that combines heterogeneous machine telemetry, maintenance records, and dashboard metrics to identify failure patterns and pre-failure warning signals **without requiring external AI APIs or cloud connectivity**.

The prototype operates within a **10-week delivery window** to support an OEM supplier scorecard due in Q4 2026.

---

## 2. Problem Statement

### Current Situation
- **60+ CNC and injection-moulding machines** across two plants
- Machines experiencing **unplanned failures approximately every 2 days**
- Maintenance handled through **third-party annual contract** with checklist-based servicing
- Last major maintenance ~6 months ago
- **No centrally structured maintenance records** (plain English, mixed calculations)
- Heterogeneous data formats (CSV telemetry, JSON exports, text logs, dashboard metrics, graphs)
- Approximately **20% of older machines have no telemetry**
- **Air-gapped plant network** (no cloud, no external APIs)

### Business Impact
- **Current baseline:** ~$10M average reported stoppage impact
- **Working target:** Reduce impact toward $5M
- **OEM requirement:** Quarterly supplier scorecard with uptime information

### Root Challenge
The highest-risk assumption is: **Does the existing telemetry and maintenance history contain repeatable signals that appear before failures?**

This prototype must test this assumption as its primary objective.

---

## 3. Product Goal

Allow **plant personnel** (Plant Head, Maintenance Supervisor, Automation Engineer, Shift Operator) to:

1. **Provide heterogeneous machine and maintenance data** from multiple vendors and formats
2. **Receive consolidated analysis** showing:
   - Machine health status
   - Downtime frequency and duration
   - Failure frequency and patterns
   - Complete maintenance history
   - Abnormal measurements and threshold violations
   - Conditions occurring **before failures**
   - **Possible contributing factors** (with confidence levels)
   - Data quality issues and gaps
   - Machines lacking sufficient telemetry

3. **Make informed maintenance decisions** by understanding:
   - Which machines are at risk
   - What signals precede failures
   - How often those signals occur
   - How maintenance interventions affect outcomes

### Critical Distinction
The application must clearly separate:
- **Observed evidence** (facts extracted from data)
- **Possible root-cause candidates** (correlations, patterns, hypotheses)
- **Confirmed root causes** (statistical proof is NOT claimed in this release)

**This application provides correlation analysis only, NOT causal proof.**

---

## 4. Primary Users

### Plant Head
- Needs: Executive summary of breakdown frequency, downtime cost, uptime metrics for OEM scorecard
- Question: "What is our current machine uptime? How many stoppages do we have?"

### Maintenance Supervisor
- Needs: Which machines fail most frequently, maintenance history, what was repaired and when
- Question: "What maintenance patterns do we see? Are recently serviced machines more reliable?"

### Automation Engineer
- Needs: Pre-failure signals, abnormal measurements, conditions before breakdowns
- Question: "What telemetry changes before a machine fails?"

### Shift Operator
- Needs: Current machine status, early warning signals, instructions for escalation
- Question: "Why did this machine stop? Could we have seen it coming?"

---

## 5. Key Features

### 5.1 Data Ingestion
- **Supported formats (v1):** CSV, JSON, TXT
- **Extensible architecture:** Future support for PDF, images, PLC exports without rewriting analysis
- **Unsupported files:** Catalogued and clearly reported (no crash)
- **Format detection:** Automatic or user-assisted
- **Vendor tolerance:** Different field names, schemas, units (°C vs °F, bar vs psi)

### 5.2 Data Normalization
- **Common machine schema:** Normalized representation across vendors
- **Missing data handling:** Explicit representation (MISSING, null) never fabricated
- **Field mapping:** Vendor-specific fields mapped to standard schema where applicable
- **Schema evolution:** New vendor formats can be added via adapter registration

### 5.3 Maintenance Record Analysis
- **Structured extraction** from unstructured text using regex, keyword matching
- **Machine ID extraction:** Locate and standardize machine identifiers
- **Timestamp parsing:** Convert various date/time formats
- **Downtime calculation:** Extract hours, support arithmetic expressions (`3.4 + 2.1 hours`)
- **Observations:** Capture technician notes, part replacements, observations
- **Safe arithmetic:** Evaluate simple expressions without unrestricted `eval()`

### 5.4 Deterministic Analysis (No LLM)
- **Threshold detection:** Identify measurements exceeding safe operating ranges
- **Statistical anomaly detection:** Z-score, IQR-based methods on available telemetry
- **Pre-failure window analysis:** Compare telemetry in N hours before failure vs. normal operation
- **Pattern identification:** Recurring conditions before failures
- **Dashboard RED correlation:** How often RED states precede failures vs. false alarms
- **Downtime aggregation:** Total downtime by machine, frequency trends
- **Maintenance impact:** Before/after analysis (observed, not causal)
- **Data completeness:** Flag machines with insufficient data

### 5.5 Reporting
- **Structured output:** JSON for programmatic access
- **Human-readable report:** Markdown with sections for summary, findings, caveats
- **Evidence-based:** Every claim includes supporting numbers (e.g., "8 of 10 failures")
- **Confidence classification:** Strong candidate, moderate candidate, weak signal
- **Limitation transparency:** Clear statements about what cannot be concluded

### 5.6 Local Execution
- **Zero external dependencies:** No cloud, no API calls, no external models
- **Deterministic:** Same dataset → same output every run
- **Offline:** Works on air-gapped networks
- **Portable:** Python, no special infrastructure

---

## 6. Data Model Overview

### Machine Inventory
```
machine_id        (e.g., "CNC-004", "IMM-002")
machine_type      (CNC, Injection Moulding, Assembly, etc.)
vendor            (e.g., FANUC, Haas, Engel)
plant             (Plant A, Plant B)
commissioned_year (e.g., 2018)
telemetry_available (true/false)
criticality       (high/medium/low)
last_maintenance_date
```

### Machine Telemetry Event
```
machine_id, timestamp, spindle_temp, pressure, vibration, 
motor_current, spindle_load, cycle_time, error_code, 
dashboard_status, source_file
```

### Maintenance Event
```
maintenance_id, machine_id, timestamp, maintenance_type,
description, technician, parts_replaced, downtime_hours,
observations, source_file
```

### Machine Failure Record
```
failure_id, machine_id, timestamp, observed_duration,
last_known_good_time, telemetry_before_failure,
maintenance_history_before_failure
```

---

## 7. Constraints & Scope

### What We ARE Building
✅ Local analysis agent  
✅ Multi-format data ingestion  
✅ Vendor normalization  
✅ Deterministic analysis (no models)  
✅ Pre-failure signal detection  
✅ Maintenance pattern analysis  
✅ Structured + human-readable output  
✅ Extensible parser architecture  
✅ Local execution, zero external dependencies  

### What We ARE NOT Building (v1)
❌ Production ML/statistical models  
❌ LLM integration (Claude, OpenAI, etc.)  
❌ Image semantic interpretation  
❌ Automated machine shutdown  
❌ PLC control  
❌ Automatic maintenance scheduling  
❌ Complete CMMS integration  
❌ Cloud infrastructure  
❌ Cross-plant deployment  
❌ Sensor retrofits  
❌ Guaranteed predictive accuracy claims  

### Future Extensibility
The architecture is designed to add these capabilities later by:
- Injecting new `ReasoningProvider` implementations
- Registering new format parsers without rewriting analysis
- Adding image/document analysis adapters
- Integrating external data sources when network access is available

---

## 8. Success Criteria

The prototype succeeds when:

1. **Data ingestion** works across CSV, JSON, TXT formats with vendor variations
2. **Maintenance records** extract machine IDs, timestamps, downtime, observations from plain text
3. **Telemetry analysis** identifies measurements that change consistently before failures
4. **Pre-failure window** shows candidate warning signals with supporting evidence
5. **Downtime metrics** accurately summarize machine stoppages
6. **Dashboard RED correlation** shows frequency of RED states before/after failures
7. **Report generation** provides actionable insights with clear caveats
8. **Local execution** requires no external APIs, cloud, or internet
9. **Deterministic output** produces reproducible results
10. **Handles incomplete data** gracefully (missing telemetry, no failures recorded)

---

## 9. Delivery Timeline

| Phase | Milestone | Target Date |
|-------|-----------|-------------|
| Documentation | PRD, SPEC, Stories, Acceptance Criteria | Week 1 |
| Synthetic Data | Sample datasets representing real scenarios | Week 2 |
| Core Pipeline | Ingestion, normalization, analysis | Week 3-4 |
| Reporting | JSON output, Markdown report | Week 5 |
| Testing | Unit, integration, end-to-end tests | Week 6 |
| UI (Optional) | Local Streamlit interface if scope permits | Week 7 |
| Refinement | Performance, edge cases, documentation | Week 8-10 |
| **OEM Scorecard** | **Supplier uptime data ready** | **Week 10** |

---

## 10. Out-of-Scope Assumptions for v1

This prototype assumes:
- Existing telemetry contains useful pre-failure signals
- Dashboard RED indicators correlate (imperfectly) with failures
- Data from different vendors can be normalized sufficiently
- Enough telemetry-enabled machines exist for analysis
- Maintenance records contain sufficient information
- The plant can provide representative sample data for development

**Risk**: If no repeatable patterns exist in the data, the prototype will discover and report this finding, which is valuable for product roadmap decisions.

---

## 11. Acceptance Gate

Prototype is accepted when:

- [ ] All user stories have passing acceptance tests
- [ ] Synthetic sample data demonstrates the workflow
- [ ] Analysis produces findings that derive from actual data (not hard-coded)
- [ ] Report clearly distinguishes observed facts from candidate hypotheses
- [ ] README explains architecture, usage, limitations, and future LLM integration path
- [ ] All automated tests pass
- [ ] Application runs offline without external dependencies
