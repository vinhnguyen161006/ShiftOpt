# worklog.md — Checklist hoàn thành ShiftOpt

Lập ngày 2026-10-26 từ `CLAUDE.md` và trạng thái repo thực tế (khung code đã có, mọi hàm nghiệp vụ còn là stub `NotImplementedError`, `data/` chưa tạo, `docs/đặc tả.md` chưa có).

**Cách dùng:** mỗi task là một khối công việc có đầu ra kiểm chứng được, không phải việc lặt vặt. Tick `[x]` khi **tiêu chí xong** của task đạt, không phải khi code xong. Làm theo thứ tự giai đoạn; trong một giai đoạn có thể song song nếu không ghi phụ thuộc.

**Quy tắc chạy xuyên suốt (áp cho mọi task):**
- Trước khi commit: `python scripts/check_conventions.py`, ruff (format + check), mypy strict, pytest sạch. Không comment, code chỉ ASCII, tiếng Anh.
- Khi triển khai một stub: bỏ `TODO:` khỏi docstring, thay `@pytest.mark.skip` bằng test thật.
- Mọi bất biến mô hình có test **tiêm vi phạm** và kiểm tra validator bắt được, không chỉ test nghiệm đẹp.
- Gặp điểm đụng nguyên tắc bất biến (CLAUDE.md mục 2) hoặc thiếu thông tin: dừng và hỏi, không đoán.

---

## Tổng quan tiến độ

| Giai đoạn | Nội dung | Phụ thuộc | Trạng thái |
|---|---|---|---|
| 0 | Chốt nền: đặc tả, quyết định mở, dữ liệu, tài liệu gốc | — | chưa làm |
| 1 | Engine: lưới thời gian, domain, quy đổi nhu cầu → số người | 0 | xong (Erlang A làm ở 6.2) |
| 2 | Engine: validator độc lập + KPI | 1 | xong (Đ.109 dời sang 3.3) |
| 3 | Engine: lớp solver chung + mô hình tổng hợp (Dantzig) | 1 | xong (3.1–3.3) |
| 4 | Engine: mô hình theo nhân viên (CP-SAT) | 2, 3 | xong (4.1–4.4; phá đối xứng tắt mặc định, phân rã chưa bật tự động) |
| 5 | Engine: phân tích độ nhạy | 3, 4 | xong (5.1–5.3) |
| 6 | Pipeline dữ liệu nhu cầu (FreshRetailNet, tổng đài) | 0, 1 | xong (6.1–6.3; tổng đài công khai còn mở) |
| 7 | Backend: service, job giải, API, test tích hợp | 2–6 | code xong (7.1–7.5); test tích hợp chưa chạy, MySQL80 không khởi động được |
| 8 | Frontend: các màn hình MVP | 7 (OpenAPI) | code xong (8.1–8.7); chưa chạy với backend thật, chưa duyệt trên trình duyệt |
| 9 | Kiểm chứng: benchmark, so sánh solver, tái lập, nghiệm thu | 4, 5, 7, 8 | chưa làm |
| 10 | Hoàn thiện CI, Docker, bảo mật, bật ngưỡng coverage | 9 | chưa làm |
| 11 | Đặc tả cuối, báo cáo, demo | 9 | chưa làm |

Đã xong từ bước dựng khung (không làm lại): dataclass engine, `LaborRules`, settings, ORM model, Pydantic schema, `create_app`, router, React router/layout, Alembic env + migration baseline, Compose, CI, Makefile, pre-commit, `check_conventions.py`, `openapi.json` + `types/api.ts`.

---

## Giai đoạn 0 — Chốt nền tảng

Mục tiêu: không bắt đầu code nghiệp vụ trên giả định chưa được xác nhận (nguyên tắc 14).

- [ ] **0.1 Chốt các quyết định mở, ghi vào `docs/đặc tả.md`**
  - Hỏi nhóm và ghi lại câu trả lời cho: ca đêm tính từ 22h hay theo hợp đồng riêng; giá trị mặc định `alpha`, `p`, `r_min`; một "ngày" bắt đầu lúc mấy giờ; `K` ngày liên tiếp tối đa mặc định (6 hay khác); 48 hay 40 giờ/tuần cho kịch bản cơ sở; doanh thu giả định cho labor cost %; giá trị `M_u`, `lambda_F` và cách chọn.
  - Xong khi: mỗi quyết định có giá trị cụ thể, lý do, người chốt; các hằng này được đưa vào config hoặc `LaborRules`, không còn nằm trong đầu.
- [ ] **0.2 Viết `docs/đặc tả.md` (nguồn sự thật mới) và đồng bộ lại `CLAUDE.md`**
  - Trích điều luật trực tiếp từ văn bản 45/2019/QH14 và NĐ 145/2020 (Đ.98, 105, 106, 107, 109, 110, 111), không qua trang thứ cấp; xác nhận lại khung đêm thuộc Đ.106.
  - Viết yêu cầu chức năng, tiêu chí nghiệm thu, phạm vi (theo CLAUDE.md mục 13–14) thành văn bản có thể kiểm chứng.
  - Xong khi: đặc tả được nhóm duyệt; `CLAUDE.md` được cập nhật khớp, ghi rõ chỗ nào đặc tả thắng.
- [ ] **0.3 Dọn tài liệu gốc và thư mục dữ liệu**
  - Chuyển `Báo cáo nghiên cứu nền Xếp ca nhâ.md` vào `docs/` (hiện không có trong git), sửa link trong CLAUDE.md.
  - Tạo `data/raw/` (gitignore), `data/processed/`, `data/benchmarks/curtois_qu/`; kiểm tra `.gitignore`.
  - Xong khi: cấu trúc khớp CLAUDE.md mục 11, `git status` sạch, không file dữ liệu thô nào bị track.
- [x] **0.4 Chốt ADR-002 thư viện biểu đồ**
  - So sánh tối thiểu 2 ứng viên trên đúng nhu cầu của dự án: cột + đường chồng (coverage), heatmap 24 ô (chi phí biên), đường cong `z(lambda)`. Tiêu chí: kích thước bundle, hỗ trợ React 19, khả năng tô màu theo điều kiện (đỏ thiếu / xanh thừa), a11y.
  - Xong khi: ADR-002 có trạng thái "đã chốt", dependency được ghim chính xác, bản phát hành ≥ 2 tuần tuổi.
  - Đã chốt (2026-10-28): không dùng thư viện, tự vẽ bằng HTML/CSS và SVG như trang chủ; không có dependency mới.

---

## Giai đoạn 1 — Engine: nền thời gian và quy đổi nhu cầu

Mục tiêu: mọi phép tính giờ/ca/nhu cầu có một nguồn duy nhất, thuần và tất định. Các giai đoạn sau đều dựa vào đây.

