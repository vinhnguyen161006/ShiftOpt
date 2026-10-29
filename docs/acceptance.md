# Nghiệm thu bản đầu

Đối chiếu từng dòng của CLAUDE.md mục 13 với bằng chứng. Ngày: 2026-10-29. Máy và phiên bản: xem [benchmarks.md](benchmarks.md). Trạng thái: **Đạt** nghĩa là bằng chứng chạy lại được; **Sai lệch** cần nhóm chấp nhận bằng văn bản; **Chờ** cần người duyệt.

| # | Tiêu chí | Kết quả bắt buộc | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| 1 | Ràng buộc cứng | 0 vi phạm, xác nhận bởi `validation.py` | **Đạt** | 18/18 lần giải trong [benchmarks.md](benchmarks.md) mục 3: `violations = 0`. Job giải hard_violations = 0 trong `smoke_flow` (`backend/scripts/smoke_flow.py`). |
| 2 | Phủ nhu cầu | Coverage ≥ 98% ở kịch bản cơ sở | **Đạt, cần xác nhận kịch bản** | Coverage 1,0000 ở 18/18 lần, không thiếu giờ ([benchmarks.md](benchmarks.md) mục 3). Kịch bản cơ sở là nhu cầu sinh theo seed của `run_roster_scale.py`, do nhóm đặt; nhóm cần xác nhận đây là kịch bản cơ sở. Chưa đo khi thiếu người. |
| 3 | Hiệu năng | 20–40 nhân viên, giải ≤ 60 s, gap ≤ 1% | **Đạt** | 18/18 `OPTIMAL`, gap 0, wall tối đa 31,5 s (1 worker) và 25,9 s (8 worker). Lệnh: `run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60`. Chỉ 9 instance × 2 cấu hình. |
| 4 | So sánh solver | CP-SAT và HiGHS trên cùng instance, có bảng | **Sai lệch** | Bảng có trong [benchmarks.md](benchmarks.md) mục 2, cùng mô hình phủ tập có nghỉ ngầm, 3 instance, cả hai `OPTIMAL` cùng objective. Sai lệch: mô hình theo nhân viên không có bản HiGHS, nên so sánh được thực hiện trên mô hình tổng hợp (quyết định 2026-10-29). Nhóm cần chấp nhận. |
| 5 | Độ nhạy | Đường cong `z(λ)`, λ ∈ [0.8, 1.3]; heatmap chi phí biên theo giờ | **Đạt ở engine; Chờ ở UI** | Engine: `DEFAULT_MULTIPLIERS = (0.8, …, 1.3)` (`test_default_multipliers_cover_the_range`), `z(λ)` không giảm (`test_cost_curve_is_monotone_in_demand_multiplier`), chi phí biên ví dụ tay (`test_marginal_cost_matches_hand_example`). API: `demand-sweep` chạy `succeeded` trong `smoke_flow`. UI (đường cong, heatmap, thanh trượt λ) chưa duyệt trên trình duyệt. |
| 6 | Pháp lý | Cặp 14h–22h → 06h–14h bị cấm; 22h–06h rồi nghỉ ≥ 24 giờ không vi phạm Đ.111 | **Đạt** | `test_afternoon_then_morning_breaks_rest_rule` (validator), `test_afternoon_then_next_morning_is_never_rostered` (CP-SAT không bao giờ xếp cặp này), `test_overnight_shift_then_full_24_hour_rest_is_allowed`, `test_trap_rest_day_with_overnight_shift_is_reported`. Bằng chứng end-to-end: `smoke_flow` sửa tay gây `rest_between_shifts` và giữ nguyên lịch gốc. |
| 7 | Tái lập | Cùng instance + seed + `num_workers = 1` → cùng objective | **Đạt** | `engine/tests/test_reproducibility.py` (roster, HiGHS, CP-SAT: objective và phân công giống nhau qua 3 lần); `backend/tests/unit/test_reproducibility.py` (cùng snapshot và seed qua `solve_snapshot`; `solve_runs` có đủ cột của nguyên tắc 10). |
| 8 | Coverage engine | ≥ 80% | **Đạt** | `pytest --cov=shiftopt` cho 98% tổng, 185 test. CI và Makefile chặn dưới 80% (`--cov-fail-under=80`). |
| 9 | UI | Nhập nhu cầu → Optimize → lịch, coverage chart, cảnh báo, chi phí; kéo λ thấy đường cong | **Chờ** | Luồng API tương đương đã chạy qua Docker Compose: `python -m scripts.smoke_flow --base-url http://localhost:3000` in `smoke flow passed`. Chưa mở trình duyệt; cần người duyệt tay `http://localhost:3000` và lưu ảnh vào `docs/acceptance/`. |

## Bằng chứng bổ sung (mục 7.x và 10.x)

- Restart: job `running` được đánh `failed` với lý do `server restarted` sau `docker compose restart backend` (kiểm trên Compose, 2026-10-29).
- Giới hạn job: 429 khi đủ `max_pending_jobs`, có test tích hợp (`backend/tests/integration/test_job_limits.py`).
- Migration: `alembic upgrade head` và `alembic check` sạch trên MySQL 8.4.10.
- Backend: 77 test pass trên MySQL 8.4.10, không skip.

## Việc cần nhóm quyết

1. Chấp nhận sai lệch dòng 4 (so sánh solver trên mô hình tổng hợp).
2. Xác nhận kịch bản cơ sở của dòng 2.
3. Duyệt tay UI (dòng 5, 9) và lưu ảnh.
