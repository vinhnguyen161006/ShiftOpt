# Số đo benchmark

Mọi số trong file này chạy lại được bằng lệnh ghi bên dưới. Kết luận chỉ áp cho instance, time limit, seed và số worker đã ghi (CLAUDE.md nguyên tắc 5). Không trích số của nhóm khác như số của ShiftOpt.

Máy đo: Windows 10 (10.0.26200), 16 luồng CPU, Python 3.11.14, OR-Tools 9.15.6755, PuLP 3.3.2, ngày 2026-10-29.

## 1. Curtois & Qu (2014), Instance1–5

Nguồn: https://www.schedulingbenchmarks.org/nrp/ (trang tổng hợp, xem 2026-10-29). Trang ghi giá trị cận dưới và nghiệm tốt nhất là cùng một số in đậm, tức đã chứng minh tối ưu. Dữ liệu không có giấy phép ghi trên trang nên không commit; `engine/benchmarks/download_curtois_qu.py` tải về `data/benchmarks/curtois_qu/` và kiểm SHA-256 ghim trong script.

Mô hình: `shiftopt.benchmarks.curtois_qu.solve_benchmark`, CP-SAT, công thức theo định dạng công bố (ca theo ngày, phủ thừa và thiếu theo từng ngày-ca, nguyện vọng ca bật/tắt, ca cấm nối, giới hạn cuối tuần, nghỉ tối thiểu liên tiếp ở biên chân trời được miễn).

Lệnh:

```
cd engine
uv run --locked python benchmarks/run_curtois_qu.py --time-limit 120 --workers 1 --seed 0
uv run --locked python benchmarks/run_curtois_qu.py --time-limit 120 --workers 8 --seed 0
```

Cột `gap_to_published` = objective − giá trị công bố (dương là kém hơn). `status = optimal` nghĩa là đã chứng minh.

### 1a. 1 worker (tái lập được với cùng seed)

| Instance | Công bố | Objective | Cận dưới | Gap tới công bố | Status | Wall (s) |
|---|---|---|---|---|---|---|
| Instance1 | 607 | 607 | 607 | 0 | optimal | 0,52 |
| Instance2 | 828 | 828 | 219 | 0 | feasible | 120,00 |
| Instance3 | 1001 | 1122 | 206 | +121 | feasible | 120,01 |
| Instance4 | 1716 | 2346 | 200 | +630 | feasible | 120,01 |
| Instance5 | 1143 | 2070 | 4 | +927 | feasible | 120,01 |

### 1b. 8 worker (không tái lập tuyệt đối do song song)

| Instance | Công bố | Objective | Cận dưới | Gap tới công bố | Status | Wall (s) |
|---|---|---|---|---|---|---|
| Instance1 | 607 | 607 | 607 | 0 | optimal | 0,22 |
| Instance2 | 828 | 828 | 828 | 0 | optimal | 4,68 |
| Instance3 | 1001 | 1001 | 1001 | 0 | optimal | 6,35 |
| Instance4 | 1716 | 1716 | 1602 | 0 | feasible | 120,07 |
| Instance5 | 1143 | 1148 | 1017 | +5 | feasible | 120,06 |

### Kết luận trong phạm vi đã đo

- Với 8 worker và 120 giây, mô hình CP-SAT đạt đúng tối ưu công bố ở Instance1–3 và chứng minh được.
- Instance4 đạt công bố nhưng chưa chứng minh (cận dưới 1602).
- Instance5 còn cách công bố 5 đơn vị, chưa chứng minh.
- Với 1 worker chỉ Instance1 được chứng minh trong 120 giây. Kết quả phụ thuộc số worker, không chỉ thuật toán.
- Đây là 5 instance và 1 seed. Không suy ra cho instance khác.

## 2. So sánh CP-SAT và HiGHS trên cùng mô hình

Cùng mô hình phủ tập có nghỉ ngầm (`shiftopt.models.implicit_breaks` cho HiGHS qua PuLP, `shiftopt.models.implicit_breaks_cpsat` cho CP-SAT), cùng dữ liệu, cùng seed 0, `num_workers = 1`, `relative_gap_limit = 0`. Không dùng số Mittelmann.

Lệnh: `cd engine && uv run --locked python benchmarks/compare_solvers.py`