- [x] **1.1 Hoàn thiện `time_grid.py` và `domain.py` (phần còn stub)**
  - `hour_of_week` quấn vòng mod 168; `shift_hours` tính giờ-trong-tuần của ca, ca qua nửa đêm sang ngày sau, ca Chủ nhật quấn về thứ Hai; `covers_hour` là `a_tj` cho chu kỳ 24 và 168; `night_hours_in_shift` và `ShiftType.night_hours` là nguồn duy nhất cho giờ đêm 22h–06h (Đ.106); `ShiftType.cost_per_wage_unit` theo Đ.98 khoản 2; `Instance.shift_by_name` raise `KeyError` khi tên lạ. Các `validate` trong `__post_init__` đã có sẵn từ trước, không cần viết thêm.
  - Test (`test_time_grid.py`, `test_smoke.py`): ca 22h–06h, ca 14h–22h, ca bắt đầu 0h, quấn vòng tuần, `L` khác 8, số giờ đêm từng ca, phí ca 980 cho ca đêm 0h.
  - Xong khi: đạt. Không còn stub trong hai file; test pass; mọi giờ đêm đi qua `night_hours_in_shift`.
- [x] **1.2 Quy đổi tuyến tính `staffing/linear.py`**
  - `r = max(floor_h, ceil(alpha * D / p))`; `floor_h` là `night_min_staff` trong khung đêm lấy từ `LaborRules`, ngược lại `min_staff`. Mặc định là placeholder `DEFAULT_*` chờ quyết định 0.1, backend import các hằng này. Từ chối `alpha <= 0`, `productivity <= 0`, tải âm hoặc NaN, sai độ dài. Làm tròn `ceil` với dung sai 9 chữ số để `0.1 * 30` ra 3 chứ không ra 4.
  - Test (`test_kpi_and_staffing.py`): ceil và floor theo ví dụ tay, bẫy số thực, từ chối đầu vào sai, mọi ô `>= floor`, đơn điệu theo `alpha`.
  - Xong khi: đạt. Hàm thuần, không I/O, test pass.
  - Ghi chú: `r_min` trong CLAUDE.md đổi tên thành `min_staff` và `night_min_staff` để khớp `ConversionParams`.
- [x] **1.3 Quy đổi tổng đài `staffing/erlang.py` (Erlang C và square-root)**
  - Đã làm: Erlang C bằng đệ quy Erlang B (không giai thừa, không tràn số); `required_staff_erlang_c` tìm số người nhỏ nhất đạt service level mục tiêu (mặc định 80/20, đơn vị giây); `required_staff_square_root` cho `N = R + beta * sqrt(R)`. Cả hai nhận `min_staff` để giờ không có cuộc gọi vẫn có người trực.
  - **Lệch so với CLAUDE.md:** Erlang A (có khách bỏ cuộc, ưu tiên hơn Erlang C) chưa làm, dời sang task 6.2. Lý do: Erlang A cần chuỗi sinh-tử và tính phân phối thời gian chờ bằng số, khó kiểm chứng bằng giá trị tham chiếu nên không đưa vào giai đoạn 1.
  - Test: đối chiếu Erlang C với oracle dùng phân số chính xác (`fractions.Fraction`), số người đạt target và `n - 1` không đạt, tải lớn `a = 2000` không tràn số, square-root theo công thức, từ chối đầu vào sai.
  - Xong khi: đạt cho Erlang C và square-root; Erlang A còn mở ở 6.2.

---

## Giai đoạn 2 — Engine: validator độc lập và KPI

Mục tiêu: thực thi nguyên tắc 1. Làm **trước** các mô hình để có "trọng tài" kiểm mọi nghiệm sau này. Chỉ phụ thuộc `domain.py`, `time_grid.py`, `labor_law_vn.py`.

- [x] **2.1 `validation.py` kiểm tra hậu nghiệm mọi ràng buộc cứng**
  - Kiểm trên **trục giờ** quấn vòng: tối đa 1 ca/ngày (`MULTIPLE_SHIFTS_PER_DAY`); ≤ 8 giờ/ngày (`DAILY_HOURS`), ≤ 48 giờ/tuần (`WEEKLY_HOURS`, Đ.105); nghỉ ≥ 12 giờ giữa hai ca (`REST_BETWEEN_SHIFTS`, Đ.110, công thức tổng quát, khoảng nghỉ tính từ ca cuối tuần sang ca đầu tuần); nghỉ dài nhất ≥ 24 giờ mỗi tuần (`WEEKLY_REST`, Đ.111, bắt được bẫy ca qua đêm); tối đa `K` ngày liên tiếp quấn qua Chủ nhật (`CONSECUTIVE_DAYS`).
  - Trả `Violation(kind, employee_id, detail, day)`; `LEGAL_BASIS` ánh xạ loại sang điều luật cho UI. Không import `models/` hay `solvers/` (test bằng `ast`).
  - Test (`test_validation.py`): nghỉ 8 giờ, nghỉ quấn qua Chủ nhật → thứ Hai, 7 ngày liên tiếp, chuỗi qua biên tuần, 6 ngày được phép, 49 giờ/tuần, giờ/ngày, bậc thang nghỉ 20 giờ, bẫy nghỉ 22 giờ (ca 22h ngày 0 + nghỉ ngày 1), hai ca một ngày, mã lạ, ca đêm hợp lệ nghỉ đúng 24 giờ không bị báo, nhân viên kiểm tra độc lập. Mỗi kịch bản "chỉ có X" assert đúng loại vi phạm.
  - **Chưa làm (dời sang 3.3):** Đ.109 nghỉ giữa giờ. `Solution` không có vị trí nghỉ, nên validator không kiểm được. Thêm 30 phút (45 phút ca đêm) vào `LaborRules` để có một nguồn duy nhất.
  - Xong khi: đạt cho các luật ở trên. Coverage `validation.py` 100%.
- [x] **2.2 `kpi.py` theo định nghĩa chính xác**
  - Đã làm: `staff_by_hour`, `labor_cost` (wage × `cost_per_wage_unit`, đơn vị phần trăm đơn vị lương), `night_premium_cost`, `labor_cost_share` (doanh thu giả định do caller truyền, ≤ 0 raise), `compute_kpi` gồm coverage, giờ thiếu/thừa, efficiency, độ lệch chuẩn ca đêm và ca cuối cùng tuần.
  - Quy ước đã chốt: **ca đêm** = quá nửa số giờ nằm trong 22h–06h (`ShiftType.is_night_shift`); **ca cuối tuần** = bắt đầu thứ Bảy hoặc Chủ nhật (`WEEKEND_DAYS`); độ lệch chuẩn tính trên mọi nhân viên, kể cả người không có ca loại đó.
  - Quy ước dùng theo docstring: tỷ số có mẫu số bằng 0 cho 1.0. Hệ quả: lịch rỗng với nhu cầu > 0 có `schedule_efficiency = 1.0`, dù coverage là 0.0. Đây là quy ước của docstring gốc, chưa phải lựa chọn đã được nhóm duyệt; nếu nhóm muốn 0.0 thì đổi ở `_ratio` và test.
  - Số vi phạm cứng không nằm trong `Kpi`: caller (backend 7.2) tính `len(validate(...))`, để `kpi.py` không phụ thuộc `validation.py`.
  - Test: ví dụ tay (ca 8h: coverage 8/168, thiếu 160, efficiency 21, cost 100 × 800), ca 00h có phụ cấp đêm, ca 22h quấn về thứ Hai, công bằng ca đêm (ca 16h không tính) và ca cuối tuần, mẫu số bằng 0.
  - Xong khi: đạt cho các KPI trong CLAUDE.md 9.1 trừ "Dự báo" (giai đoạn 6) và "Kỹ thuật" (do backend).
