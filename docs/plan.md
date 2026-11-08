# Kế hoạch hoàn thiện ShiftOpt

Cập nhật: 2026-11-08, sau merge `feat/phase-9-10` vào `main` (`256e94a`), [benchmarks.md](benchmarks.md), [đặc tả.md](đặc%20tả.md) và kế hoạch nhóm đề xuất ngày 2026-11-08. File này thay cho các kế hoạch rời trước đó.

**Nhóm điền trước khi dùng:**

- Deadline nộp: [điền]. Ngày demo hoặc bảo vệ: [điền].
- Rubric chấm điểm (nếu có): [đính kèm]. Có rubric thì sắp lại mục 3 theo đúng tiêu chí chấm.
- Người phụ trách: cột "Phụ trách" ở mục 3.

## 1. Nguyên tắc chọn việc

Đề bài yêu cầu bốn phần:

1. Mô hình hóa bài toán xếp ca bằng quy hoạch nguyên tuyến tính: nhu cầu theo giờ, ca 8 giờ, nghỉ giữa ca, số ngày làm liên tiếp.
2. Giải bằng OR-Tools hoặc PuLP.
3. Phân tích độ nhạy khi nhu cầu thay đổi.
4. Giao diện nhập nhu cầu và xem lịch.

Điểm cao đến từ ba thứ, theo thứ tự:

1. **Sức nặng học thuật:** công thức ILP rõ ràng, phân tích mô hình (kích thước, integrality gap, cách chọn mục tiêu), nhận xét rút ra từ kết quả. Đây là phần yếu nhất hiện nay.
2. **Bằng chứng tối ưu hóa:** so với baseline xếp tay, so hai solver, đo độ nhạy và đánh đổi, trên nhiều store.
3. **Sản phẩm chạy được, trình bày trung thực:** UI được duyệt, báo cáo và slide khớp số đo, giới hạn nói rõ.

Mức ưu tiên: **P0** bắt buộc, **P1** nên có, **P2** có thì tốt. Việc đụng phạm vi đã chốt trong CLAUDE.md (mục 14) hoặc thứ tự ưu tiên của mô hình (mục 5.2) ghi **"cần duyệt đặc tả"** và chỉ làm sau khi nhóm đồng ý.

## 2. Hiện trạng

### 2.1 Đã đạt

| Hạng mục | Bằng chứng |
|---|---|
| Ràng buộc cứng: 0 vi phạm trên mọi nghiệm | CLAUDE §13 dòng 1 |
| Hiệu năng: 20–40 nhân viên, 18/18 `OPTIMAL`, tối đa 31,5 giây | CLAUDE §13 dòng 3 |
| Pháp lý: test bắt buộc Đ.110, Đ.111 | CLAUDE §13 dòng 6 |
| Tái lập: cùng seed, `num_workers = 1`, cùng objective | CLAUDE §13 dòng 7 |
| Curtois & Qu (8 worker, 120 giây): Instance1–3 đạt và chứng minh tối ưu công bố; Instance4 đạt nhưng chưa chứng minh; Instance5 cách 5 đơn vị | benchmarks.md mục 1 |
| Độ nhạy ở engine: `z(λ)`, chi phí biên bằng giải lại, dual LP gắn nhãn xấp xỉ | CLAUDE §13 dòng 5 |
| Ingest file doanh số tổng quát, CSV hoặc parquet, gợi ý cột (đặc tả D19) | `backend/src/demand/sales_ingest.py` |
| Giao diện tối | CLAUDE.md mục 8.3 |
| **Xếp lại lịch (repair) và gợi ý người thay** (đặc tả D20): ngày khóa, người vắng, ca ghim, tầng "số ca thay đổi" sau thiếu người; kiểm tập khóa bằng validator trước khi giải | `engine/src/shiftopt/models/roster_cpsat.py`, `engine/src/shiftopt/replacement.py`, `POST /schedules/{id}/repair`, `GET /schedules/{id}/replacements` |