| Instance | Solver | Time limit (s) | Status | Objective | Cận dưới | Wall (s) |
|---|---|---|---|---|---|---|
| uniform_3_shifts | HiGHS | 10 | optimal | 3 696 000 | 3 696 000 | 0,01 |
| uniform_3_shifts | CP-SAT | 10 | optimal | 3 696 000 | 3 696 000 | 0,03 |
| uniform_3_shifts | HiGHS | 60 | optimal | 3 696 000 | 3 696 000 | 0,02 |
| uniform_3_shifts | CP-SAT | 60 | optimal | 3 696 000 | 3 696 000 | 0,04 |
| peaked_3_shifts | HiGHS | 10 | optimal | 4 256 000 | 4 256 000 | 0,05 |
| peaked_3_shifts | CP-SAT | 10 | optimal | 4 256 000 | 4 256 000 | 0,02 |
| peaked_3_shifts | HiGHS | 60 | optimal | 4 256 000 | 4 256 000 | 0,05 |
| peaked_3_shifts | CP-SAT | 60 | optimal | 4 256 000 | 4 256 000 | 0,02 |
| peaked_spaced_8_shifts | HiGHS | 10 | optimal | 3 570 000 | 3 570 000 | 0,02 |
| peaked_spaced_8_shifts | CP-SAT | 10 | optimal | 3 570 000 | 3 570 000 | 0,03 |
| peaked_spaced_8_shifts | HiGHS | 60 | optimal | 3 570 000 | 3 570 000 | 0,01 |
| peaked_spaced_8_shifts | CP-SAT | 60 | optimal | 3 570 000 | 3 570 000 | 0,03 |

Kết luận trong phạm vi đã đo: 3 instance, cả hai solver chứng minh cùng objective; cả hai đều quá nhanh để phân biệt hiệu năng. Mô hình này nhỏ (không có phân công từng người); không suy ra cho mô hình theo nhân viên (mục 3).

### 2b. Mô hình theo nhân viên: CP-SAT và HiGHS (`roster_mip.py`)

Cùng công thức C1–C8 ([model.md](model.md) mục 2a), cùng tầng lexicographic, cùng seed, `num_workers = 1`, time limit 60 giây cho cả lượt giải (chia đều cho các tầng). Nhu cầu sinh theo `weekly_instance` trong `engine/benchmarks/run_roster_scale.py`.

Lệnh: `cd engine && uv run --locked python -u benchmarks/run_roster_scale.py --solver both --sizes 10 20 30 --seeds 0 1 2 --time-limit 60 --workers 1`

Cột `shortfall` và `chi phí` là giá trị tầng 1 (thiếu người) và tầng 2 (chi phí lương). Cột `objective` là tầng cuối, không dùng để so chi phí giữa các dòng.

| Nhân viên | Seed | Solver | Status | Shortfall (giờ) | Chi phí tầng 2 | Wall (s) |
|---|---|---|---|---|---|---|
| 10 | 0 | CP-SAT | feasible | 28 | 5 148 000 | 26,5 |
| 10 | 0 | HiGHS | optimal | 28 | 5 148 000 | 31,1 |
| 10 | 1 | CP-SAT | feasible | 34 | 5 136 000 | 60,5 |
| 10 | 1 | HiGHS | optimal | 34 | 5 136 000 | 28,6 |
| 10 | 2 | CP-SAT | feasible | 34 | 5 106 000 | 60,5 |
| 10 | 2 | HiGHS | feasible | 34 | 5 106 000 | 29,1 |
| 20 | 0 | CP-SAT | optimal | 0 | 6 352 000 | 17,1 |
| 20 | 0 | HiGHS | optimal | 0 | 6 352 000 | 17,1 |
| 20 | 1 | CP-SAT | optimal | 0 | 6 518 000 | 27,9 |
| 20 | 1 | HiGHS | optimal | 0 | 6 518 000 | 17,6 |
| 20 | 2 | CP-SAT | optimal | 0 | 6 414 000 | 22,2 |
| 20 | 2 | HiGHS | optimal | 0 | 6 414 000 | 18,5 |
| 30 | 0 | CP-SAT | optimal | 0 | 6 352 000 | 23,6 |
| 30 | 0 | HiGHS | optimal | 0 | 6 352 000 | 21,8 |
| 30 | 1 | CP-SAT | optimal | 0 | 6 518 000 | 26,8 |
| 30 | 1 | HiGHS | optimal | 0 | 6 518 000 | 23,2 |
| 30 | 2 | CP-SAT | optimal | 0 | 6 414 000 | 25,4 |
| 30 | 2 | HiGHS | optimal | 0 | 6 414 000 | 26,6 |

