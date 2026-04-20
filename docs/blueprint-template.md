# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: C401_D3
- [REPO_URL]: https://github.com/Alyn121/C401-D3.git
- [MEMBERS]:
  - Member A: Nguyễn Quốc Khánh_2A202600200, Lý Quốc An _2A202600123 | Role: Logging & PII
  - Member B: Lưu Quang Lực_2A202600121, Đinh Văn Thư_2A202600035 | Role: Tracing & Enrichment
  - Member C: Nguyễn Phương Nam _ 2A202600194  | Role: SLO & Alerts
  - Member D: Nguyễn Bá Khánh_2A202600135 | Role: Load Test & Dashboard , frontend 
  - Member E: Lưu Thị Ngọc Quỳnh_2A202600122, Nguyễn Quang Minh_2A202600195   | Role: Demo & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]:100/100
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 

Total log records analyzed: 391
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 199
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: ![alt text](image.png)
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: ![alt text](image-1.png)
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: ![alt text](image-2.png)
- [TRACE_WATERFALL_EXPLANATION]: (Briefly explain one interesting span in your trace)

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: [Path to image]
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | ~160ms | 28d | ~158ms |
| Error Rate | < 2% | 28d | ~7.5% (Breached) |
| Cost Budget | < $2.5/day | 1d | ~$0.30 |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: [Path to image]
- [SAMPLE_RUNBOOK_LINK]: [docs/alerts.md#L...]

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: tool_fail (Knowledge Base Outage)
- [SYMPTOMS_OBSERVED]: Error Rate tăng vọt lên mức ~7.5%, bảng điều khiển "Error Distribution" chuyển sang trạng thái BREACH. Nhiều yêu cầu kiểm thử trả về lỗi HTTP 500.
- [ROOT_CAUSE_PROVED_BY]: Log hệ thống ghi nhận `error_type: RuntimeError` kèm thông báo `Knowledge base retriever timeout — vector store unreachable` trong quá trình truy xuất dữ liệu (RAG).
- [FIX_ACTION]: Gọi API `/incidents/tool_fail/disable` để tắt giả lập sự cố, khôi phục khả năng truy cập vào Knowledge Base.
- [PREVENTIVE_MEASURE]: Triển khai Circuit Breaker cho dịch vụ RAG, thiết lập cơ chế fallback (trả về kiến thức mặc định) khi vector store không phản hồi, và bổ sung cảnh báo (Alert) khi Error Rate vượt quá 2%.
---

## 5. Individual Contributions & Evidence

### [MEMBER_A_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_C_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_D_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

### [MEMBER_E_NAME]
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: 

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
