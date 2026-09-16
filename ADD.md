| Section                                | Decision / Summary                                                                                                                                                |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1. Problem & success criteria**      | Machines break down about every 2 days, causing major losses. Success = fewer stoppages, better uptime visibility, and useful early-warning signals.              |
| **2. Workflow or agent?**              | **Workflow.** Steps are predictable: ingest → normalize → analyze → report. AI agent can be added later.                                                          |
| **3. Agent inventory**                 | **Ingestion**, **Normalization**, **Analysis**, **Reporting**. All deterministic in V1; future AI reasoning agent optional.                                       |
| **4. Orchestration pattern**           | **Sequential LangGraph workflow:** Input → Parse → Normalize → Analyze → Correlate → Report.                                                                      |
| **5. Reasoning approach**              | Rule-based analysis in V1. Future AI can use plan-and-execute/ReAct with max 3 iterations.                                                                        |
| **6. Tools & integrations**            | Python, LangGraph, Pandas, Pydantic, local filesystem. No cloud/API dependency.                                                                                   |
| **7. Data sources & knowledge**        | CSV, JSON, unstructured maintenance logs, dashboard data, telemetry, graphs. ~20% machines have no telemetry.                                                     |
| **8. Memory design**                   | Short-term workflow state in LangGraph. Future long-term storage for historical failures/patterns.                                                                |
| **9. Framework decision**              | **Python + LangGraph** for stateful workflows and easy future AI integration.                                                                                     |
| **10. Model strategy**                 | **No LLM in V1.** Future: small/mid model for text interpretation; larger model only for complex cases.                                                           |
| **11. Guardrails & HITL**              | Never fabricate missing data; correlation ≠ root cause; no direct PLC/machine control; maintenance supervisor validates recommendations.                          |
| **12. Failure handling**               | Continue with valid files if one fails; max 2 retries; flag unsupported/corrupt data and escalate when needed.                                                    |
| **13. Observability & evaluation**     | Log files processed, anomalies, failures, latency, false alerts, data completeness, and future model cost.                                                        |
| **14. Volume & usage assumptions**     | Pilot: 5–10 users, 5–20 requests/day, future 2–4 LLM calls/request, ~10K input + 1.5K output tokens/call.                                                         |
| **15. Open risks & pending decisions** | Risk: weak predictive signals, incomplete maintenance history, false dashboard alerts. Need machine selection, telemetry details, and success target from client. |

### Simple Architecture

**Data Sources → Ingestion → Normalization → Analysis → Pattern Detection → Report → Human Review**
