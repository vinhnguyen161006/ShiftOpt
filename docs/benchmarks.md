# Số đo benchmark

Mọi số trong file này chạy lại được bằng lệnh ghi bên dưới. Kết luận chỉ áp cho instance, time limit, seed và số worker đã ghi (CLAUDE.md nguyên tắc 5). Không trích số của nhóm khác như số của ShiftOpt.

**Đơn vị chi phí:** mọi chi phí trong file này là đơn vị nội bộ của engine, bằng lương mỗi giờ × giờ × 100 (`PERCENT_BASE` trong `engine/src/shiftopt/domain.py`, để phụ cấp đêm 30% là số nguyên). Chia cho 100 để ra số tiền lương. Ví dụ store 18, 30 nhân viên: 8 892 000 đơn vị nội bộ tương ứng 88 920 tiền lương. Tỷ lệ phần trăm không bị ảnh hưởng.

Máy đo: Windows 11 (10.0.26200), 16 luồng CPU, Python 3.11.14, OR-Tools 9.15.6755, PuLP 3.3.2. Mục 1–3 đo ngày 2026-10-29; mục 2b, 2c, 7, 8 đo ngày 2026-11-08; mục 4 ngày 2026-11-05; mục 5 ngày 2026-11-08; mục 6 ngày 2026-11-09. Các mục đo trước khi có giờ tối thiểu và ngân sách (G3) không dùng hai tính năng này, nên không bị ảnh hưởng.

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

## 3. Lịch tuần 7×24, 20–40 nhân viên (CLAUDE.md mục 13, tiêu chí hiệu năng)

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

Nhu cầu: `derive_demand` trên `data/demo/train.parquet`, cửa hàng 18 (split train; ô hết hàng đã thay bằng nhu cầu ẩn; giờ 22h–06h đặt sàn đêm). Giả định của nhóm, đã duyệt 2026-11-08 (đặc tả D7–D9): `alpha = 1.0`, `p = 4.0` (chọn để giờ đỉnh cần 8 người), `min_staff = 1`, `night_min_staff = 1`. Ca: 0h, 8h, 16h, mỗi ca 8 giờ. 30 nhân viên, lương 100, không yêu cầu cá nhân. Luật: 48 giờ/tuần, `K = 6`. Time limit 60 giây, gap 0,01, 1 worker, không phá đối xứng.

Lệnh:

```
cd backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 30 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
```

| Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng | Solver |
|---|---|---|---|---|---|---|---|
| 0 | optimal | 0.0 | 19,54 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |
| 1 | optimal | 0.0 | 16,91 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |
| 2 | optimal | 0.0 | 12,03 | 0 | 1.0000 | 0 | ortools-cp-sat 9.15.6755 |

Kịch bản căng (8 nhân viên, cùng nhu cầu và giả định, sức chứa 384 giờ-người nhỏ hơn 468 giờ-người nhu cầu):

```
cd backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 8 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
```

| Seed | Status | Gap | Wall (s) | Thiếu (giờ) | Coverage | Vi phạm cứng |
|---|---|---|---|---|---|---|
| 0 | feasible | 1,0 | 60,26 | 139 | 0,7030 | 0 |
| 1 | feasible | 1,0 | 60,35 | 139 | 0,7030 | 0 |
| 2 | feasible | 1,0 | 60,43 | 139 | 0,7030 | 0 |

Kết quả: không chứng minh được tối ưu trong 60 giây (gap 1,0 ở tầng cuối). Lịch vẫn hợp lệ theo validator. Đây là giới hạn của solver với time limit này, không phải lỗi ràng buộc. Không hạ ràng buộc. Hướng xử lý nếu cần: tăng time limit, bật phân rã hai pha (`decompose`, [model.md](model.md) mục 2) để có nghiệm ban đầu, hoặc tăng nhân viên.

Kết luận trong phạm vi đã đo:
- 3/3 `OPTIMAL`, coverage 1,0, 0 vi phạm cứng, mọi lần dưới 60 giây.
- Kịch bản 30 người dư sức chứa: giờ đỉnh cần 8 người, tổng nhu cầu 468 giờ-người mỗi tuần (chưa tính nghỉ giữa giờ), sức chứa 30 × 48 = 1440. Coverage 98% đạt ở đây không chứng minh được khả năng phủ khi thiếu người.
- Kịch bản căng 8 người ở trên cho coverage 70,3% và chỉ `FEASIBLE`. Mức "vừa đủ" (khoảng 1,1 lần nhu cầu) chưa đo (plan E1).
- Kết quả phụ thuộc `alpha`, `p`, các sàn. Đổi `p` đổi toàn bộ nhu cầu; xem độ nhạy theo giả định (`sweep_staffing_assumption`, [model.md](model.md) mục 5).
- 1 store, 3 seed. Không suy ra cho store khác.

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