Kiểm tra ngày 2026-11-08: engine 162 test pass, coverage 98,36%; backend 101 unit test pass; frontend `npm run ci` pass; `check_conventions.py` sạch. **Integration test backend chưa chạy** trong lượt này vì máy không có MySQL.

### 2.2 Còn mở

| Mục | Trạng thái | Việc |
|---|---|---|
| Công thức ILP mô hình theo nhân viên | Thiếu | B1, B2 |
| Acceptance dòng 2, phủ nhu cầu | Đạt có điều kiện: kịch bản cơ sở dư sức chứa; kịch bản 8 người cho coverage 0,703, gap 1,0 | E |
| Acceptance dòng 4, so sánh solver | Sai lệch: chỉ so trên mô hình tổng hợp (D12) | B3 |
| Acceptance dòng 5 và 9, UI | Chờ người duyệt tay | D |
| Phạm vi dữ liệu | Mọi kết quả chỉ trên store 18 | C2 |
| Nhận xét quản lý | Có số đo, chưa có nhận xét | J2 |
| Đặc tả | Bản nháp D1–D20; điều luật chưa đối chiếu nguyên văn | A3, A4 |
| Repair, gợi ý người thay | Chưa duyệt trên trình duyệt; nguồn UI thứ hai (Deputy) chỉ đọc được qua snippet | A5 |

## 3. Lộ trình

| Giai đoạn | Nội dung | Ưu tiên | Ước lượng | Phụ trách | Mốc |
|---|---|---|---|---|---|
| A | Hợp nhất nhánh, tài liệu, quyết định nhóm | P0 | 1 ngày | [điền] | [điền] |
| B | Mô hình ILP và phân tích mô hình | P0 | 2,5 ngày | [điền] | [điền] |
| C | Baseline greedy và thực nghiệm nhiều store | P0 | 2,5 ngày | [điền] | [điền] |
| D | Đóng nghiệm thu UI | P0 | 1 ngày | [điền] | [điền] |
| E | Coverage khi thiếu người | P1 | 0,5 ngày | [điền] | [điền] |
| F | Đánh đổi chi phí và công bằng (cần duyệt đặc tả) | P1 | 1 ngày | [điền] | [điền] |
| G | Tính năng nhỏ | P2 | 1–2 ngày | [điền] | [điền] |
| H | Tuần không quấn vòng (cần duyệt đặc tả) | P2 | 3 ngày | [điền] | [điền] |
| I | Dự báo tối giản (cần duyệt đặc tả) | P2 | 1 ngày | [điền] | [điền] |
| J | Báo cáo, nhận xét quản lý, slide, demo | P0 | 2,5 ngày | [điền] | [điền] |

Ước lượng thô, tính cho một người, đã cộng khoảng 25% dự phòng cho B và C. Tổng P0 khoảng 9,5 ngày-người.

Thứ tự đề xuất: A → B1 → C → D → B2–B6 → J (bản nháp) → E → F → J (bản cuối) → G, H, I nếu còn thời gian.

Thiếu thời gian thì làm đủ A, B1–B3, C1–C5, D, J. Đưa E–I vào mục "Hướng phát triển" của báo cáo, kèm lý do.

Chia việc cho hai người: một người làm B và C (engine, thực nghiệm), một người làm D và J (UI, tài liệu, demo). A làm chung.

## 4. Chi tiết

### A. Hợp nhất nhánh, tài liệu, quyết định nhóm (P0)