- [x] **2.3 Rà soát `LaborRules` làm nguồn duy nhất cho hằng pháp lý**
  - Đã làm: `LaborRules` có thêm `min_break_minutes` (30) và `min_night_break_minutes` (45). Grep `engine/src` không còn ngưỡng luật nằm ngoài `LaborRules`; các số còn lại chỉ nằm trong docstring và thông báo lỗi. Ngưỡng ca đêm đi qua `rules.night_start/night_end`.
  - Test: đổi `max_weekly_hours` từ 48 sang 40 làm cùng lịch 6×8 giờ chuyển từ sạch sang `WEEKLY_HOURS`; `night_premium_percent` đổi thì phí ca đêm đổi theo.
  - Xong khi: đạt cho `engine/`. Chưa rà `backend/` và `frontend/` ở mức này, vì hai bên chưa có logic luật (grep không có con số luật).

---

## Giai đoạn 3 — Engine: lớp solver chung và mô hình tổng hợp (Dantzig)

Mục tiêu: có đường đi LP/MIP hoàn chỉnh, có đáp án tay, làm nền cho dual và độ nhạy.

- [x] **3.1 Lớp solver chung: `solvers/base.py`, `cpsat.py`, `pulp_backend.py`**
  - Đã làm: `SolveParams` có `log_search_progress`; `SolveResult` có `solver_version` và `log`; `relative_gap` là nguồn duy nhất cho gap; `ModelInvalidError` raise khi solver báo model lỗi (không trả status). `run_cp_model` (CP-SAT) và `run_problem` (PuLP + HiGHS) cùng một kiểu kết quả. Trạng thái HiGHS lấy từ `getModelStatus()` vì PuLP status không phân biệt được nghiệm hết giờ với tối ưu đã chứng minh.
  - Đã xác minh API: `pulp.HiGHS(... random_seed=...)` truyền xuống `setOptionValue`; cận dưới MIP từ `getInfo().mip_dual_bound`.
  - Cảnh báo PuLP: code dùng `add_variable`, `problem += expr >= rhs, name` và `get_constraint_by_name`, không kích hoạt cảnh báo PuLP 4. `pyproject.toml` đổi filter: thay vì nuốt mọi `DeprecationWarning` của pulp, chỉ coi cảnh báo "PuLP 4.0" là lỗi.
  - `SolveParams` (time limit, gap, workers, seed, log) và `SolveResult(status, objective, bound, gap, wall_time_seconds, solver)` dùng chung hai backend; map status về `OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN/MODEL_INVALID`; gap = `|obj - bound| / max(1, |obj|)`; `MODEL_INVALID` là lỗi lập trình, không trả như lỗi người dùng; ghi tên + phiên bản solver (nguyên tắc 10).
  - PuLP dùng `pulp.HiGHS`, không `PULP_CBC_CMD`; xử lý `DeprecationWarning` PuLP 3.3.2 có chủ đích, không im lặng.
  - Test: mô hình đồ chơi có đáp án biết trước trên cả hai backend; time limit cực nhỏ trả `FEASIBLE`/`UNKNOWN` kèm bound; infeasible nhận diện đúng.
  - Xong khi: hai backend trả cùng kiểu kết quả, test pass.
- [x] **3.2 Mô hình phủ tập Dantzig `models/set_covering_pulp.py`**
  - Đã làm: biến nguyên `x[d, s]` cho ca dài tối đa `max_daily_hours`; chi phí `wage * cost_per_wage_unit(s)` (dùng lại hàm sẵn có, không viết công thức `0.3 * wage` thứ hai, đơn vị phần trăm đơn vị lương); phủ từng giờ quấn vòng 168; `relax=True` cho LP và trả dual theo giờ (`get_constraint_by_name(...).pi`, có thể `None`).
  - Test (`test_set_covering.py`): 3 ca 0/8/16 nhu cầu 1 → 21 ca, objective `7 * 100 * (2400 + 30 * 8)`; nhu cầu 2 → 42 ca; nhu cầu 0 → 0; ca 10 giờ bị loại → INFEASIBLE; 168 dual không âm; LP ≤ nguyên.
  - Xong khi: đạt. Ví dụ có đáp án tay là ví dụ 3 ca ở trên, lời giải ghi trong test.
- [x] **3.3 Nghỉ giữa ca ngầm `models/implicit_breaks.py` (biến thể Bechtold–Jacobs)**
  - Đã làm: `LaborRules.break_required_from_hours = 6` (placeholder, phải đối chiếu văn bản 45/2019 ở task 0.2); `ShiftType.break_window` là offset 1 đến L-2. Mỗi người của ca cần nghỉ được đếm một lần trong `x` và một lần trong một khe nghỉ `y[d, s, k]`; nghỉ làm mất đúng một giờ phủ. Nghỉ 30/45 phút tính trọn một giờ, là xấp xỉ bảo thủ.
  - Test: oracle liệt kê đầy đủ cột (ca, vị trí nghỉ) bằng HiGHS, objective phải khớp với mô hình ngầm trên instance đều và instance có nhu cầu đỉnh; nghỉ không làm rẻ hơn mô hình không nghỉ.
  - Xong khi: đạt; ghi trong `docs/model.md` mục 1b.

---

## Giai đoạn 4 — Engine: mô hình theo nhân viên (CP-SAT)

Mục tiêu: lõi sản phẩm — lịch thật, mọi ràng buộc cứng pháp lý, luôn khả thi nhờ biến thiếu người.

- [x] **4.1 Ràng buộc chuỗi và công bằng: `constraints/sequences.py`, `constraints/fairness.py`**
  - Đã làm: `rest_hours(prev, next, day_offset)` là công thức tổng quát duy nhất (không dùng rút gọn `sigma - sigma' > 4`); `forbidden_shift_pairs` trả bộ ba (ca trước, ca sau, offset 1–6) theo vòng tuần; `consecutive_day_windows` là cửa sổ `K+1` ngày quấn vòng; `night_shift_spread` = max − min số ca đêm trên mọi nhân viên (cùng định nghĩa với CP-SAT).
  - Lệch có chủ đích: model tối thiểu hóa max − min (tuyến tính), KPI báo độ lệch chuẩn (mô tả). Hai đại lượng khác nhau, không thay thế nhau.
  - Test: cặp 14h → 06h bị cấm; công thức tổng quát với ca dài khác 8; cửa sổ `K = 4` bắt đầu thứ Bảy là `(5, 6, 0, 1, 2)`; **đối chiếu với validator**: với mọi cặp ca và offset 1–6, cặp bị cấm khi và chỉ khi validator báo `REST_BETWEEN_SHIFTS` ở ngày đó.
  - Xong khi: đạt.
