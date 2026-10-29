# Rà soát bảo mật và phụ thuộc

Ngày rà soát: 2026-10-29. Phạm vi: backend, engine, frontend, Docker Compose. Mục 10.3 trong [WORKLOG.md](../WORKLOG.md).

## Kết quả kiểm tự động (máy phát triển)

| Kiểm tra | Lệnh | Kết quả |
|---|---|---|
| Phụ thuộc Python (backend) | `uv run --locked pip-audit` (trong `backend/`) | Không có lỗ hổng đã biết. Gói `shiftopt` (đường dẫn cục bộ) bị bỏ qua vì không có trên PyPI. |
| Phụ thuộc JS (production) | `npm audit --omit=dev` (trong `frontend/`) | 0 lỗ hổng |
| Phụ thuộc Python (engine) | `uvx pip-audit -r` trên `uv export --locked --no-hashes` (trong `engine/`) | Không có lỗ hổng đã biết (28 gói). |
| Quét bí mật | gitleaks | Chỉ chạy trên CI (job `security`); không cài trên máy phát triển |

## Checklist

| Mục | Trạng thái | Ghi chú |
|---|---|---|
| Giới hạn kích thước request | Đạt một phần | CSV nhu cầu tối đa 100 000 ký tự (`MAX_CSV_CHARACTERS`). Nginx: `client_max_body_size 1m`. Lưới 168 ô và danh sách nhân viên đã có giới hạn trong schema Pydantic. |
| CORS | Đạt | Chỉ `GET`, `POST`, `PUT`, `DELETE` và header `Content-Type`. Method khác bị từ chối (400), có test. |
| Giới hạn job đang chạy | Đạt, có giới hạn | `max_pending_jobs = 4` (đếm `queued` và `running` của cả solve và analysis). Trả 429. Đếm rồi mới thêm, không khóa nên có thể vượt nhẹ khi nhiều request đồng thời. Job bị gián đoạn khi khởi động lại được đánh `failed` và trả lại chỗ. Có test. |
| Rate limit theo IP | Không làm | Quyết định của nhóm: không thêm phụ thuộc (slowapi). Chỉ có giới hạn đồng thời. |
| Không lộ stack trace | Đạt | Lỗi không xử lý trả 500 với "Internal Server Error", không có traceback hay tên ngoại lệ. Có test. |
| Lỗi nghiệp vụ | Đạt | Mã và thông điệp rõ ràng qua `AppError`. Không trả chi tiết nội bộ. |
| Bí mật trong mã | Đạt | `.env` nằm trong `.gitignore`. Mật khẩu trong `.env.example` là giá trị mẫu. |
| Image Docker ghim | Đạt | Tag và digest đều ghim (backend, frontend, nginx). Không dùng `latest`. |
| Backend chạy non-root | Đạt | `USER app` trong Dockerfile backend. |
| Frontend (nginx) chạy non-root | **Chưa đạt** | Image `nginx:1.30.5-alpine` chạy master process bằng root theo mặc định. Chờ quyết định của nhóm trước khi đổi image (đổi user cần thay đổi cấu hình nginx và quyền thư mục). |
| Xác thực, phân quyền | Ngoài phạm vi | CLAUDE.md mục 14. Chỉ chạy trong mạng tin cậy. |
| Phiên bản ghim gần nhất | Đạt | Theo CLAUDE.md mục 10: chỉ ghim bản phát hành ≥ 2 tuần tuổi. |

## Việc còn mở

- Chờ quyết định về user của container nginx.
- Chạy job `security` (gitleaks) trên CI sau khi push.