| # | Việc | Xong khi |
|---|---|---|
| A0 | **Xong 2026-11-08**: giữ repair, bỏ FR-9, merge vào `main`. Gốc: commit thay đổi của `feat/phase-9-10`. Fetch nhánh `tulee`, so FR-9 (`bbff7c2`) với repair (D20). Chọn **một** đường API và **một** giao diện cho báo nghỉ, bỏ bản còn lại | Một PR duy nhất chứa ingest D19, giao diện tối, báo nghỉ đã hợp nhất; không còn hai endpoint cùng việc |
| A1 | Merge PR vào `main` | CI trên `main` xanh. **Xong 2026-11-08**: `main` = `256e94a`, run `42484777634` |
| A2 | Đồng bộ tài liệu với D18 | Đã làm 2026-11-08: `grep -n -i "tổng đài\|erlang" CLAUDE.md docs/*.md` chỉ còn câu ghi D18 và giới hạn |
| A3 | Nhóm duyệt đặc tả D1–D20 và "Việc cần nhóm quyết" (mục 5 của file này) | Đặc tả bỏ nhãn "bản nháp"; ghi ngày và người duyệt ở đầu `đặc tả.md` |
| A4 | Đối chiếu nguyên văn Đ.98, 105, 106, 109, 110, 111 và NĐ 145/2020 với văn bản 45/2019/QH14 | Đặc tả mục 4 trích nguyên văn, ghi nguồn chính thức |
| A5 | Nguồn UI thứ hai cho màn xếp lại và gợi ý người thay: mở được trang, ghi ngày xem | phụ lục nguồn UI trong `báo cáo.md` R15 có nguồn đã mở (thay snippet Deputy) |
| A6 | Chạy integration test backend trên MySQL 8.4 (gồm 3 test repair mới), `alembic check` | **Xong 2026-11-08** qua CI run `42484777634`: 128 passed, 0 skip, `alembic check` sạch |

### B. Mô hình ILP và phân tích mô hình (P0)

Đề bài ghi "quy hoạch nguyên tuyến tính". Mô hình chính chạy bằng CP-SAT, chưa phải ILP theo nghĩa giáo khoa. Giai đoạn này đưa phần lõi của đề bài lên đúng tầm.

| # | Việc | Xong khi |
|---|---|---|
| B1 | Viết công thức ILP đầy đủ của mô hình theo nhân viên vào `model.md` và báo cáo: tập, tham số, biến `x[e,d,s]` nhị phân, `u_h` nguyên không âm, mọi ràng buộc (Đ.105, 109, 110, 111, ngày liên tiếp) dạng bất đẳng thức tuyến tính, mục tiêu lexicographic, cách tuyến tính hóa nghỉ 24 giờ và max/min của công bằng, tầng thay đổi của repair | Mỗi ràng buộc trong code có một dòng công thức; có bảng đối chiếu ràng buộc ↔ hàm trong `roster_cpsat.py` |
| B2 | `engine/src/shiftopt/models/roster_mip.py`: cùng công thức B1, giải bằng PuLP + HiGHS, lexicographic bằng cách cố định tầng trước | Validator cho 0 vi phạm; với 10–20 nhân viên, cùng giá trị tầng thiếu người và chi phí với CP-SAT |
| B3 | So sánh solver trên mô hình theo nhân viên: `compare_solvers.py` thêm chế độ roster, 10/20/30 nhân viên, cùng time limit và seed | Bảng trong benchmarks.md mục 2; CLAUDE §13 dòng 4 chuyển Đạt hoặc ghi rõ phạm vi |
| B4 | Kích thước mô hình: số biến, số ràng buộc theo số nhân viên (10, 20, 30, 40) và số loại ca, cho CP-SAT và MIP | Bảng và biểu đồ trong báo cáo |
| B5 | Integrality gap: so LP relaxation với nghiệm nguyên tối ưu trên nhiều instance, cả mô hình tổng hợp và MIP theo nhân viên | Bảng trong báo cáo, kèm giải thích vì sao dual LP chỉ là xấp xỉ |
| B6 | Lexicographic so với trọng số: cùng instance, thử `M_u` nhỏ, vừa, lớn; chỉ ra khi nào trọng số đảo thứ tự ưu tiên | Bảng trong báo cáo |

B2 chậm trên instance lớn thì chỉ báo cáo phạm vi đã đo và giải thích lý do (MIP lớn hơn, CP-SAT mạnh ở ràng buộc chuỗi).

### C. Baseline greedy và thực nghiệm nhiều store (P0)

