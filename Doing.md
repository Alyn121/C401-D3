# Nhật ký thực hiện Lab - EdTech Agent Observability

Dưới đây là tiến độ thực hiện lab theo các bước trong README.md.

## 1. Khởi tạo dữ liệu giả lập (Mock Data)
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã tạo `data/sample_queries.jsonl` với các tình huống sinh viên nộp bài luận, hỏi đáp toán học và chính sách phúc khảo.
    - Đã cài cắm các dữ liệu PII (MSSV, Tên, Số điện thoại, Email) để kiểm tra tính năng bảo vệ dữ liệu.
    - Đã tạo `data/expected_answers.jsonl` với các từ khóa mong đợi.

## 2. Triển khai Correlation IDs
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã triển khai Middleware để tự động xóa context cũ, tạo ID duy nhất (`req-xxxx`) và gắn vào Response Headers.

## 3. Làm giàu nhật ký (Enrich Logs)
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã cấu hình `bind_contextvars` trong endpoint `/chat` để tự động đính kèm `user_id_hash`, `session_id`, `feature`, và `model` vào mọi dòng log phát sinh trong request.

## 4. Bảo mật dữ liệu (PII Redaction)
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã bổ sung Regex để nhận diện Mã số sinh viên (MSSV), số điện thoại VN, và các từ khóa địa chỉ tiếng Việt.
    - Đã kích hoạt `scrub_event` processor trong hệ thống structlog.

## 5. Truy vết (Tracing)
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã gắn `@observe` vào các thành phần chủ chốt: `LabAgent.run` (Trace), `FakeLLM.generate` (Generation), và `retrieve` (Span).
    - Dữ liệu truy vết đã bao gồm metadata về số lượng tài liệu tìm thấy và preview câu hỏi.

## 6. Chỉ số (Metrics)
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã kiểm tra và đảm bảo `app/metrics.py` thu thập đầy đủ các chỉ số: Traffic, Latency (P50/P95/P99), Cost, Tokens và đặc biệt là Quality Score cho bài luận.

## 7. Cảnh báo (Alerting)
- **Trạng thái**: Hoàn hành ✅
- **Chi tiết**: 
    - Đã bổ sung các quy tắc cảnh báo đặc thù cho EdTech: Cảnh báo khi chất lượng chấm điểm giảm sút (`low_grading_quality`) và khi Vector Store gặp lỗi hệ thống.

## 8. Tổng kết
- **Trạng thái**: Hoàn thành ✅
- **Chi tiết**: 
    - Đã hoàn thành toàn bộ hệ thống quan sát cho EdTech Agent.
    - Sẵn sàng demo và thu thập bằng chứng.