- [x] **4.2 `models/roster_cpsat.py`: biến, ràng buộc cứng, coverage mềm, mục tiêu**
  - Đã làm: `work[e,d,s]`, `breaks[e,d,s,k]`, `shortfall[h]` (nguyên, trong `[0, r_h]`), `rest_start[e,t]` cho cửa sổ nghỉ 24 giờ. Ràng buộc cứng: tối đa 1 ca/ngày, giờ/tuần theo từng nhân viên, nghỉ 12 giờ theo offset 1–6, số ngày liên tiếp, nghỉ 24 giờ liên tục trên trục giờ, mỗi ca cần nghỉ có đúng một khe nghỉ, không xếp ca vào ngày không làm được. Coverage mềm luôn khả thi.
  - Mục tiêu lexicographic 4 tầng (thiếu người → chi phí → chênh ca đêm → vi phạm mong muốn), mỗi tầng một lần giải CP-SAT, tầng sau bị chặn bởi tối ưu tầng trước; tầng bỏ qua nếu không có điều kiện tương ứng. `OPTIMAL` chỉ khi mọi tầng `OPTIMAL`.
  - Lỗi đã bắt được trong quá trình làm (ghi lại vì là bài học): (1) giới hạn giờ/tuần ban đầu cộng toàn đội vào một ràng buộc `≤ 48`, nên cả đội chỉ được 6 ca; sửa theo từng nhân viên; (2) thiếu `AtMostOne` một ca/ngày, validator báo `MULTIPLE_SHIFTS_PER_DAY` ngay trong test.
  - Test (`test_roster_cpsat.py`): đủ người → thiếu = 0, tầng 1 `OPTIMAL`, validator rỗng; thiếu người (3 nhân viên) → thiếu ≥ 42 giờ, tính tay: tối đa 6 ca × 3 người = 18 ca, mỗi ca 8 giờ trừ 1 giờ nghỉ = 126 giờ có người, 168 − 126 = 42; cùng seed + 1 worker → cùng objective; ca 14h rồi 06h không bao giờ cùng nhân viên (thiếu đúng 1 giờ); lexicographic ưu tiên thiếu người hơn chi phí; yêu cầu ngày không làm được và ngày nghỉ mong muốn; ngẫu nhiên 2 instance nhỏ → validator rỗng.
  - Số đo scale (`benchmarks/run_roster_scale.py`, seed 0, giới hạn 60 giây, 1 worker, không phá đối xứng): 20 nhân viên `OPTIMAL` 8,7 s; 30 `OPTIMAL` 15,5 s; 40 `OPTIMAL` 22,2 s; 0 vi phạm, 0 giờ thiếu. Đây là một instance và một seed, chưa phải kết luận chung.
  - Xong khi: đạt cho 20–40 nhân viên ở instance benchmark; validator 0 vi phạm; nghiệm trên instance khác vẫn cần đo thêm (task 9.4).
- [x] **4.3 Phá đối xứng cho nhóm đồng nhất**
  - Đã làm: `symmetry_pairs` chỉ ghép nhân viên cùng lương và không có yêu cầu (nguyên tắc 12); ràng buộc `shifts_e >= shifts_{e+1}`. Tham số `symmetry_breaking`, **mặc định tắt**.
  - Lý do tắt: đo trên benchmark 20/30/40 nhân viên, bật làm chậm hơn (12,7 s so với 8,7 s; 24,3 s so với 22,2 s ở 20 và 40 nhân viên cùng seed và 1 worker). Đây là một seed; cần đo thêm trước khi đổi mặc định.
  - Test: objective bằng nhau khi bật/tắt (cả hai `OPTIMAL`); nhân viên có yêu cầu không được ghép cặp.
  - Xong khi: test tương đương pass; mức giảm thời gian không đạt, ghi lại như trên và giữ tính năng tắt.
- [x] **4.4 Phân rã hai pha (khi instance lớn)**
  - Đã làm: `solve_roster(..., decompose=True)` giải mô hình tổng hợp có nghỉ ngầm (3.3) trong nửa thời gian, lấy số ca mỗi (ngày, loại ca), giới hạn `ceil(count)` cho mô hình nhân viên. Kết quả gắn `approximate=True`, status không bao giờ `OPTIMAL` (tối đa `FEASIBLE`).
  - Chưa bật tự động. Ngưỡng tự bật sẽ đặt sau khi có số đo ở 9.4 cho thấy một pha không đạt 60 giây với gap 1%.
  - Test: nghiệm qua validator rỗng; cờ `approximate` đúng; status không `OPTIMAL`.
  - Xong khi: đạt về tính đúng. Chưa đo được lợi về thời gian giải trên instance lớn (sẽ đo ở 9.4).

---

## Giai đoạn 5 — Engine: phân tích độ nhạy

Mục tiêu: thực thi nguyên tắc 4 và 5 — độ nhạy nguyên bằng giải lại, dual chỉ từ LP và gắn nhãn xấp xỉ.

- [x] **5.1 Quét tham số `sensitivity/parametric.py`**
  - `lambda` trong `{0.8, ..., 1.3}`, `r_t(lambda) = tolerant_ceil(lambda * r_t)`; `sweep_demand_multiplier` trả `SweepPoint(multiplier, evaluation, proven)`; `Evaluation` mang chi phí, giờ thiếu, giờ đã xếp. Hai resolver: `aggregate_resolver` (mô hình có nghỉ ngầm) và `roster_resolver` (CP-SAT, chi phí tính bằng `kpi.labor_cost`).
  - **Chi phí biên rời rạc** `z(r + e_t) - z(r)` bằng 168 lần giải lại (một lần mỗi giờ), không dùng dual. `proven` chỉ đúng khi cả hai lần giải `OPTIMAL`.
  - Test: `z(lambda)` không giảm; `1.1 * 10 -> 11`; điểm `FEASIBLE` có `proven = False`; chi phí biên ví dụ tay (3 ca 0/8/16, nhu cầu 1, không nghỉ: giờ 3 = `100 * 980`); 168 giá trị đều không âm khi `OPTIMAL`.
  - Đo: 168 lần giải lại trên instance 3 ca, nhu cầu 1, mô hình không nghỉ: khoảng 5.5 giây, 168/168 `OPTIMAL`, cấu hình `num_workers = 1`, seed 0.
  - Xong khi: đạt. Kết quả tái lập với cùng seed (`num_workers = 1`); điểm không `OPTIMAL` được đánh dấu `proven = False`.
