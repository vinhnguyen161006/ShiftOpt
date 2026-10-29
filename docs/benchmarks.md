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
