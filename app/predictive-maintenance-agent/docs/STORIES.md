# User Stories & Acceptance Criteria
## Local Manufacturing Maintenance Analysis Agent

---

## Story 1: Data Ingestion from Multiple Vendors

**Title:** Ingest heterogeneous machine data from different vendors without manual conversion

**As a** Maintenance Engineer  
**I want to** provide machine data in CSV, JSON, and text formats from different vendors  
**So that** I can analyze the plant without manually converting every dataset to a standard format  

### Acceptance Criteria

**GIVEN** CSV files with telemetry data (e.g., timestamp, machine_id, spindle_temp)  
**WHEN** I run the agent on a directory containing these files  
**THEN** the files are recognized, parsed, and converted into internal records  
**AND** no manual schema conversion is required  

**GIVEN** JSON exports with different vendor field names (e.g., equipmentCode vs machine_id)  
**WHEN** the agent processes the JSON files  
**THEN** different vendor schemas are automatically detected and mapped  
**AND** a common machine record is created  

**GIVEN** a text file with plain-English maintenance notes  
**WHEN** the parser processes the file  
**THEN** machine IDs, timestamps, and downtime are extracted  
**AND** unstructured observations are preserved for later review  

**GIVEN** an unsupported file type (e.g., .png, .exe)  
**WHEN** the agent encounters the file  
**THEN** the file is catalogued with status UNSUPPORTED  
**AND** processing continues without crash  
**AND** a report note indicates the file could not be analyzed  

**GIVEN** a malformed CSV (e.g., missing columns, invalid JSON syntax)  
**WHEN** parsing begins  
**THEN** useful validation errors are produced  
**AND** other valid files in the same directory continue processing  

---

## Story 2: Normalize Vendor-Specific Data Formats

**Title:** Normalize data from different machine vendors into a common schema

**As an** Automation Engineer  
**I want to** use telemetry data from FANUC, Haas, Engel and other vendors together  
**So that** I can compare machines and identify patterns across vendor types  

### Acceptance Criteria

**GIVEN** telemetry from Vendor A using fields (spindle_temp, vibration_mm_s, motor_current_a)  
**AND** telemetry from Vendor B using fields (hydPressure_bar, cycleDuration_s, equipmentCode)  
**WHEN** normalization occurs  
**THEN** both are mapped into a common schema with fields like (spindle_temperature, pressure, vibration, machine_id)  
**AND** the mapping is reversible (vendor fields remain in metadata)  

**GIVEN** a machine field that does not map to the common schema  
**WHEN** normalization occurs  
**THEN** the field is preserved in vendor_fields dictionary  
**AND** the analysis continues using common fields  

**GIVEN** temperature data in Fahrenheit from one vendor and Celsius from another  
**WHEN** normalization occurs  
**THEN** all temperatures are converted to Celsius  
**AND** the original units are noted in metadata  

**GIVEN** missing sensor readings (e.g., no vibration sensor on machine X)  
**WHEN** normalization occurs  
**THEN** the field remains None/null  
**AND** no fabricated sensor value is created  

**GIVEN** the same raw dataset  
**WHEN** normalization is run twice  
**THEN** the output is identical both times (deterministic)  

---

## Story 3: Extract Maintenance Information from Unstructured Records

**Title:** Parse plain-English maintenance logs and extract key information

**As a** Maintenance Supervisor  
**I want to** analyze historical maintenance notes even though they're written in different formats  
**So that** I can correlate maintenance actions with machine reliability  

### Acceptance Criteria

**GIVEN** a maintenance record like "12 March 2026, CNC-004. Bearing replaced. Downtime = 3.4 hours."  
**WHEN** the text parser processes it  
**THEN** machine_id (CNC-004), timestamp (12 March 2026), downtime_hours (3.4), parts_replaced (bearing) are extracted  

**GIVEN** a record with arithmetic expressions like "Downtime = 1.5 + 0.75 hours" or "Change = (142 - 117) / 142 × 100"  
**WHEN** the parser evaluates expressions  
**THEN** safe arithmetic is computed (no unrestricted eval())  
**AND** the result is stored (e.g., downtime_hours = 2.25, pressure_change_percent = 17.6)  