- [x] **5.2 Dual của LP relaxation `sensitivity/lp_duals.py`**
  - `lp_relaxation_duals` lấy dual từ bản relax của mô hình có nghỉ ngầm (cùng mô hình với chi phí biên); `normalize_duals` đổi `None` thành `0.0` và liệt kê giờ thiếu; `LpDuals` luôn có `approximate = True` và nhãn "xấp xỉ, integrality gap có thể lớn"; LP không `OPTIMAL` thì raise.
  - Thay "cố định biến nguyên rồi giải lại LP" bằng `compare_duals_with_marginal_cost`: 168 dòng `(giờ, dual LP, chi phí biên, proven)`. Lý do: khi mọi biến đều nguyên, cố định hết thì LP không còn biến tự do và dual suy biến.
  - Test: đối ngẫu mạnh `sum(pi * r) = objective LP`; `None` được chuẩn hóa; nhãn luôn có; bảng so sánh có 168 dòng. Dual không bao giờ lấy từ CP-SAT hoặc MIP.
  - Xong khi: đạt (không có đường trình bày dual MIP như chi phí biên).
- [x] **5.3 Kịch bản theo covariate `sensitivity/scenarios.py`**
  - `DemandScenario(name, day_multipliers, source)`; `apply_demand_scenario` nhân nhu cầu theo ngày bằng `tolerant_ceil`, trả instance mới (bất biến). `promotion_scenario` dùng `PROMOTION_UPLIFT = 1.43` với nguồn ghi rõ. Ngày lễ và mưa không có số mặc định: người gọi tự truyền hệ số và nguồn.
  - `compare_scenarios` trả baseline cùng các kịch bản. `sweep_staffing_assumption` dựng lại nhu cầu bằng `required_staff` cho từng giá trị của `alpha`, `productivity`, `min_staff`, `night_min_staff` (hai floor phải là số nguyên), rồi giải lại: đây là độ nhạy theo giả định quy đổi.
  - Test: instance gốc không đổi; chỉ ngày được chọn bị đổi; ngày sai hoặc hệ số `<= 0` bị từ chối; quét `alpha` tăng thì chi phí tăng.
  - Xong khi: đạt. So sánh kịch bản trên cùng instance; giả định hiện trong `source` và trong kết quả quét.

---

## Giai đoạn 6 — Pipeline dữ liệu nhu cầu

Mục tiêu: dữ liệu vào đúng, giả định minh bạch (nguyên tắc 6, 7, 8).

- [x] **6.1 Nạp và xử lý FreshRetailNet-50K (`backend/src/demand/dataset_loader.py` + hàm xử lý thuần)**
  - Tải `Dingdong-Inc/FreshRetailNet-50K` vào `data/raw/` (có script, không commit); xác nhận bằng `dt.min()/max()` split eval 7 ngày thay vì suy luận; cộng `hours_sale` theo (`dt`, giờ) cho một `store_id`/`city_id` → `D[d,h]`; xuất `data/processed/demand_store_<id>.parquet`.
  - **Nhu cầu ẩn:** giờ `hours_stock_status = 1` thay bằng trung bình cùng giờ, cùng thứ, loại giờ hết hàng; ghi phương pháp trong metadata kết quả.
  - Gắn nhãn trong dữ liệu trả về: "doanh số chuẩn hóa của kho tiền phương", không phải nhu cầu nhân sự hay cửa hàng vật lý 24/7. Ghi "~863–865 SKU" khi trích dẫn.
  - Test trên dữ liệu mẫu nhỏ cố định: cộng đúng, thay hết hàng đúng, giờ đêm không suy từ doanh số (dùng `r_min`).
  - Xong khi: một store xử lý end-to-end ra lưới 7×24 và `r[d,h]`; metadata ghi rõ phương pháp, `alpha`, `p`, `r_min`.
  - Đã làm: `engine/src/shiftopt/staffing/latent_demand.py` (`ProductDay`, `weekly_load`: nhu cầu ẩn theo từng sản phẩm, giờ đêm bằng 0); `backend/src/demand/dataset_loader.py` (`build_processed_store`, `load_hourly_load`, `dataset_required_staff`); `backend/scripts/download_freshretailnet.py` (tải vào `data/raw/`, kiểm SHA-256 ghim theo LFS oid của Hugging Face, bỏ qua file đúng hash); `backend/scripts/build_demand_store.py`. Thêm `pyarrow==26.0.0` (phát hành 2026-10-09, đủ 2 tuần tuổi); `data/processed/*.parquet` vào `.gitignore`.
  - Lệch so với kế hoạch: `ProductDay` nhận `day: date` thay cho `weekday`, để đếm số ngày mỗi thứ khi lấy trung bình. Nhu cầu lấy từ split `train`; split `eval` giữ lại làm tập đánh giá.
  - Đã xác minh bằng `dt.min()/max()`: `train` 2024-03-28 .. 2024-06-25 (90 ngày), `eval` 2024-06-26 .. 2024-07-02 (7 ngày). Hash file local khớp LFS oid trên Hugging Face.
  - Chạy thật store 18: 164 sản phẩm; ô hết hàng được thay bằng trung bình 90159 ô; 1008 ô không có ngày không hết hàng để học nên giữ doanh số quan sát; 56 giờ đêm đặt 0. `build_demand_store` mất khoảng 2,7 giây (gồm cả khởi động uv).
  - Test: `test_latent_demand.py` (11), `test_dataset_loader.py` (4).
- [x] **6.2 Dữ liệu tổng đài** (kèm Erlang A, dời từ 1.3: thêm hàm Erlang A với chuỗi sinh-tử, kiểm tra Erlang A cho số người ≤ Erlang C trên cùng lưu lượng)
  - Bộ giả lập lưu lượng cuộc gọi theo giờ có seed cố định (mô hình ngày/tuần, đỉnh buổi); tùy chọn nạp dataset công khai (ngân hàng Đông Bắc Mỹ, SEELab Technion) nếu giấy phép cho phép.
  - Xong khi: cùng seed cho cùng lưu lượng; đi qua Erlang A ra `r[d,h]` hợp lý.
  - Đã làm: `erlang_a_queue_probabilities` (chuỗi sinh-tử M/M/n+M, tính trong miền log), `erlang_a_service_level` (xác suất thời gian chờ ảo không quá `answer_seconds`, theo Garnett, Mandelbaum và Reiman 2002), `required_staff_erlang_a` (tìm n nhỏ nhất: nhân đôi rồi chia đôi). Thời gian chờ ảo bỏ qua việc chính khách tự bỏ, nên khớp Erlang C khi patience → ∞. `patience_seconds` không có mặc định: là giả định của nhóm.
  - Đã làm: `simulate_arrival_rates` (168 tốc độ đến, seed cố định, mọi tham số ngày/đỉnh/nhiễu là giả định, không phải dữ liệu quan sát). Mô-đun được miễn S311 trong `engine/pyproject.toml` vì là mô phỏng có seed, không phải bảo mật.
  - Kiểm: patience → ∞ khớp `erlang_c_service_level` (sai số 1e-6); số người Erlang A ≤ Erlang C trên cả 168 giờ của lưu lượng thử; tổng xác suất trạng thái = 1.
  - Chưa làm: dataset tổng đài công khai (ngân hàng Đông Bắc Mỹ, SEELab Technion) vì chưa kiểm giấy phép. Để mở, cần quyết định của nhóm.
  - Test: `test_erlang_a.py`, `test_call_arrivals.py`.