Trạng thái: C1–C5 đã làm (2026-11-08); C6 chưa làm theo yêu cầu. Chỉ 3 store đạt tiêu chí, xem mô tả dữ liệu mục 8.

| # | Việc | Xong khi |
|---|---|---|
| C1 | `engine/src/shiftopt/baseline.py`: greedy ưu tiên giờ thiếu nhiều nhất, chọn người khả dụng có ít giờ nhất, kiểm ràng buộc cứng trước mỗi lần gán. Validator kiểm lại | Test: greedy luôn 0 vi phạm; trên ví dụ có đáp án tay, chi phí greedy ≥ tối ưu |
| C2 | Chọn thêm 3–5 store khác quy mô (theo tổng doanh số). Ingest bằng `derive_demand` qua `backend/scripts/baseline_store18.py --store N` (script `build_demand_store.py` đã bỏ) | Tiêu chí chọn và loại trừ ghi trong `mô tả dữ liệu.md` |
| C3 | `engine/benchmarks/run_experiments.py`: một lệnh sinh `docs/experiments/scenario_results.csv`, seed cố định, `num_workers = 1`, nhiều seed cho kịch bản chính | Cột: store, kịch bản, phương án, chi phí, giờ thiếu, giờ thừa, coverage, status, gap, thời gian |
| C4 | Kịch bản: cơ sở; λ ∈ {0,8 … 1,3}; bớt 1, 2, 5 nhân viên; bộ ca 3 giờ bắt đầu (0/8/16) so với 6 giờ bắt đầu (0/4/…/20); p ∈ {3, 4, 5}; báo nghỉ 1 người 1–3 ngày, đo `changes` của repair | Mỗi kịch bản có dòng cho CP-SAT và greedy, trên mọi store đã chọn |
| C5 | Bảng và biểu đồ: chênh lệch chi phí tối ưu so với greedy, coverage, thời gian, theo store | Báo cáo có mục "Tối ưu so với baseline" |
| C6 | (P1) Nút "So với baseline" trong What-if, bảng hai phương án | Thấy trên UI; `npm run ci` pass; có hai nguồn UI trong phụ lục nguồn UI trong `báo cáo.md` |

### D. Đóng nghiệm thu UI (P0)

| # | Việc | Xong khi |
|---|---|---|
| D1 | Script end-to-end trên stack Compose: nhu cầu → mẫu ca → nhân viên → Optimize → lịch, coverage, tuân thủ, chi phí → kéo λ → xếp lại → gợi ý người thay → sửa tay gây vi phạm. Playwright cần nhóm đồng ý (CLAUDE.md mục 10); nếu không, mở rộng `smoke_flow` ở mức API | Chạy hai lần liên tiếp đều pass |
| D2 | Ảnh nghiệm thu mới: `repair.png` (ô đổi, ngày khóa), `replacements.png`, `schedule_dark.png` | Ảnh chèn vào `slides.md` và `báo cáo.md` |
| D3 | Một người duyệt tay theo checklist mục 7 | CLAUDE §13 dòng 5 và 9 chuyển Đạt, có tên và ngày |
| D4 | Sửa lỗi tìm được ở D1–D3. Tiêu đề lượt repair hiện "sửa từ lượt …": đổi thành "xếp lại từ lượt …" ở `RunWorkspace` và `SolveStatusPanel` | Không còn lỗi đã ghi; `npm run ci` pass |

### E. Coverage khi thiếu người (P1)

| # | Việc | Xong khi |
|---|---|---|
| E1 | Kịch bản "vừa đủ": sức chứa khoảng 1,1 × nhu cầu (store 18, khoảng 12 người) | Đo coverage, status, gap với 60 và 120 giây |
| E2 | Kịch bản căng (8 người): thử thêm worker và `decompose=True`. Kết quả phân rã là xấp xỉ, không bao giờ `OPTIMAL`, phải ghi nhãn | Bảng trong benchmarks.md; CLAUDE §13 dòng 2 ghi ba mức: dư, vừa đủ, căng |