### 5b. Nhận xét quản lý: store 18, cùng lượt thực nghiệm (plan J2)

Các dòng CP-SAT seed 0 của store 18 trong `docs/experiments/scenario_results.csv` (cùng lượt chạy mục 5, 30 giây, 1 worker). Số nhân viên của kịch bản cơ sở do `run_experiments.employee_count` đặt: `ceil(1,25 × 468 / 40) = 15` người, lương 100, `p = 4`, 3 ca 0/8/16 h. Đây khác kịch bản cơ sở 30 người của mục 4.

| Kịch bản | Nhân viên | Giờ thiếu | Giờ thừa | Coverage | Chi phí | Tầng CP-SAT |
|---|---|---|---|---|---|---|
| cơ sở (3 ca) | 15 | 12 | 174 | 0,974 | 7 740 000 | optimal / optimal / feasible |
| 6 giờ bắt đầu ca (0/4/…/20) | 15 | 0 | 71 | 1,000 | 6 514 000 | optimal / optimal / optimal |
| bớt 1 người | 14 | 18 | 138 | 0,962 | 7 242 000 | optimal / optimal / optimal |
| bớt 2 người | 13 | 30 | 108 | 0,936 | 6 690 000 | optimal / optimal / optimal |
| bớt 5 người | 10 | 81 | 33 | 0,827 | 5 028 000 | feasible / feasible / feasible |
| λ = 1,1 | 15 | 56 | 50 | 0,912 | 7 704 000 | optimal / optimal / feasible |
| λ = 1,3 | 15 | 101 | 31 | 0,856 | 7 632 000 | feasible / optimal / feasible |
| p = 3 | 15 | 60 | 101 | 0,898 | 7 608 000 | optimal / optimal / feasible |
| p = 5 | 15 | 0 | 177 | 1,000 | 7 166 000 | optimal / optimal / optimal |

Đọc trong phạm vi đã đo (một store, seed 0, 30 giây):

- **Bộ ca quan trọng hơn số người.** Với cùng 15 người, chuyển từ 3 lên 6 giờ bắt đầu ca đưa giờ thiếu từ 12 về 0, giờ thừa từ 174 về 71 và chi phí giảm khoảng 15,8%; cả ba tầng `OPTIMAL`. Tầng thiếu người và chi phí của kịch bản 3 ca cũng `OPTIMAL`, nên so sánh hai tầng này là giữa hai tối ưu đã chứng minh.
- **Mỗi người bớt đi làm tăng giờ thiếu nhanh dần:** 12 → 18 → 30 giờ khi bớt 1 rồi 2 người (đều `OPTIMAL` ở tầng thiếu người); bớt 5 người còn 81 giờ thiếu nhưng chỉ `FEASIBLE`.
- **Giả định năng suất `p` tác động ngang với biến động nhu cầu:** `p = 3` cho 60 giờ thiếu, gần bằng λ = 1,1 (56 giờ); `p = 5` phủ đủ. Kết luận về biên chế phụ thuộc mạnh vào giả định quy đổi.
- Chi phí giảm khi λ tăng hay khi bớt người vì phần thiếu không phát sinh lương; không đọc như tiết kiệm.

Tái chạy:

```
cd backend
uv run --locked python -m scripts.rank_stores > ../docs/experiments/store_ranking.csv
uv run --locked python -m scripts.run_experiments --time-limit 30 --seeds 0 1 2
uv run --locked python -m scripts.run_experiments --summary
```

Lần chạy đầy đủ mất khoảng 36 phút trên một máy.

## 6. Đánh đổi chi phí và công bằng (plan F3)

Lệnh: `cd engine && uv run --locked python -u -m benchmarks.cost_tolerance`. Lương lệch theo vòng 100, 120, 150. Mỗi dòng là một lần giải đầy đủ với `cost_tolerance_percent` tương ứng, 1 worker, seed 0, 60 giây, không ngưỡng gap. `cost_increase_percent` so với dòng 0 của cùng số nhân viên, tính bằng `kpi.labor_cost` trên lịch trả về.