- [x] **6.3 Nhập từ người dùng: lưới 7×24 và CSV**
  - Validate ở biên: đủ 168 ô, số nguyên không âm, giới hạn trên hợp lý; thông báo lỗi có nghĩa ("demand grid must have 168 cells"); parser CSV chịu được dòng trống, dấu phân cách, BOM.
  - Xong khi: test các trường hợp biên (167/169 ô, âm, số thực, quá lớn) trả lỗi đúng.
  - Đã làm: `DemandProfileCreate.required_staff` là `list[StrictInt]`, cận `MAX_HOURLY_DEMAND = 1000`, thông điệp "demand grid must have 168 cells". Kiểm độ dài bằng validator `mode="before"` để `minItems`/`maxItems` vẫn nằm trong OpenAPI; `openapi.json` không đổi. `parse_demand_csv` (`backend/src/demand/csv_import.py`) nhận BOM, dòng trống, dòng tiêu đề, dấu `,` `;` tab, dấu phân cách cuối, CRLF; chấp nhận lưới 7×24 hoặc một cột 168 giá trị; lỗi báo dòng và cột.
  - Test: `test_csv_import.py`, `test_demand_schema.py`.
  - Sửa sau review (10/2026): (1) vòng Poisson của Erlang A có số bước tối đa, không còn treo khi thời gian trả lời lớn (đo: 2,4 giây thay vì treo); (2) `patience_seconds` tối đa 3600 giây, và tìm số người Erlang A trong `[1, n_C]` (không nhân đôi từ 1); (3) khung đêm không còn chốt lúc build: `weekly_load` giữ tải đêm, `zero_night_load` áp theo `LaborRules` của người gọi, metadata ghi `night_start`, `night_end`, `night_hours_floored`; (4) test roster của phase 5 so khớp một nghiệm đã giải, không giải hai lần; (5) `dataset_dir` mặc định `../data/processed` (backend chạy từ `backend/`); (6) CSV nhận dòng nhãn giờ `0..23` và dò dấu phân cách trên toàn bộ dòng; (7) đỉnh Gaussian dùng khoảng cách vòng; (8) revision HF chỉ khai báo ở `dataset_loader.py`; (9) cận 0..1000 nằm trong `Annotated[StrictInt, Field(...)]`, OpenAPI có `minimum`/`maximum`.

---

## Giai đoạn 7 — Backend: service, job giải, API

Mục tiêu: nối engine vào HTTP đúng quy tắc: router mỏng, solver không chạy trên event loop, job tái lập được.

- [ ] **7.1 CRUD domain: `demand`, `employees`, `shifts` (`service.py`)**
  - Hoàn thiện các hàm service stub (list/get/create/update/delete) với validation Pydantic v2 tại biên, giới hạn kích thước (`Settings.max_employees`…), lỗi nghiệp vụ qua `AppError` (`NotFoundError`, `ConflictError`, `InstanceTooLargeError`), không lộ stack trace.
  - Tích hợp 6.1–6.3: tạo profile nhu cầu từ FreshRetailNet / CSV / tay / tổng đài, lưu `alpha`, `p`, `r_min`, phương pháp ẩn vào profile.
  - Xong khi: test tích hợp (MySQL thật) cho từng domain, kể cả đường lỗi 404/409/422.
- [ ] **7.2 Job giải: `schedules/service.py`, `dependencies.py`**
  - `POST` tạo hàng `solve_runs`, trả `job_id` ngay; chạy trong `ProcessPoolExecutor` có time limit (`Settings.max_solve_seconds`, `solve_workers`); frontend poll `GET`.
  - Lưu đủ tái lập (nguyên tắc 10): instance đầu vào, tham số, tên + phiên bản solver, `random_seed`, `num_workers`, time limit, status, objective, bound, gap, wall time, log solver.
  - **Mọi nghiệm qua `validation.py` trước khi lưu**; vi phạm cứng > 0 thì đánh dấu run lỗi, không trình bày như thành công. Lịch bất biến: sửa tay tạo bản mới + chạy lại validator.
  - Khi backend khởi động lại: job `running` → `failed` với lý do rõ (lifespan hook).
  - Endpoint KPI và compliance cho một run.
  - Xong khi: test tích hợp end-to-end tạo job → poll → nhận lịch + KPI + vi phạm; test restart đánh dấu `failed`; chứng minh event loop không bị chặn (request khác vẫn phản hồi khi đang giải).
- [ ] **7.3 Phân tích độ nhạy: `analysis/service.py`**
  - Ba loại job (`demand_sweep`, `marginal_cost`, `lp_duals`) trong `analysis_runs`, cùng cơ chế job như 7.2; kết quả mang cờ `OPTIMAL/FEASIBLE` từng điểm và nhãn "xấp xỉ" cho dual; quét 24 giờ chạy hợp lý trong time limit tổng.
  - Xong khi: test tích hợp từng loại job; schema trả đủ trường để UI vẽ đường cong, heatmap, cảnh báo.
- [ ] **7.4 Xuất CSV và sửa tay lịch**
  - Endpoint xuất CSV lịch/KPI; endpoint sửa tay tạo bản lịch mới + chạy validator, trả vi phạm (Đ.105/110/111).
  - Xong khi: sửa tay tạo run mới không đụng run cũ; vi phạm được phát hiện test bằng lịch cố ý sai.
- [ ] **7.5 Cố định hợp đồng API và sinh lại OpenAPI**
  - `make openapi`, `npm run gen:api`; CI kiểm tra khớp. Thêm migration Alembic nếu đổi model (autogenerate → review tay MySQL → bỏ comment → `alembic check`).
  - Xong khi: `openapi.json` và `types/api.ts` khớp code; không còn endpoint stub trả `NotImplementedError`.
  - Trạng thái (chưa tick vì tiêu chí "test tích hợp MySQL" chưa đạt): code 7.1–7.5 đã viết; `ruff`, `mypy` strict, `check_conventions`, `npm run ci` đạt; unit test 45 pass; 19 test tích hợp bị skip vì thiếu `SHIFTOPT_TEST_DATABASE_URL`. Migration `89510c048e94` sinh bằng SQLite tạm, chưa review trên MySQL thật, chưa chạy `alembic check`.
  - Mới: `backend/src/jobs.py` (ProcessPoolExecutor, `run_in_child`), `schedules/snapshot.py`, `schedules/worker.py`, `analysis/worker.py`; endpoint `POST /demand-profiles/from-csv`, `from-call-center`, `DELETE /demand-profiles/{id}`, `POST /schedules/{id}/edits`, `GET /schedules/{id}/{assignments,coverage,kpi}.csv`.
  - Lệch so với kế hoạch: độ nhạy quét 168 giờ (không 24); giới hạn đầu vào của job độ nhạy kiểm trên từng lần giải (`time_limit_seconds`), còn tổng thời gian job là `max_analysis_seconds`; `LaborRules` qua API chỉ đổi `max_weekly_hours` và `max_consecutive_days`; sửa tay có vi phạm cứng → run `failed` kèm lý do; `objective` của run roster là giá trị tầng cuối của lexicographic, chi phí lấy từ KPI.
  - Việc còn mở: chạy test tích hợp và `alembic check` trên MySQL 8.4; giết tiến trình con khi quá hạn (hiện chỉ bỏ chờ, CP-SAT tự dừng theo time limit).