### F. Đánh đổi chi phí và công bằng (P1, cần duyệt đặc tả)

CLAUDE.md mục 5.2 đặt chi phí trên công bằng. F2 cho phép tăng chi phí để công bằng hơn, tức đổi thứ tự này. Nhóm duyệt trước khi làm.

| # | Việc | Xong khi |
|---|---|---|
| F1 | `constraints/fairness.py`: thêm độ lệch giờ làm `H_max − H_min` cạnh ca đêm | Test tiêm lịch lệch, đo đúng |
| F2 | `cost_tolerance` (0–10%): tầng công bằng được tăng chi phí tối đa theo tỷ lệ này (epsilon-constraint) | Test: tolerance 0 cho kết quả như hiện nay |
| F3 | Quét tolerance, vẽ đường đánh đổi trong What-if và báo cáo | Đường cong trên UI; số liệu trong benchmarks.md |

### G. Tính năng nhỏ (P2)

| # | Việc | Ghi chú |
|---|---|---|
| G1 | Cảnh báo trước khi giải: nhân viên không còn ngày khả dụng, tổng sức chứa < tổng nhu cầu, không ai làm được ca đêm | Rẻ, giúp hiểu vì sao thiếu |
| G2 | Giải thích giờ thiếu: với mỗi giờ thiếu, liệt kê ràng buộc chặn (hết người, chạm 48 giờ, nghỉ 12 giờ) | Dùng lại hạ tầng độ nhạy |
| G3 | Trần ngân sách tuần, giờ tối thiểu theo hợp đồng | Ràng buộc tuyến tính |
| G4 | Đánh dấu kết quả cũ khi đầu vào đổi (hash đầu vào trong `solve_runs`) | Cần migration Alembic |
| G5 | Gợi ý người thay khi báo nghỉ | **Đã làm** (D20) |

### H. Tuần không quấn vòng (P2, cần duyệt đặc tả)

Mô hình coi tuần là vòng tròn: ca Chủ nhật nối với thứ Hai cùng tuần. CLAUDE.md mục 14 để chân trời nhiều tuần ngoài phạm vi bản đầu. Không làm thì ghi rõ giới hạn trong báo cáo và chuẩn bị câu trả lời (mục 8).

| # | Việc | Xong khi |
|---|---|---|
| H1 | `Instance.horizon_mode`: `"cyclic"` hoặc `"linear"`; `PreviousState` cho từng nhân viên (giờ kết thúc ca cuối, số ngày làm liên tiếp, giờ đã làm) | Chế độ cyclic cho kết quả cũ, mọi test hiện có pass |
| H2 | Nghỉ 12 giờ, 24 giờ, số ngày liên tiếp tính cả kỳ trước, ở mô hình và validator | Test tiêm: ca kết thúc 22h Chủ nhật kỳ trước rồi 06h thứ Hai bị cấm; đã làm 5 ngày với K = 6 thì chỉ còn 1 ngày |
| H3 | Backend lấy `previous_state` từ một lượt trước; UI chọn "tuần trước" | Integration test trên MySQL pass |

### I. Dự báo tối giản (P2, cần duyệt đặc tả)

CLAUDE.md mục 14 không huấn luyện mô hình dự báo ở bản đầu; mục 10 cấm thêm thư viện. Chỉ làm khi A–F xong và nhóm đồng ý.

| # | Việc | Xong khi |
|---|---|---|
| I0 | Xác nhận khoảng ngày của split eval bằng `dt.min()/max()` trước khi dùng (CLAUDE.md mục 4.1) | Ngày ghi trong `mô tả dữ liệu.md` |
| I1 | Baseline "cùng giờ tuần trước" và "trung bình cùng giờ k tuần" trên nhu cầu đã khử censoring | Hàm thuần trong `engine/src/shiftopt/forecast/` |
| I2 | Đánh giá trên split eval: WAPE và bias. Không dùng MAPE vì nhiều giờ bằng 0 | Bảng trong báo cáo |
| I3 | Xếp lịch theo nhu cầu dự báo, đo KPI trên nhu cầu thật | Trả lời "sai số dự báo ảnh hưởng lịch thế nào" |