**GIVEN** a record with multiple timestamps or ambiguous date formats  
**WHEN** parsing occurs  
**THEN** the most likely date is extracted  
**AND** confidence and ambiguity are noted in a parsing_notes field  

**GIVEN** a record missing optional fields (e.g., no technician name listed)  
**WHEN** parsing occurs  
**THEN** known fields are extracted  
**AND** missing fields remain null  
**AND** parsing does not fail  

**GIVEN** a partial or corrupted maintenance record  
**WHEN** extraction is attempted  
**THEN** extractable information is captured  
**AND** the record is flagged for review  

---

## Story 4: Analyze Machine Failure Patterns

**Title:** Compare telemetry before failures against normal operation

**As an** Automation Engineer  
**I want to** see what measurements change before a machine fails  
**So that** I can identify early warning signals  

### Acceptance Criteria

**GIVEN** a known machine failure at timestamp T  
**WHEN** pre-failure analysis runs  
**THEN** telemetry from the N hours (default 6) before time T is extracted  
**AND** this is compared against telemetry from normal operating periods  

**GIVEN** telemetry comparison for a failing machine  
**WHEN** analysis occurs  
**THEN** mean, standard deviation, and percentage change for each field are calculated  
**AND** anomalies (temperature spikes, pressure drops) in the pre-failure window are identified  

**GIVEN** multiple failures of the same machine  
**WHEN** pattern analysis runs  
**THEN** conditions are compared across failures  
**AND** recurring signals (e.g., temperature always rises before failure) are flagged  

**GIVEN** a failure with weak or no detectable precursor signals  
**WHEN** analysis completes  
**THEN** this finding is reported accurately  
**AND** the machine is NOT marked as having a "strong" warning signal if evidence is weak  

**GIVEN** insufficient telemetry before a failure (e.g., first event is the failure)  
**WHEN** analysis occurs  
**THEN** the record is flagged as "insufficient pre-failure data"  
**AND** analysis continues for other failures  

---

## Story 5: Summarize Downtime and Breakdown Frequency

**Title:** Provide executive summary of machine reliability metrics

**As a** Plant Head  
**I want to** understand total downtime, breakdown frequency, and impact  
**So that** I can communicate machine uptime to the OEM customer  

### Acceptance Criteria

**GIVEN** failure records from all machines  
**WHEN** metrics are calculated  
**THEN** total downtime hours, average downtime per incident, and incidents per week are computed  

**GIVEN** a cost per production hour  
**WHEN** downtime metrics are calculated  
**THEN** estimated impact can be computed (optional, if input provided)  

**GIVEN** machines with and without recent maintenance  
**WHEN** downtime is analyzed  
**THEN** machines are ranked by downtime  
**AND** time since last maintenance is noted for each  

**GIVEN** the same failure dataset  
**WHEN** metrics are calculated twice  
**THEN** the results are identical  

**GIVEN** no failures recorded for a time period  
**WHEN** metrics are calculated  
**THEN** downtime = 0 and frequency = 0 are reported accurately  

---

## Story 6: Identify and Report Data Quality Issues

**Title:** Clearly identify missing or incomplete data

**As a** Project Owner  
**I want to** see which machines have insufficient data  
**So that** predictive decisions are not based on fabricated information  

### Acceptance Criteria

**GIVEN** a machine with no telemetry sensors  
**WHEN** analysis runs  
**THEN** the machine is marked as "telemetry_unavailable"  
**AND** it is NOT included in pre-failure signal analysis  

**GIVEN** a machine with 30% of expected telemetry values missing  
**WHEN** analysis occurs  
**THEN** data completeness is calculated  
**AND** the machine is flagged as "incomplete data (30% missing)"  

**GIVEN** maintenance records with missing timestamps  
**WHEN** analysis runs  
**THEN** records without dates are flagged  
**AND** they are either excluded or noted in the analysis with lower confidence  

**GIVEN** unsupported file types (e.g., .png, .pdf)  
**WHEN** ingestion completes  
**THEN** these files are listed in the report  
**AND** a note indicates "Image interpretation requires future enhancement"  

**GIVEN** a dataset with all data quality issues  
**WHEN** the report is generated  
**THEN** a complete list of issues appears in a "Data Quality" section  
**AND** recommendations for data improvement are included  