Kết luận trong phạm vi đã đo:

- 20 và 30 nhân viên: cả hai solver chứng minh đủ tầng 1 và 2, cùng shortfall và cùng chi phí ở mọi seed. Thời gian 17–28 giây cho cả hai, không khác biệt đáng kể.
- 10 nhân viên khó hơn: nhu cầu đỉnh 3–4 người nhiều hơn số người có sẵn, nên thiếu 28–34 giờ và tầng 2 phải cân nhắc nhiều hơn. CP-SAT không chứng minh được trong 60 giây ở cả 3 seed (chạm giới hạn ở seed 1 và 2). HiGHS chứng minh được 2/3 seed; seed 2 chỉ `FEASIBLE`.
- Nơi cả hai cùng chứng minh hoặc cùng có lời giải, shortfall và chi phí khớp nhau. Không có dòng nào mà solver này cho chi phí thấp hơn solver kia với cùng shortfall.
- Đây là 3 seed, 3 cỡ, 1 worker. Không suy ra cho instance khác. 40 nhân viên không có trong lượt này; xem mục 3a cho CP-SAT ở 40 nhân viên.

### 2c. Kích thước mô hình theo số nhân viên

Đếm biến và ràng buộc của mô hình dựng xong, chưa giải. Lệnh: `cd engine && uv run --locked python -u benchmarks/run_roster_scale.py --sizes-only --sizes 10 20 30 40`

| Nhân viên | Bộ ca | CP-SAT biến | CP-SAT ràng buộc | HiGHS biến | HiGHS ràng buộc |
|---|---|---|---|---|---|
| 10 | 3 ca (0/8/16) | 3 331 | 2 440 | 3 320 | 7 278 |
| 20 | 3 ca | 6 491 | 4 710 | 6 470 | 14 388 |
| 30 | 3 ca | 9 651 | 6 980 | 9 620 | 21 498 |
| 40 | 3 ca | 12 811 | 9 250 | 12 770 | 28 608 |
| 10 | 6 ca (0/4/…/20) | 4 801 | 3 140 | 4 790 | 14 488 |
| 20 | 6 ca | 9 431 | 6 110 | 9 410 | 28 808 |
| 30 | 6 ca | 14 061 | 9 080 | 14 030 | 43 128 |
| 40 | 6 ca | 18 691 | 12 050 | 18 650 | 57 448 |

Số biến của hai mô hình gần như bằng nhau và tăng tuyến tính theo số nhân viên. Số ràng buộc không so trực tiếp được: CP-SAT gộp mỗi cửa sổ 24 giờ nghỉ (C5) thành một ràng buộc có điều kiện cho mỗi `(e, t)`, còn HiGHS viết từng cặp `(x, v)`. Cách viết từng cặp làm số hàng của HiGHS gấp 2–3 lần. Theo lý thuyết, dạng từng cặp chặt hơn ở phép nới lỏng LP; chưa đo riêng ([model.md](model.md) mục 2a).

## 3. Lịch tuần 7×24, 20–40 nhân viên (mục 9.4)

Máy và phiên bản như mục đầu. Nhu cầu: đỉnh 3–4 người ban ngày, nền 1–2 người ban đêm, sinh theo seed (`weekly_instance` trong `engine/benchmarks/run_roster_scale.py`). Phá đối xứng tắt (mặc định). `relative_gap_limit = 0.01`, time limit 60 giây.

Lệnh:

```
cd engine
uv run --locked python -u benchmarks/run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60 --workers 1
uv run --locked python -u benchmarks/run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60 --workers 8
```

### 3a. 1 worker