### J. Báo cáo, nhận xét quản lý, slide, demo (P0)

| # | Việc | Xong khi |
|---|---|---|
| J1 | Cập nhật `báo cáo.md`: công thức ILP (B1), phân tích mô hình (B4–B6), so sánh solver (B3), baseline và nhiều store (C), xếp lại (D20), đánh đổi (F nếu có), giới hạn tuần vòng tròn, D18 | Mọi con số có dòng tương ứng trong benchmarks.md hoặc `scenario_results.csv` |
| J2 | Nhận xét quản lý: giờ nào đẩy chi phí (heatmap chi phí biên); thêm hoặc bớt một người đổi chi phí và coverage bao nhiêu; ràng buộc nào chặt nhất; tác động của `p` và `alpha`; bộ ca 3 hay 6 giờ bắt đầu; báo nghỉ một người đổi bao nhiêu ca | Mỗi nhận xét có số đo và phạm vi (store, kịch bản) |
| J3 | `slides.md`: thêm "Công thức ILP", "Tối ưu so với baseline", "Nhận xét quản lý", "Xếp lại khi có người vắng"; giữ 10–12 slide | Số liệu khớp báo cáo |
| J4 | `demo.md`: kịch bản 5–7 phút gồm Optimize, λ, xếp lại, sửa tay gây vi phạm | Chạy thử hai lần không lỗi; có video dự phòng |
| J5 | Câu hỏi bảo vệ (mục 8) | Mỗi câu có trả lời ngắn và chỗ dẫn chứng |
| J6 | README: lệnh chạy một lần (`cp .env.example .env`, `docker compose up -d --build`) | Người mới chạy được trong 10 phút |

## 5. Việc cần nhóm quyết

1. **Đã chốt 2026-11-08:** giữ repair D20, bỏ FR-9 (`tulee`); nộp từ `main`.
2. Duyệt đặc tả D1–D20, gồm D20 (repair: tầng "số ca thay đổi" đứng **trước** chi phí).
3. Chấp nhận sai lệch CLAUDE §13 dòng 4 nếu B3 không xong.
4. Xác nhận kịch bản cơ sở D13 (store 18, 30 nhân viên).
5. Thêm Playwright làm dependency cho D1 hay không.
6. Có làm F, H, I không (mỗi mục đổi đặc tả).

## 6. Kiểm tra cho mọi việc

Một việc chỉ tính là xong khi:

- `python scripts/check_conventions.py` sạch (không comment, code chỉ ASCII).
- Engine: ruff, mypy strict, pytest với coverage ≥ 80%.
- Backend: ruff, mypy, pytest gồm integration trên MySQL 8.4, `alembic check`, OpenAPI khớp code.
- Frontend: `npm run ci` (Biome, tsc, vite build).
- Mỗi bất biến mới có test tiêm vi phạm.
- Dependency mới được nhóm đồng ý, ghim bản phát hành ≥ 2 tuần.
- Màn hình mới có hai nguồn đã mở trong phụ lục nguồn UI trong `báo cáo.md`.
- CI trên GitHub xanh trước khi merge vào `main`.

## 7. Checklist duyệt tay UI (D3)

