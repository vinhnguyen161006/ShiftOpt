# Kịch bản demo ShiftOpt

Cập nhật: 2026-11-05. Dùng dữ liệu có sẵn, không cần internet sau khi đã tải dữ liệu FreshRetailNet.

## Chuẩn bị

1. `cp .env.example .env` và đặt mật khẩu DB trong `.env`.
2. `docker compose up -d --build`. Chờ `backend` ở trạng thái `healthy`. UI: `http://localhost:3000`.
3. Nếu DB đã có dữ liệu từ lần chạy trước, các lần smoke tạo thêm 25 nhân viên mỗi lần. Khi tổng đạt `max_employees` (200), smoke flow báo `at most 200 employees are allowed`. Cách sạch là làm rỗng DB bằng `docker compose down -v` rồi `up -d`. Lệnh này xóa dữ liệu trong volume; chỉ chạy khi không cần giữ dữ liệu.

## Kịch bản (khoảng 10 phút)

| Bước | Thao tác trên UI | Điều cần thấy | Ghi chú |
|---|---|---|---|
| 1 | Trang **Demand**: tạo profile từ FreshRetailNet store 18 | Tham số `alpha`, `p`, sàn hiển thị; nhãn "doanh số chuẩn hóa, không phải dữ liệu nhân sự" | Nguyên tắc 6 |
| 2 | Trang **Employees**: thêm vài nhân viên; một người có giờ tối đa riêng (ví dụ 24) | Cột "Max hours/week" | Giờ tối đa không vượt luật 48 |
| 3 | Trang **Shift templates**: xem ba mẫu ca 0h, 8h, 16h | Ca 8 giờ, không có cảnh báo | Thử thêm một ca 10 giờ: kiểm xem có cảnh báo vượt 8 giờ không (chưa xác nhận) |
| 4 | Trang **Schedule**: chọn profile, mẫu ca, nhân viên, bấm **Optimize** | Trạng thái, gap, thời gian giải; `OPTIMAL` chỉ khi chứng minh được | Store 18, 30 nhân viên giải trong khoảng 12–20 giây |
| 5 | Xem lịch, biểu đồ coverage, chi phí | Giờ thiếu hiện rõ trên biểu đồ; 0 vi phạm cứng | Kịch bản cơ sở đủ người |
| 6 | Trang **Compliance** / sửa tay: đặt một nhân viên làm ca 14h–22h rồi 06h–14h | Cảnh báo Đ.110 (nghỉ 8 giờ) hiện ngay; lịch gốc giữ nguyên | Đây là ca bị cấm |
| 7 | Trang **What-if**: chạy **Run demand sweep** | Đường cong `z(λ)` cho λ 0,8–1,3; điểm không `OPTIMAL` có dấu riêng | Nhãn xấp xỉ cho dual LP |
| 8 | Trang **What-if**: chạy **Run assumption sweep** với `alpha` | Bảng chi phí theo giá trị giả định; nhãn "không phải dữ liệu nhân sự" | Cần profile FreshRetailNet |
| 9 | Xuất CSV lịch và KPI | File tải về có tiêu đề cột | |

## Bản dự phòng

Nếu solver chậm hoặc máy không ổn định, dùng ảnh trong [acceptance/](acceptance/): `schedule_run.png` (kết quả lịch), `what_if.png` (màn What-if). Ảnh được chụp bằng Playwright 1.55.0 trên Compose ngày 2026-11-05.

## Kiểm nhanh không cần trình duyệt

```
cd backend
uv run --locked python -m scripts.smoke_flow --base-url http://localhost:3000
```

In `smoke flow passed` khi luồng API đạt: tạo profile, Optimize, poll job, KPI, sửa tay bị cảnh báo, sweep chạy `succeeded`.

## Trạng thái chạy thử

- Smoke flow: đạt trên Compose trong lần chạy đầu của ngày 2026-11-05.
- **Chưa đạt tiêu chí "hai lần liên tiếp".** Lần chạy thứ hai sau đó thất bại vì DB đã đủ 200 nhân viên từ các lần smoke trước. Khắc phục là làm rỗng DB (mục Chuẩn bị, bước 3). Lệnh đó chưa được thực hiện.
- Chưa duyệt các bước 1–9 bằng trình duyệt thật. Người duyệt cần làm theo bảng trên và ghi kết quả vào [acceptance.md](acceptance.md).