| Nhân viên | Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng |
|---|---|---|---|---|---|---|---|
| 20 | 0 | optimal | 0.0 | 14.37 | 0 | 1.0000 | 0 |
| 30 | 0 | optimal | 0.0 | 21.38 | 0 | 1.0000 | 0 |
| 40 | 0 | optimal | 0.0 | 31.53 | 0 | 1.0000 | 0 |
| 20 | 1 | optimal | 0.0 | 24.76 | 0 | 1.0000 | 0 |
| 30 | 1 | optimal | 0.0 | 22.56 | 0 | 1.0000 | 0 |
| 40 | 1 | optimal | 0.0 | 27.92 | 0 | 1.0000 | 0 |
| 20 | 2 | optimal | 0.0 | 19.38 | 0 | 1.0000 | 0 |
| 30 | 2 | optimal | 0.0 | 21.13 | 0 | 1.0000 | 0 |
| 40 | 2 | optimal | 0.0 | 29.38 | 0 | 1.0000 | 0 |

### 3b. 8 worker

| Nhân viên | Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng |
|---|---|---|---|---|---|---|---|
| 20 | 0 | optimal | 0.0 | 9.90 | 0 | 1.0000 | 0 |
| 30 | 0 | optimal | 0.0 | 17.40 | 0 | 1.0000 | 0 |
| 40 | 0 | optimal | 0.0 | 25.87 | 0 | 1.0000 | 0 |
| 20 | 1 | optimal | 0.0 | 12.18 | 0 | 1.0000 | 0 |
| 30 | 1 | optimal | 0.0 | 18.99 | 0 | 1.0000 | 0 |
| 40 | 1 | optimal | 0.0 | 25.60 | 0 | 1.0000 | 0 |
| 20 | 2 | optimal | 0.0 | 12.42 | 0 | 1.0000 | 0 |
| 30 | 2 | optimal | 0.0 | 17.18 | 0 | 1.0000 | 0 |
| 40 | 2 | optimal | 0.0 | 22.40 | 0 | 1.0000 | 0 |

### Kết luận trong phạm vi đã đo

- 18/18 lần giải đạt `OPTIMAL` với gap 0, coverage 1,0, không thiếu giờ, 0 vi phạm cứng theo validator. Thời gian tối đa 31,5 s (1 worker) và 25,9 s (8 worker), đều dưới ngưỡng 60 giây.
- Instance này dễ: nhu cầu thấp hơn sức chứa, nên chưa kiểm được coverage ≥ 98% khi thiếu người. Đó là phạm vi chưa đo.
- `objective` là giá trị tầng cuối của lexicographic (vi phạm sở thích), nên bằng 1,0 ở mọi dòng; không so sánh chi phí giữa các dòng qua cột này.
- Cùng seed với `num_workers = 1` cho cùng kết quả (test `test_roster_repeats_objective_and_assignments`). Dòng 8 worker không đảm bảo tái lập.
- 3 seed × 3 cỡ. Không suy ra cho instance khác.

## 4. Kịch bản cơ sở: FreshRetailNet store 18 (CLAUDE §13 dòng 2)

Nhu cầu: `derive_demand` trên `data/demo/train.parquet`, cửa hàng 18 (split train; ô hết hàng đã thay bằng nhu cầu ẩn; giờ 22h–06h đặt sàn đêm). Giả định của nhóm, chưa được duyệt (đặc tả D7–D9): `alpha = 1.0`, `p = 4.0` (chọn để giờ đỉnh cần 8 người), `min_staff = 1`, `night_min_staff = 1`. Ca: 0h, 8h, 16h, mỗi ca 8 giờ. 30 nhân viên, lương 100, không yêu cầu cá nhân. Luật: 48 giờ/tuần, `K = 6`. Time limit 60 giây, gap 0,01, 1 worker, không phá đối xứng.

Lệnh:

```
cd backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 30 --productivity 4 --time-limits 60 --workers 1 --seeds 0 1 2
```

| Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng | Solver |
|---|---|---|---|---|---|---|---|
| 0 | optimal | 0.0 | 19,54 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |
| 1 | optimal | 0.0 | 16,91 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |
| 2 | optimal | 0.0 | 12,03 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |

Kịch bản căng (8 nhân viên, cùng nhu cầu và giả định, sức chứa 384 giờ-người nhỏ hơn 468 giờ-người nhu cầu):

```
cd backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 8 --productivity 4 --time-limits 60 --workers 1 --seeds 0 1 2
```

| Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng |
|---|---|---|---|---|---|---|
| 0 | feasible | 1,0 | 60,26 | 139 | 0,7030 | 0 |
| 1 | feasible | 1,0 | 60,35 | 139 | 0,7030 | 0 |
| 2 | feasible | 1,0 | 60,43 | 139 | 0,7030 | 0 |

Kết quả: không chứng minh được tối ưu trong 60 giây (gap 1,0 ở tầng cuối). Lịch vẫn hợp lệ theo validator. Đây là giới hạn của solver với time limit này, không phải lỗi ràng buộc. Không hạ ràng buộc. Hướng xử lý nếu cần: tăng time limit, bật phân rã hai pha (4.4) để có nghiệm ban đầu, hoặc tăng nhân viên.

Kết luận trong phạm vi đã đo:
- 3/3 `OPTIMAL`, coverage 1,0, 0 vi phạm cứng, mọi lần dưới 60 giây.
- Kịch bản này dư sức chứa: giờ đỉnh cần 8 người, tổng nhu cầu 468 giờ-người mỗi tuần (chưa tính nghỉ giữa giờ), sức chứa 30 × 48 = 1440. Coverage 98% đạt ở đây không chứng minh được khả năng phủ khi thiếu người. Mục 4b đo kịch bản thiếu người.
- Kết quả phụ thuộc `alpha`, `p`, các sàn. Đổi `p` đổi toàn bộ nhu cầu; xem độ nhạy theo giả định (`sweep_staffing_assumption`, mục 8.6).
- 1 store, 3 seed. Không suy ra cho store khác.

### 4b. Coverage khi thiếu người (plan E1, E2)

Cùng nhu cầu và giả định với mục 4, số nhân viên thay đổi. Tỉ lệ sức chứa = số người × 48 giờ / 468 giờ-người nhu cầu. Cận trên coverage = 1 − cận dưới giờ thiếu / 468: solver chứng minh coverage không thể vượt mức này, và chỉ tính khi tầng thiếu người đã được giải (kể cả khi chưa tối ưu).

Lệnh (1 worker, seed 0–2, chế độ exact):

```
cd backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 8 9 10 11 12 13 14 15 16 17 18 --time-limits 60 120 --modes exact --workers 1 --seeds 0 1 2
```

Dữ liệu: `docs/experiments/coverage_capacity.csv` (8–14 người) và `docs/experiments/coverage_capacity_15_18.csv` (15–18 người). Bảng gộp theo số người và giới hạn thời gian:

| Người | Giới hạn (s) | Tỉ lệ sức chứa | Coverage (3 seed) | Tầng thiếu người | Cận trên coverage | Thời gian (s) |
|---|---|---|---|---|---|---|
| 8 | 60 | 0,82 | 0,7009, 0,7030, 0,7051 | feasible | 0,7821 | 56,2–58,2 |
| 8 | 120 | 0,82 | 0,7009, 0,7030, 0,7051 | feasible | 0,7821 | 113,3–115,0 |
| 9 | 60 | 0,92 | 0,7692, 0,7756, 0,7778 | feasible | 0,8248 | 55,9–58,5 |
| 9 | 120 | 0,92 | 0,7714, 0,7756, 0,7778 | feasible | 0,8248 | 112,0–114,3 |
| 10 | 60 | 1,03 | 0,8291, 0,8312 | feasible | 0,8590 | 56,3–56,6 |
| 10 | 120 | 1,03 | 0,8291, 0,8312 | feasible | 0,8590 | 112,0–115,4 |
| 11 | 60 | 1,13 | 0,8697 | feasible | 0,8846 | 55,6–57,1 |
| 11 | 120 | 1,13 | 0,8697 | feasible | 0,8846 | 113,8–115,4 |
| 12 | 60 | 1,23 | 0,9081 | feasible | 0,9103 | 56,4–57,6 |
| 12 | 120 | 1,23 | 0,9081 | feasible | 0,9103 | 110,7–114,1 |
| 13 | 60 | 1,33 | 0,9359 | optimal | 0,9359 | 3,2–3,9 |
| 13 | 120 | 1,33 | 0,9359 | optimal | 0,9359 | 3,2–3,9 |
| 14 | 60 | 1,44 | 0,9615 | optimal | 0,9615 | 7,1–20,6 |
| 14 | 120 | 1,44 | 0,9615 | optimal | 0,9615 | 6,9–40,5 |
| 15 | 60 | 1,54 | 0,9744 | optimal | 0,9744 | 4,0–20,0 |
| 15 | 120 | 1,54 | 0,9744 | optimal | 0,9744 | 4,1–39,5 |
| 16 | 60 | 1,64 | 0,9872 | optimal | 0,9872 | 5,2–22,7 |
| 16 | 120 | 1,64 | 0,9872 | optimal | 0,9872 | 5,0–23,4 |
| 17 | 60 | 1,74 | 1,0000 | optimal | 1,0000 | 19,2–22,3 |
| 17 | 120 | 1,74 | 1,0000 | optimal | 1,0000 | 39,2–39,7 |
| 18 | 60 | 1,85 | 1,0000 | optimal | 1,0000 | 19,6–22,3 |
| 18 | 120 | 1,85 | 1,0000 | optimal | 1,0000 | 39,6–39,8 |