---

## Giai đoạn 8 — Frontend: các màn hình MVP

Mục tiêu: luồng "nhập nhu cầu → Optimize → xem lịch, coverage, cảnh báo, chi phí → kéo λ" chạy được. Không import chéo giữa feature; kiểu TypeScript sinh từ OpenAPI.

- [ ] **8.1 Nền UI: `lib/api-client.ts`, `components/ui/*`, `config/env.ts`**
  - `apiFetch` có xử lý `ApiError` theo mã/thông điệp backend; `Button`, `Table`, `Modal`, `Slider` đủ dùng, truy cập được (bàn phím, nhãn); trạng thái loading/error/empty thống nhất.
  - Xong khi: không còn `throw new Error("TODO...")` trong nền; `npm run ci` sạch.
- [ ] **8.2 Màn Nhu cầu: `features/demand`**
  - Lưới 7×24 chỉnh trực tiếp, import CSV, "tạo từ FreshRetailNet store X"; **form tham số chuyển đổi hiển thị `alpha`, `p`, `r_min`** và hiển thị nhãn "doanh số chuẩn hóa, không phải dữ liệu nhân sự" (nguyên tắc 6); chọn chế độ bán lẻ / tổng đài.
  - Xong khi: tạo, sửa, lưu được profile; lỗi validate backend hiển thị đúng ô.
- [ ] **8.3 Màn Mẫu ca và Nhân viên: `features/shift-templates`, `features/employees`**
  - Mẫu ca (giờ bắt đầu, độ dài, nghỉ, hệ số đêm), hồ sơ nhân viên (hợp đồng, giờ tối đa, ngày không thể làm, mong muốn); cảnh báo ngay khi mẫu ca vi phạm luật (vd. > 8 giờ).
  - Xong khi: CRUD đầy đủ; dữ liệu vào dùng được cho nút Optimize.
- [ ] **8.4 Màn Lịch: `features/schedule`**
  - Nút **Optimize** + `SolveStatusPanel` (trạng thái, gap, bound, thời gian giải, seed; chỉ ghi "tối ưu" khi `OPTIMAL`, `FEASIBLE` kèm gap — nguyên tắc 5); poll theo `job_id`.
  - `ScheduleGrid` (hàng = nhân viên, cột = ngày, màu theo loại ca), `CoverageChart` (cột số người chồng đường nhu cầu; thiếu = sọc chéo, thừa = phần trên vạch nhu cầu, theo CLAUDE.md 8.3), `CostSummary` (lương, phụ cấp đêm, %), xuất CSV.
  - Xong khi: chạy được trên instance 20–40 nhân viên; giờ thiếu nhìn thấy rõ trên chart.
- [ ] **8.5 Màn Tuân thủ: `features/compliance`**
  - `ViolationList` hiển thị vi phạm Đ.105/110/111 kèm nhân viên/ngày/giờ; chỉnh tay lịch bằng form → gọi lại validator và cập nhật cảnh báo; lịch gốc không bị ghi đè.
  - Xong khi: sửa tay gây nghỉ 8 giờ → cảnh báo Đ.110 hiện ngay.
- [ ] **8.6 Màn What-if: `features/what-if`**
  - `LambdaSlider` + đường cong `z(lambda)` (λ ∈ [0.8, 1.3]), `SensitivityHeatmap` chi phí biên 24 giờ (đánh dấu điểm `FEASIBLE`), `ScenarioCompare` hai kịch bản cạnh nhau, hiển thị nhãn "xấp xỉ" nếu có dual LP; tham số `alpha`, `p`, `r_min` cũng quét được.
  - Xong khi: kéo λ thấy đường cong cập nhật; heatmap không diễn giải sai điểm không tối ưu.
- [ ] **8.7 Hoàn thiện trải nghiệm**
  - Responsive cơ bản, a11y (tương phản, nhãn, bàn phím), trạng thái rỗng/lỗi/chờ ở mọi màn, văn bản UI tiếng Anh (quy ước code), không còn class `.todo`.
  - Xong khi: `npm run ci` sạch; duyệt tay toàn bộ luồng trên trình duyệt thật.
  - Trạng thái giai đoạn 8 (chưa tick vì chưa chạy với backend + MySQL thật và chưa duyệt trên trình duyệt; máy không có Chrome/Edge):
    - Đã làm: token, font và class dùng chung chuyển từ trang chủ sang `styles/`; component dùng chung `components/ui/*`, `components/solve/SolveRequestForm`; `apiFetch` đọc lỗi 422 thành lỗi theo ô; năm màn hình Demand, Employees, Shift templates, Schedule (kèm Compliance, sửa tay, xuất CSV), What-if (sweep, heatmap chi phí biên / dual LP, so sánh run). Nguồn UI ghi trong `docs/ui-references.md`.
    - Backend thêm cho UI: `ShiftTemplateRead.night_hours`, `break_required` (tính bằng engine), `SolveRunRead.employee_codes`, `shift_types` (từ snapshot), `GET /api/labor-rules`.
    - Kiểm: `npm run ci` (Biome, tsc, build) sạch; `check_conventions` sạch; render SSR mọi component với dữ liệu mẫu không lỗi; trang chủ vẫn đủ 102/102 đoạn chữ sau khi tách style; backend unit 48 pass.
    - Lệch: hợp đồng và giờ tối đa riêng từng nhân viên chưa có (engine chưa hỗ trợ); quét `alpha`, `p`, `r_min` chưa có API nên chưa lên UI; profile suy từ FreshRetailNet/tổng đài chỉ xem, muốn sửa thì chép sang profile tay (PUT sẽ ghi đè tham số tổng đài).

---

## Giai đoạn 9 — Kiểm chứng và nghiệm thu

Mục tiêu: chứng minh độ đúng bằng bằng chứng, chỉ kết luận trong phạm vi instance đã đo (nguyên tắc 5).

- [ ] **9.1 Benchmark Curtois & Qu (2014) — `engine/benchmarks/run_curtois_qu.py`**
  - Kiểm tra giấy phép (commit dữ liệu hay viết script tải); parser instance → `Instance`; chạy CP-SAT trên Instance1–5; báo cáo khoảng cách tới cận dưới đã công bố, kèm time limit, seed, số worker.
  - Xong khi: bảng kết quả có thể tái chạy bằng một lệnh; kết luận chỉ áp cho 5 instance đã đo.