---

## Story 7: Ensure Local Execution Without External Dependencies

**Title:** Guarantee that analysis runs completely locally with no external API calls

**As the** Plant Security Owner  
**I want to** ensure all analysis happens on the plant network  
**So that** plant-floor information never leaves the secured environment  

### Acceptance Criteria

**GIVEN** an air-gapped network with no internet connectivity  
**WHEN** the agent runs  
**THEN** all core functionality works without external API calls  
**AND** no data is transmitted externally  

**GIVEN** the application running on a machine without cloud connectivity  
**WHEN** analysis executes  
**THEN** no errors about missing cloud services occur  
**AND** all outputs are generated locally  

**GIVEN** dependencies like pandas, numpy, Python standard library  
**WHEN** installation happens  
**THEN** only local Python packages are required  
**AND** no model downloads or API key requests are needed  

**GIVEN** a request to integrate AI/LLM capabilities in the future  
**WHEN** that integration is implemented  
**THEN** it is optional via configuration  
**AND** the application still works in offline mode if LLM is unavailable  

---

## Story 8: Support Future AI/LLM Integration Without Rewriting

**Title:** Design reasoning layer for future LLM integration

**As a** Developer  
**I want to** inject AI reasoning later without rewriting the ingestion and analysis pipeline  
**So that** we can upgrade intelligence as capabilities become available  

### Acceptance Criteria

**GIVEN** a ReasoningProvider interface/protocol  
**WHEN** the application is implemented  
**THEN** deterministic analysis uses RuleBasedReasoningProvider  
**AND** a placeholder AIReasoningProvider exists that raises NotImplementedError  

**GIVEN** future LLM availability  
**WHEN** an AIReasoningProvider is implemented  
**THEN** the provider can be swapped via configuration  
**AND** no changes to ingestion, normalization, or analysis are required  

**GIVEN** the current implementation with deterministic reasoning  
**WHEN** AI is later added  
**THEN** the application continues working with deterministic reasoning if the AI provider is unavailable  

**GIVEN** existing analysis output  
**WHEN** AI reasoning is added  
**THEN** it enhances the analysis output without removing deterministic findings  

---

## Story 9: Support New Data Formats Without Rewriting Analysis

**Title:** Design extensible parser architecture for future formats

**As a** Developer  
**I want to** add support for new file formats (PDF, images, PLC exports)  
**So that** the application can ingest more data sources as they become available  

### Acceptance Criteria

**GIVEN** the ParserRegistry with CSV, JSON, TXT parsers  
**WHEN** a new format is needed  
**THEN** a new parser class is created  
**AND** registered in the registry  
**AND** the analysis pipeline is unchanged  

**GIVEN** multiple parsers  
**WHEN** file ingestion runs  
**THEN** the appropriate parser is selected automatically  
**AND** unsupported formats are identified and catalogued  

**GIVEN** a future image parser for graph interpretation  
**WHEN** it is added  
**THEN** graph images are processed without changing the ingestion or analysis layers  

---

## Story 10: Generate Clear, Evidence-Based Reports

**Title:** Produce reports that explain findings with supporting evidence

**As a** Maintenance Supervisor  
**I want to** see not just "spindle temperature is a risk"  
**So that** I understand how confident we should be and what the evidence shows  

### Acceptance Criteria

**GIVEN** analysis results including candidate factors  
**WHEN** the report is generated  
**THEN** each finding includes:
- Number of failures analyzed
- How many had the condition
- Percentage frequency
- Median lead time before failure
- Examples (machine IDs, dates)
- Confidence classification (Strong/Moderate/Weak)
- False positive rate

**GIVEN** a weak signal (occurs in < 30% of failures)  
**WHEN** reported  
**THEN** it is classified as "Weak candidate" or "Requires further validation"  
**AND** it is NOT presented as a strong indicator  

**GIVEN** a strong signal (> 60% of failures)  
**WHEN** reported  
**THEN** it is classified as "Strong candidate"  
**AND** supporting evidence is clearly documented  

**GIVEN** correlation analysis  
**WHEN** reported  
**THEN** clear statements appear such as:
- "This analysis shows correlation only, not proof of root cause"
- "Other factors may contribute"
- "Maintenance team validation is recommended"