Kết luận trong phạm vi đã đo (1 store, 3 seed, 1 worker):
- Số người nhỏ nhất đạt coverage ≥ 98% là **16** (tỉ lệ sức chứa 1,64, coverage 0,9872). Với 15 người coverage là 0,9744, chưa đạt.
- Từ 13 người trở lên, tầng thiếu người được chứng minh tối ưu trong cả 60 và 120 giây. Từ 8 đến 12 người, tầng này chỉ `feasible`: cận trên coverage được chứng minh, nhưng coverage thực tế thấp hơn và không biết khoảng cách còn lại. Tăng time limit từ 60 lên 120 giây gần như không đổi coverage (chỉ 9 người seed 0 thay đổi nhỏ).
- Ở 17 và 18 người, tầng thiếu người đạt 0 giờ thiếu và được chứng minh. Tầng chi phí (tầng sau) thì không chứng minh được trong 120 giây (gap 0,5–0,75), nên dòng đó chỉ là `feasible`. Phần này không ảnh hưởng kết luận về coverage.
- Mỗi người thêm vào tăng coverage khoảng 0,01–0,03 (từ 12 đến 16 người); từ 17 người coverage đạt 1,0.

Kịch bản căng 8 người, so sánh exact và decompose (`docs/experiments/coverage_tight.csv`, 1 worker, seed 0–2):

| Chế độ | Giới hạn (s) | Coverage (3 seed) | Tầng thiếu người | Xấp xỉ | Thời gian (s) |
|---|---|---|---|---|---|
| exact | 60 | 0,7009, 0,7030, 0,7051 | feasible | không | 54,4–57,4 |
| exact | 120 | 0,7009, 0,7030, 0,7051 | feasible | không | 109,5–112,8 |
| decompose | 60 | 0,7009, 0,7009, 0,7051 | feasible | có, không bao giờ `OPTIMAL` | 27,0–27,7 |
| decompose | 120 | 0,7030, 0,7030, 0,7051 | feasible | có, không bao giờ `OPTIMAL` | 53,9–57,7 |

Kết luận: với 8 người, exact và decompose không chứng minh được gì thêm trong 120 giây. Decompose nhanh hơn một nửa nhưng nghiệm không tốt hơn và chỉ là xấp xỉ.

Lượt 8 worker (seed 0, 60 giây, `docs/experiments/coverage_tight_workers8.csv`) cho `OPTIMAL` tầng thiếu người trong 2,5 giây với 139 giờ thiếu. Lần kiểm tra lại với cùng cấu hình cho 138 giờ thiếu (coverage 0,7051). Hai lần khác nhau vì chạy đa luồng không tái lập được. Vì vậy không dùng lượt 8 worker để kết luận, chỉ ghi nhận rằng nhiều worker có thể chứng minh nhanh hơn.

Lưu ý về cột CSV: `objective`, `bound`, `gap` là của tầng chi phí (tầng cuối), không phải số giờ thiếu. Số giờ thiếu nằm ở `understaffed` (nghiệm cuối) và `shortfall_bound` (cận của tầng đầu).

## 5. Tối ưu so với baseline greedy (plan C5)

Số liệu từ `docs/experiments/scenario_results.csv`, sinh ngày 2026-11-08 bằng `backend/scripts/run_experiments.py` (`--time-limit 30`, seed 0–2 cho kịch bản cơ sở, seed 0 cho các kịch bản khác, 1 worker). Ba store đã chọn theo `docs/experiments/store_ranking.csv`: 18, 84, 578. Tổng 108 lượt, mọi lượt `violations = 0`, không có lỗi.