1. Trang chủ mở được; nút giao diện tối đổi được và giữ sau khi tải lại.
2. Nhu cầu: tạo bằng nhập tay, CSV, ingest file doanh số; lưới 7×24 sửa được; tham số `alpha`, `p` hiện rõ; nhãn "doanh số chuẩn hóa, không phải nhu cầu nhân sự".
3. Mẫu ca và Nhân viên: thêm, sửa, xóa; ngày không làm được hiện đúng.
4. Optimize: trạng thái đi từ đang chờ, đang giải tới hoàn tất; hiện status, gap, thời gian; `FEASIBLE` có gap.
5. Lịch: lưới nhân viên × ngày; coverage chart phân biệt thiếu và thừa không chỉ bằng màu.
6. Tuân thủ: lượt solver 0 vi phạm; sửa tay gây vi phạm Đ.110 thì lượt mới thất bại, lượt gốc không đổi.
7. Xếp lại: ngày trước "Xếp lại từ ngày" có nhãn "khóa" và giữ nguyên; ô đổi có chữ "đổi"; KPI "Ca thay đổi"; ngày vắng rơi vào ngày khóa bị từ chối với thông báo rõ.
8. Gợi ý người thay: không có người vắng và người đã có ca ngày đó; Áp dụng tạo lượt mới 0 vi phạm.
9. What-if: kéo λ thấy đường cong; heatmap chi phí biên; dual LP có nhãn "xấp xỉ".
10. Xuất CSV mở được.
11. Lặp lại 4–9 ở giao diện tối.

## 8. Câu hỏi bảo vệ nên chuẩn bị

| Câu hỏi | Trả lời ngắn | Dẫn chứng |
|---|---|---|
| Mô hình có phải quy hoạch nguyên tuyến tính không? | Có: công thức ILP đầy đủ, giải bằng PuLP + HiGHS; CP-SAT giải cùng mô hình nhanh hơn | B1, B3 |
| Vì sao không dùng shadow price của mô hình nguyên? | Bài toán nguyên không có dual hợp lệ; chi phí biên thật tính bằng giải lại; integrality gap đo được | `model.md` mục 5, B5 |
| Làm sao tin lịch đúng luật? | Validator độc lập kiểm lại mọi nghiệm, không import mô hình | `validation.py`, CLAUDE §13 dòng 1 |
| Vì sao lexicographic thay vì trọng số? | Trọng số chọn sai làm đảo thứ tự ưu tiên; có số đo minh họa | B6 |
| Mô hình lớn cỡ nào, giải được tới đâu? | Bảng kích thước và thời gian theo số nhân viên; Curtois & Qu | B4, benchmarks.md mục 1 |
| Tối ưu tốt hơn xếp tay bao nhiêu? | Số đo trên nhiều store | C5 |
| Kết quả có đúng cho store khác không? | Đã chạy 3–5 store; nêu phạm vi | C2–C5 |
| Người báo ốm giữa tuần thì sao? | Xếp lại: khóa ngày đã qua, solver đổi ít ca nhất; tập khóa được validator kiểm trước nên luôn có lời giải | `model.md` mục 6, đặc tả D20 |
| FreshRetailNet có phải dữ liệu nhân sự? | Không; là doanh số chuẩn hóa; `alpha`, `p` là giả định, có quét độ nhạy | `mô tả dữ liệu.md` |
| Ca đêm lấy nhu cầu từ đâu? | Mức tối thiểu cố định, vì doanh số đêm gần bằng 0 | CLAUDE.md nguyên tắc 7 |
| Tuần nối tuần xử lý thế nào? | Hiện quấn vòng; đã nêu giới hạn, hoặc đã sửa ở H | báo cáo mục Hạn chế |
| Vì sao bỏ chế độ tổng đài? | Quyết định D18, giữ một chế độ bán lẻ; đề bài cho phép "tổng đài hoặc cửa hàng 24/7" | đặc tả D18 |

## 9. Rủi ro

| Rủi ro | Cách giảm |
|---|---|
| Thiếu thời gian | Làm đủ P0 trước; E–I vào "Hướng phát triển" |
| MIP theo nhân viên (B2) chậm | Chỉ so trên instance nhỏ; báo cáo đúng phạm vi |
| Store mới (C2) có dữ liệu bất thường | Ghi tiêu chí chọn và loại trừ trong `mô tả dữ liệu.md` |
| H làm hỏng test cũ | Giữ cyclic mặc định, chạy toàn bộ test trước mỗi commit |
| Demo lỗi trên máy chấm | Video dự phòng; dữ liệu seed sẵn bằng service `seed` |
