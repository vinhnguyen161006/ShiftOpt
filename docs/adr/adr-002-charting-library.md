# ADR-002: Thư viện biểu đồ frontend

Ngày: 2026-10-21 (chốt 2026-10-28)
Trạng thái: Đã chốt — không dùng thư viện biểu đồ

## Các lựa chọn đã xét

| Thư viện | Ưu | Nhược |
|----------|-----|-------|
| Recharts | API React tự nhiên, phổ biến | Bundle lớn hơn |
| Chart.js + react-chartjs-2 | Nhẹ, canvas | API kém React hơn |
| Visx (Airbnb) | Linh hoạt, D3 | Cấu hình phức tạp |
| Tự vẽ bằng HTML/CSS và SVG | Không thêm dependency, khớp trang chủ | Phải tự làm tooltip và bảng thay thế |

## Quyết định

Tự vẽ bằng HTML/CSS và SVG, không thêm thư viện.

Lý do:

- Trang chủ (chuẩn thiết kế, CLAUDE.md mục 8.3) đã vẽ coverage chart bằng cột CSS và đường `z(lambda)` bằng SVG. Dùng thư viện sẽ phải ghi đè style của nó để khớp, đi ngược quy tắc "không đưa style của nguồn vào".
- Ba biểu đồ cần có hình học đơn giản: cột 24 giờ có vạch nhu cầu, heatmap 7 × 24 ô, đường 6 điểm. Không cần trục thời gian liên tục, zoom hay animation.
- CLAUDE.md mục 10 yêu cầu hỏi trước khi thêm dependency; không có nhu cầu đủ lớn để thêm.

Hệ quả: tooltip dùng `title` theo ô hoặc cột, mỗi biểu đồ có bảng số liệu thay thế (`<details>`) cho người đọc màn hình và để kiểm tra số.
