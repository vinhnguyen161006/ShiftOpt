# Nghiệm thu bản đầu

Đối chiếu từng dòng của CLAUDE.md mục 13 với bằng chứng. Cập nhật lần cuối: 2026-11-05. Máy và phiên bản: xem [benchmarks.md](benchmarks.md). Trạng thái: **Đạt** nghĩa là bằng chứng chạy lại được; **Đạt có điều kiện** là đạt ở phạm vi đã đo, cần nhóm xác nhận; **Sai lệch** cần nhóm chấp nhận bằng văn bản; **Chờ** cần người duyệt.

| # | Tiêu chí | Kết quả bắt buộc | Trạng thái | Bằng chứng |
|---|---|---|---|---|
| 1 | Ràng buộc cứng | 0 vi phạm, xác nhận bởi `validation.py` | **Đạt** | 18/18 lần giải trong [benchmarks.md](benchmarks.md) mục 3: `violations = 0`. Kịch bản store 18 mục 4: 0 vi phạm. Job giải `hard_violations = 0` trong `smoke_flow`. |
| 2 | Phủ nhu cầu | Coverage ≥ 98% ở kịch bản cơ sở | **Đạt có điều kiện** | Kịch bản cơ sở (store 18, 30 nhân viên, D13): coverage 1,0000 ở 3/3 seed ([benchmarks.md](benchmarks.md) mục 4). Kịch bản này dư sức chứa (468 giờ-người nhu cầu, 1440 sức chứa), nên không chứng minh được coverage khi thiếu người. Kịch bản căng (8 nhân viên) cho coverage 0,703, `FEASIBLE`, gap 1,0. Nhóm cần xác nhận D13 là kịch bản cơ sở và chấp nhận giới hạn này. |
| 3 | Hiệu năng | 20–40 nhân viên, giải ≤ 60 s, gap ≤ 1% | **Đạt** | 18/18 `OPTIMAL`, gap 0, wall tối đa 31,5 s (1 worker) và 25,9 s (8 worker). Lệnh: `run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60`. Chỉ 9 instance × 2 cấu hình. |
| 4 | So sánh solver | CP-SAT và HiGHS trên cùng instance, có bảng | **Sai lệch** | Bảng có trong [benchmarks.md](benchmarks.md) mục 2, cùng mô hình phủ tập có nghỉ ngầm, 3 instance, cả hai `OPTIMAL` cùng objective. Mô hình theo nhân viên không có bản HiGHS (D12). Nhóm cần chấp nhận. |
| 5 | Độ nhạy | Đường cong `z(λ)`, λ ∈ [0,8; 1,3]; heatmap chi phí biên theo giờ | **Đạt ở engine; Chờ ở UI** | Engine: `test_default_multipliers_cover_the_range`, `test_cost_curve_is_monotone_in_demand_multiplier`, `test_marginal_cost_matches_hand_example`. API: `demand-sweep` và `staffing-sweep` chạy `succeeded` trong `smoke_flow`. UI: `what_if.png` (chụp tự động 2026-11-07, store 18, 30 nhân viên) có đường cong `z(λ)`, bảng quét `p` ∈ {3, 4, 5} và heatmap chi phí biên, mọi điểm `OPTIMAL`; chưa có người duyệt tay trên trình duyệt. |
| 6 | Pháp lý | Cặp 14h–22h → 06h–14h bị cấm; 22h–06h rồi nghỉ ≥ 24 giờ không vi phạm Đ.111 | **Đạt** | `test_afternoon_then_morning_breaks_rest_rule` (validator), `test_afternoon_then_next_morning_is_never_rostered` (CP-SAT), `test_overnight_shift_then_full_24_hour_rest_is_allowed`, `test_trap_rest_day_with_overnight_shift_is_reported`. Bằng chứng end-to-end: `smoke_flow` sửa tay gây `rest_between_shifts` và giữ nguyên lịch gốc. Lưu ý: nội dung các điều luật chưa đối chiếu nguyên văn ([đặc tả](đặc%20tả.md) mục 4). |
| 7 | Tái lập | Cùng instance + seed + `num_workers = 1` → cùng objective | **Đạt** | `engine/tests/test_reproducibility.py`; `backend/tests/unit/test_reproducibility.py`; `solve_runs` đủ cột nguyên tắc 10. |
| 8 | Coverage engine | ≥ 80% | **Đạt** | `pytest --cov=shiftopt`: 98,21%, 194 test. CI và Makefile chặn dưới 80%. |
| 9 | UI | Nhập nhu cầu → Optimize → lịch, coverage chart, cảnh báo, chi phí; kéo λ thấy đường cong | **Chờ** | `smoke_flow --base-url http://localhost:3000` in `smoke flow passed` (Compose, 2026-11-05). Ảnh chụp các màn trong [acceptance/](acceptance/), giao diện tiếng Việt, chụp tự động bằng Playwright ngày 2026-11-07 trên một stack Compose riêng với dữ liệu demo (`demo.md` mục B: 30 nhân viên, 3 ca 0/8/16 h, store 18 với p = 4): `home`, `demand`, `employees`, `shift_templates`, `schedule`, `schedule_run` (lượt 1: `OPTIMAL`, 3,2 s, 8 worker, phủ 100%, 0 vi phạm), `schedule_violation` (lượt 3, sửa tay ca của E01 thứ Tư, validator báo đúng 1 vi phạm Đ.110), `what_if`. Chưa có người duyệt tay trên trình duyệt. |

## Bằng chứng bổ sung

- Backend trên MySQL 8.4.10 thật (container tạm, 2026-11-05): 102 test pass, 0 skip, gồm integration test.
- Migration: `alembic upgrade head` và `alembic check` sạch trên MySQL 8.4.10 (head `3a7c9e1f2b40`, thêm cột `employees.max_weekly_hours`). `alembic check` chạy cả trên DB của Compose và DB test: "No new upgrade operations detected".
- Restart: job `running` được đánh `failed` với lý do `server restarted` sau `docker compose restart backend` (2026-10-29).
- Giới hạn job: 429 khi đủ `max_pending_jobs`, có test tích hợp `backend/tests/integration/test_job_limits.py`.
- Giờ tối đa riêng theo nhân viên: test tiêm vi phạm ở validator và ràng buộc ở roster (`test_employee_weekly_cap_binds_in_roster`).

## Việc cần nhóm quyết

1. Chấp nhận sai lệch dòng 4 (so sánh solver trên mô hình tổng hợp).
2. Xác nhận kịch bản cơ sở (D13, store 18, 30 nhân viên) và chấp nhận rằng coverage 98% chưa đo khi thiếu người.
3. Duyệt tay UI trên `http://localhost:3000` (dòng 5 và 9), xác nhận ảnh trong `docs/acceptance/`.
4. Duyệt đặc tả [đặc tả.md](đặc%20tả.md), gồm D1–D17 và đối chiếu các điều luật với văn bản gốc.