| Nhân viên | Dung sai (%) | Status | Chi phí lao động | Tăng (%) | Chênh ca đêm | Chênh giờ làm | Giờ thiếu |
|---|---|---|---|---|---|---|---|
| 12 | 0 | feasible | 7 531 200 | 0,00 | 6 | – | 2 |
| 12 | 1 | feasible | 7 606 200 | 1,00 | 2 | 0 | 2 |
| 12 | 2 | feasible | 7 611 600 | 1,07 | 5 | 0 | 2 |
| 12 | 5 | feasible | 7 615 200 | 1,12 | 2 | 0 | 2 |
| 12 | 10 | feasible | 7 632 000 | 1,34 | 2 | 0 | 2 |
| 20 | 0 | feasible | 6 864 000 | 0,00 | 6 | – | 0 |
| 20 | 1 | feasible | 6 864 000 | 0,00 | 6 | 48 | 0 |
| 20 | 2 | feasible | 7 000 000 | 1,98 | 1 | 48 | 0 |
| 20 | 5 | feasible | 7 203 800 | 4,95 | 1 | 32 | 0 |
| 20 | 10 | feasible | 7 539 000 | 9,83 | 1 | 24 | 0 |

Kết luận trong phạm vi đã đo:

- **Mọi dòng đều `FEASIBLE`, không dòng nào `OPTIMAL` trong 60 giây.** Các số chỉ là nghiệm tìm được tới lúc dừng. Không được đọc chênh lệch 1–2 đơn vị như xu hướng đã chứng minh.
- Với 20 nhân viên, dung sai 2–10% kéo chênh ca đêm từ 6 xuống 1 và chênh giờ làm từ 48 xuống 24, với chi phí tăng 2–10%. Đây là đánh đổi thực, đúng hướng mục tiêu F.
- Với 12 nhân viên, dung sai 1% đã đưa chênh ca đêm từ 6 xuống 2. Các dòng sau không cải thiện thêm và dao động (2 → 5 → 2), phù hợp với việc giải không kết thúc.
- Dòng 20 nhân viên, dung sai 1%: chi phí không đổi nhưng chênh giờ làm đã có giá trị 48. Tầng `hours_spread` chưa được chứng minh tối ưu nên giá trị này là giới hạn trên.
- Chưa đo ở store 18 hay kịch bản 30 nhân viên. Muốn kết luận chắc hơn cần chạy lại với time limit dài hơn và có gap.

## 7. Integrality gap: LP relaxation so với nghiệm nguyên

Gap đo bằng cùng một công thức trên cả hai mô hình: `gap_pct = 100 (z_IP − z_LP) / max(1, z_IP)`. `z_LP` là tối ưu của bài toán nới lỏng (biến liên tục). Đây là nguồn gốc của nhãn "xấp xỉ" cho dual LP ([model.md](model.md) mục 5, [kiến trúc.md](kiến%20trúc.md) mục 7.5): dual lấy từ bài toán nới lỏng, nên sai lệch với chi phí biên thật tùy theo gap.

Lệnh: `cd engine && uv run --locked python -u -m benchmarks.integrality_gap`. Nhu cầu store 18 đọc từ `docs/experiments/store18_demand.csv` (168 giờ, xuất bằng `backend/scripts/baseline_store18.py`, cùng giả định mục 4).

Mô hình tổng hợp (có nghỉ ngầm, [model.md](model.md) mục 1b), chi phí lương:

| Instance | z_LP | z_IP | gap (%) |
|---|---|---|---|
| uniform_3_shifts | 2 217 600 | 3 696 000 | 40,0 |
| peaked_3_shifts | 3 371 200 | 4 256 000 | 20,8 |
| peaked_spaced_8_shifts | 3 570 000 | 3 570 000 | 0,0 |
| store 18, 30 nhân viên (nhu cầu thật, mục 4) | 8 828 000 | 8 892 000 | 0,72 |

Mô hình theo nhân viên, 10 nhân viên, seed 0, 1, 2 (HiGHS, 60 giây, tầng 1 và tầng 2):

| Seed | Tầng | z_LP | z_IP | gap (%) |
|---|---|---|---|---|
| 0 | thiếu người | 26,2 | 28,0 | 6,4 |
| 0 | chi phí | 5 131 600 | 5 148 000 | 0,32 |
| 1 | thiếu người | 31,2 | 34,0 | 8,4 |
| 1 | chi phí | 5 127 000 | 5 136 000 | 0,18 |
| 2 | thiếu người | 28,9 | 34,0 | 15,0 |
| 2 | chi phí | 5 101 000 | 5 106 000 | 0,10 |

Store 18, 30 nhân viên, nhu cầu tuần cố định (không có seed), HiGHS 60 giây, `relative_gap_limit = 0`:

| Tầng | z_LP | z_IP | gap (%) | Trạng thái IP |
|---|---|---|---|---|
| thiếu người | 0 | 0 | 0,0 | optimal |
| chi phí | 8 827 999,9 | 8 892 000 | 0,72 | optimal |

Kết luận trong phạm vi đã đo:

- Gap của tổng hợp lớn ở instance đều (40%) và đỉnh (21%). Ở instance ca cách đều 8 ca, gap bằng 0. Dual LP của mô hình tổng hợp vì vậy chỉ có thể dùng làm xấp xỉ, không thể đọc như chi phí biên của giờ nguyên.
- Mô hình theo nhân viên: gap của tầng chi phí rất nhỏ (dưới 0,4%), gap của tầng thiếu người lớn hơn nhiều (6–15%). Lý do: nhu cầu 3–4 người không chia được đều theo ca 8 giờ, nên nghiệm nới lỏng có phần giờ thiếu không nguyên.
- Store 18 (B5): cả hai mô hình có gap tầng chi phí 0,72%, cả hai `OPTIMAL`. Z_IP của hai mô hình bằng nhau (8 892 000), kiểm tra chéo được. Tầng thiếu người bằng 0 vì 30 nhân viên dư sức chứa, nên gap tầng này không có ý nghĩa ở kịch bản này.
- Trên nhu cầu thật, gap nhỏ hơn nhiều so với instance tổng hợp đỉnh 3 ca (20,8%). Nguyên nhân chưa kiểm chứng riêng: nhu cầu cao và nhiều ca khiến nghiệm nới lỏng gần nguyên hơn. Đây là một store với một bộ giả định (`alpha = 1`, `p = 4`); không suy ra cho store khác.
- Mô hình tổng hợp và mô hình theo nhân viên đều cho gap dưới 1% trên store 18, nhưng dual LP vẫn chỉ là xấp xỉ theo nguyên tắc 4 của CLAUDE.md.

## 8. Lexicographic so với mục tiêu có trọng số

Mục tiêu có trọng số: `min w · thiếu người + chi phí + 1 · (n_max − n_min)`, một lần giải CP-SAT. Mục tiêu lexicographic là lượt giải theo tầng của `solve_roster`. Cùng nhu cầu, 1 worker, seed 0, 60 giây.

Lệnh: `cd engine && uv run --locked python -u -m benchmarks.weighted_vs_lexicographic`

| Nhân viên | Phương án | w | Status | Giờ thiếu | Chi phí lương | F |
|---|---|---|---|---|---|---|
| 8 | lexicographic | – | feasible | 87 | 4 092 000 | 4 |
| 8 | có trọng số | 1 | optimal | 414 | 0 | 0 |
| 8 | có trọng số | 1 000 | optimal | 414 | 0 | 0 |
| 8 | có trọng số | 100 000 | feasible | 88 | 4 092 000 | 2 |
| 8 | có trọng số | 10 000 000 | feasible | 86 | 4 110 000 | 3 |
| 12 | lexicographic | – | feasible | 2 | 6 168 000 | 2 |
| 12 | có trọng số | 1 | optimal | 414 | 0 | 0 |
| 12 | có trọng số | 1 000 | optimal | 414 | 0 | 0 |
| 12 | có trọng số | 100 000 | feasible | 11 | 5 892 000 | 0 |
| 12 | có trọng số | 10 000 000 | feasible | 2 | 6 168 000 | 2 |

Kết luận trong phạm vi đã đo:

- Với w = 1 và w = 1 000, không xếp ai: giờ thiếu bằng toàn bộ nhu cầu (414), chi phí bằng 0. Một giờ-người phục vụ thêm chỉ tiết kiệm w, trong khi một ca 8 giờ tốn khoảng 80 000 đơn vị chi phí, tức khoảng 10 000 mỗi giờ. Trọng số dưới ngưỡng này làm mất hết độ phủ mà không báo lỗi.
- Với w = 100 000, mục tiêu có trọng số bắt đầu phủ nhu cầu: 12 nhân viên thiếu 11 giờ thay vì 2 giờ, đổi lại chi phí thấp hơn 276 000 (khoảng 4,5%). Ngưỡng nằm giữa 10 000 và 100 000 cho cấu hình này.
- Trọng số lớn (10⁷) cho kết quả gần lexicographic ở 12 nhân viên (cùng 2 giờ thiếu và cùng chi phí).
- Ở 8 nhân viên, lượt lexicographic không chứng minh được tầng 1 trong 60 giây; lượt có trọng số 10⁷ tìm được 86 giờ thiếu so với 87 của lexicographic. Đây là giới hạn thời gian, không phải kết quả về thứ tự ưu tiên. Không kết luận cái nào tốt hơn ở cấu hình này.
- Kết luận cho báo cáo: lexicographic không cần chọn trọng số, nên không có nguy cơ mất độ phủ âm thầm như trên; đổi lại mỗi tầng phải được giải riêng và chia thời gian.