- [ ] **9.2 So sánh solver CP-SAT vs HiGHS**
  - Cùng instance, cùng time limit, cùng seed; bảng status/objective/bound/gap/thời gian; không trích số Mittelmann như số của nhóm.
  - Xong khi: bảng kết quả có trong báo cáo và tái lập được.
- [ ] **9.3 Kiểm tra tái lập**
  - Test tự động: cùng instance + tham số + `num_workers = 1` + seed → cùng objective, nhiều lần chạy.
  - Xong khi: test pass ổn định; `solve_runs` đủ trường để chạy lại bất kỳ run nào.
- [ ] **9.4 Đo hiệu năng theo tiêu chí nghiệm thu**
  - Tuần 7×24, 20–40 nhân viên: giải ≤ 60 giây, gap ≤ 1%, coverage ≥ 98% ở kịch bản cơ sở, 0 vi phạm cứng.
  - Xong khi: bảng đo ghi máy chạy, phiên bản solver; nếu không đạt, ghi nguyên nhân và hướng xử lý (phân rã hai pha, phá đối xứng) thay vì hạ ràng buộc.
- [ ] **9.5 Nghiệm thu bản đầu theo CLAUDE.md mục 13**
  - Chạy lần lượt từng dòng bảng nghiệm thu, lưu bằng chứng (lệnh, kết quả, ảnh UI). Bao gồm hai ca pháp lý: 14h–22h → 06h–14h bị cấm; 22h–06h rồi nghỉ đủ 24 giờ không vi phạm Đ.111.
  - Xong khi: tất cả 9 tiêu chí đạt hoặc có ghi chú sai lệch được nhóm chấp nhận bằng văn bản.

---

## Giai đoạn 10 — Hoàn thiện CI, Docker, bảo mật

- [ ] **10.1 Bật ngưỡng coverage và dọn CI**
  - Thêm `--cov-fail-under=80` cho engine vào CI và `Makefile` khi coverage thật ≥ 80%; không còn test skip `TODO`; mọi job CI xanh trên `main`.
  - Xong khi: CI chặn được PR làm tụt coverage dưới 80%.
- [ ] **10.2 Chạy toàn stack bằng Docker Compose**
  - `cp .env.example .env` → `docker compose up -d --build`: `db` → `migrate` → `backend` → `frontend`; UI ở `http://localhost:3000` chạy được luồng đầy đủ; image ghim tag + digest, không `latest`; user non-root.
  - Xong khi: máy sạch dựng được theo README; healthcheck và thứ tự khởi động đúng.
- [ ] **10.3 Bảo mật và phụ thuộc**
  - `pip-audit`, `npm audit --omit=dev`, gitleaks sạch; giới hạn kích thước request, CORS, rate limit cơ bản cho endpoint tạo job; rà soát không rò stack trace; ghim phiên bản mới nhất ≥ 2 tuần tuổi.
  - Xong khi: job `security` xanh; checklist rà soát được ghi lại.
- [ ] **10.4 Cập nhật `README.md` và hướng dẫn chạy**
  - Cài đặt, chạy, test, dữ liệu, lệnh `make`; ghi rõ giới hạn đã biết.
  - Xong khi: người mới làm theo README chạy được mà không cần hỏi.

---

## Giai đoạn 11 — Đặc tả cuối, báo cáo, demo

- [ ] **11.1 Đồng bộ tài liệu kỹ thuật**
  - `docs/model.md` khớp mô hình đã cài (công thức, biến, ràng buộc, lexicographic); ADR-001/002 cập nhật; `docs/đặc tả.md` bản cuối; `CLAUDE.md` đồng bộ trạng thái repo (bỏ chú thích "skeleton").
  - Xong khi: không có mâu thuẫn giữa đặc tả, `model.md`, code.
- [ ] **11.2 Báo cáo cuối**
  - Nội dung: bài toán, mô hình, ràng buộc pháp lý, kết quả benchmark, so sánh solver, độ nhạy, hạn chế. Tuân thủ CLAUDE.md mục 15: nêu mâu thuẫn SKU 863/865; split eval ghi đúng mức đã kiểm; số liệu bài báo FreshRetailNet ghi "bản v5"; "CP-SAT không trả dual" ghi là suy luận từ tài liệu; FreshRetailNet không gọi là dữ liệu nhân sự; mọi kết luận hiệu năng chỉ áp cho instance đã đo.
  - Xong khi: nhóm duyệt; mỗi số liệu truy ra được lệnh/bảng nguồn.
- [ ] **11.3 Demo**
  - Kịch bản demo ngắn chạy trên dữ liệu có sẵn: nhập nhu cầu → Optimize → coverage + cảnh báo → sửa tay gây vi phạm → kéo λ → heatmap chi phí biên. Có bản dự phòng (ảnh/video) nếu solver chậm.
  - Xong khi: chạy thử trọn kịch bản không lỗi ít nhất hai lần liên tiếp.

---

## Ngoài phạm vi bản đầu (không làm trừ khi nhóm yêu cầu)

Đa địa điểm / ma trận kỹ năng, stochastic hai giai đoạn, robust optimization, chân trời nhiều tuần, kéo-thả và Gantt theo giờ, huấn luyện mô hình dự báo, xuất PDF, xác thực / phân quyền, tích hợp chấm công, Redis/Celery/WebSocket, Timefold, Gurobi bắt buộc.

## Rủi ro cần theo dõi

| Rủi ro | Dấu hiệu | Hướng xử lý |
|---|---|---|
| Roster CP-SAT quá chậm ở 40 nhân viên | gap > 1% sau 60 giây | phá đối xứng (4.3), phân rã hai pha (4.4), tinh chỉnh `num_workers`; không hạ ràng buộc pháp lý |
| PuLP 4 đổi API | `DeprecationWarning` thành lỗi | sửa `set_covering_pulp.py`, `pulp_backend.py`, chạy lại toàn bộ test engine |
| Dataset không tải được / quá nặng | 6.1 kẹt | làm việc trên mẫu một store, giữ script tải tái lập |
| Giả định `alpha`/`p` bị hỏi nguồn | người xem nghi ngờ | luôn hiện trên UI + đưa vào độ nhạy (8.2, 8.6) |
| Biome/TypeScript lệch phiên bản | `npm run ci` đỏ | giữ ghim hiện tại (Biome 2.5.x, TypeScript 5.9.3); nâng có kiểm tra binary Windows |
| `test_roster_resolver_reports_cost_from_kpi` (5.1) lỗi trong một lần chạy đầy đủ | so sánh hai lần giải CP-SAT; giới hạn thời gian có thể cho hai nghiệm khác nhau | đã sửa: test dùng lại một nghiệm đã giải (monkeypatch `solve_roster`) |