Greedy là heuristic (`engine/src/shiftopt/baseline.py`), không báo `OPTIMAL`. Trạng thái CP-SAT ghi theo ba tầng (thiếu người / chi phí / lệch ca đêm); lượt chỉ là `optimal` khi cả ba tầng `optimal`.

| Store | Kịch bản | CP-SAT: giờ thiếu / chi phí | Greedy: giờ thiếu / chi phí | Chênh lệch chi phí (cùng giờ thiếu) | Tầng CP-SAT |
|---|---|---|---|---|---|
| 18 | cơ sở | 12 / 7 740 000 | 22 / 7 212 000 | không so sánh được | optimal / optimal / feasible |
| 18 | λ = 1,3 | 101 / 7 632 000 | 168 / 6 606 000 | không so sánh được | feasible / optimal / feasible |
| 18 | bớt 5 người | 81 / 5 028 000 | 121 / 4 684 000 | không so sánh được | feasible / feasible / feasible |
| 18 | p = 3 | 60 / 7 608 000 | 97 / 6 994 000 | không so sánh được | optimal / optimal / feasible |
| 84 | cơ sở | 2 / 5 178 000 | 14 / 4 614 000 | không so sánh được | optimal / optimal / optimal |
| 84 | bớt 5 người | 112 / 2 532 000 | 110 / 2 562 000 | không so sánh được (gần bằng) | feasible / feasible / feasible |
| 578 | cơ sở | 1 / 4 176 000 | 10 / 3 832 000 | không so sánh được | optimal / optimal / optimal |
| 578 | λ = 1,1 | 86 / 4 170 000 | 86 / 4 170 000 | 0,0% | optimal / optimal / optimal |
| 578 | λ = 1,3 | 88 / 4 158 000 | 88 / 4 170 000 | +0,3% (CP-SAT rẻ hơn) | optimal / optimal / optimal |
| 578 | bớt 5 người | 128 / 1 482 000 | 128 / 1 566 000 | +5,7% (CP-SAT rẻ hơn) | feasible / feasible / feasible |

Báo nghỉ 1 người từ thứ Tư (`repair` so với greedy chạy lại từ đầu), số phân công thay đổi:

| Store | Nghỉ 1 ngày | Nghỉ 2 ngày | Nghỉ 3 ngày |
|---|---|---|---|
| 18 | 10 / 16 | 9 / 29 | 8 / 42 |
| 84 | 8 / 16 | 13 / 31 | 8 / 45 |
| 578 | 10 / 20 | 5 / 41 | 4 / 52 |

Đọc kết quả trong phạm vi đã đo:

- Trên cả ba store, greedy thường thiếu người nhiều hơn CP-SAT (ví dụ store 18 cơ sở: 22 giờ so với 12). Chi phí thấp hơn của greedy vì vậy không phải là lợi thế; chỉ so chi phí khi cùng số giờ thiếu.
- Chỉ có những kịch bản cùng số giờ thiếu mới có so sánh chi phí: store 578 với λ ≥ 1,1 và khi bớt 5 người. Ở đó CP-SAT rẻ hơn từ 0 đến 5,7%.
- Báo nghỉ: `repair` của CP-SAT đổi ít phân công hơn greedy ở mọi kịch bản (4–13 so với 16–52). Greedy được chạy lại từ đầu, không phải sửa từ lịch cũ, nên đây là so sánh số thay đổi chứ không phải so sánh thuật toán.
- Nhiều lượt CP-SAT chỉ đạt `feasible` ở tầng chi phí hoặc ca đêm trong 30 giây. Không có kết luận tối ưu cho các lượt đó.

Giới hạn: ba store, 30 giây mỗi lượt, một worker. Kết quả không suy ra cho store khác hay cho giới hạn thời gian dài hơn.

Tái chạy:

```
cd backend
uv run --locked python -m scripts.rank_stores > ../docs/experiments/store_ranking.csv
uv run --locked python -m scripts.run_experiments --time-limit 30 --seeds 0 1 2
uv run --locked python -m scripts.run_experiments --summary
```

Lần chạy đầy đủ mất khoảng 36 phút trên một máy.
