# CLAUDE.md

Hướng dẫn cho Claude Code khi làm việc trong repo **ShiftOpt** — xếp ca nhân viên cho dịch vụ có nhu cầu biến động (quy hoạch nguyên tuyến tính, OR-Tools / PuLP, FastAPI, React).

Nguồn sự thật về yêu cầu, theo thứ tự ưu tiên:

1. Đề bài của nhóm (mục 1).
2. [docs/đặc tả.md](docs/đặc tả.md) — **chưa có**, sẽ viết dựa trên báo cáo nghiên cứu nền. Khi có, đặc tả thắng file này; hãy cập nhật file này theo đặc tả.
3. [Báo cáo nghiên cứu nền Xếp ca nhâ.md](<Báo cáo nghiên cứu nền Xếp ca nhâ.md>) — nghiên cứu tham chiếu (dữ liệu, mô hình, pháp lý, solver). Đây là khuyến nghị, không phải yêu cầu; chỗ nào báo cáo ghi "nên" thì file này đã chốt thành quy tắc hoặc loại bỏ ở các mục dưới. Nên chuyển báo cáo vào `docs/` khi dựng khung.

> **Trạng thái repo (2026-10-21):** đã có **khung code (skeleton)**. Mọi hàm nghiệp vụ là stub: docstring `TODO: ...` mô tả việc cần làm + `raise NotImplementedError` (frontend: `throw new Error("TODO: ...")` hoặc `<p className="todo">`). Phần khai báo (dataclass engine, `LaborRules`, settings, ORM model, Pydantic schema), phần nối dây (`create_app`, router, React router/layout, Alembic env, Compose, CI) và công cụ nội bộ (`scripts/`) là code thật. Đã có migration Alembic baseline. Engine coverage hiện ~32% nên CI **chưa** đặt ngưỡng 80% — bật `--cov-fail-under=80` khi đã triển khai engine. Cấu trúc ở mục 11, quy ước và lệnh ở mục 12.

---

## 1. Dự án làm gì

Đề bài của nhóm: **Xếp ca nhân viên cho dịch vụ có nhu cầu biến động.** Mô hình hóa bài toán xếp ca cho tổng đài chăm sóc khách hàng hoặc cửa hàng 24/7 dưới dạng quy hoạch nguyên tuyến tính: nhu cầu theo giờ, ca dài 8 giờ, ràng buộc nghỉ giữa ca và số ngày làm liên tiếp. Giải bằng OR-Tools hoặc PuLP, phân tích độ nhạy khi nhu cầu thay đổi, và xây dựng giao diện đơn giản cho phép nhập nhu cầu và xem lịch kết quả.

Web app nhận **nhu cầu theo giờ + danh sách nhân viên + mẫu ca + tham số luật**, trả ra:

1. Một **lịch xếp ca** (lưới nhân viên × ngày, kèm biểu đồ phủ nhu cầu) với trạng thái solver, gap, thời gian giải.
2. Bộ **KPI** (coverage, giờ thiếu/thừa, chi phí lao động, công bằng) và danh sách **vi phạm ràng buộc** (phải bằng 0 với ràng buộc cứng).
3. **Phân tích độ nhạy**: đường cong chi phí theo hệ số nhu cầu λ, chi phí biên rời rạc theo giờ, so sánh kịch bản.

Điểm phân biệt — mọi thiết kế phải giữ được:

- **Lịch do solver sinh ra phải được kiểm tra lại bởi validator độc lập**, không tin trạng thái của solver.
- **Độ nhạy của bài toán nguyên được tính bằng giải lại, không bằng shadow price giả.**
- **Mọi giả định chuyển đổi dữ liệu (doanh số → số người) là tham số hiển thị trên UI**, không giấu trong code.

Hai chế độ nhu cầu dùng chung một engine:

| Chế độ | Nguồn nhu cầu | Quy đổi ra số người |
|---|---|---|
| Bán lẻ / kho vận hành mở rộng | FreshRetailNet-50K (doanh số theo giờ) | Tuyến tính: `r = max(r_min, ceil(alpha * D / p))` |
| Tổng đài | Lưu lượng cuộc gọi (dữ liệu công khai hoặc giả lập) | Erlang C / Erlang A, mục tiêu service level |

---

## 2. Nguyên tắc bất biến (KHÔNG được vi phạm)

Khi một thay đổi đụng tới một trong các điều này, dừng lại và hỏi.

1. **Solver đề xuất, validator phán xét.** Mọi nghiệm (kể cả `OPTIMAL`) phải qua `validation.py` kiểm tra lại toàn bộ ràng buộc cứng trên dữ liệu đầu ra, bằng code độc lập với mô hình solver. Validator không import module `models/` hay `solvers/`.
2. **Ràng buộc pháp lý là ràng buộc cứng.** Nghỉ ≥12 giờ giữa hai ca, ≥24 giờ liên tục mỗi tuần, ≤48 giờ/tuần, số ngày làm liên tiếp tối đa. Không bao giờ hạ thành soft để "dễ giải".
3. **Coverage là soft với phạt rất lớn** (biến thiếu người `u_h`), để mô hình luôn khả thi và UI hiển thị được giờ nào thiếu. Không trả về `INFEASIBLE` trần trụi cho người dùng khi nguyên nhân là thiếu nhân lực.
4. **ILP / CP-SAT không có shadow price hợp lệ.** Không bao giờ trình bày dual của mô hình nguyên như chi phí biên. Dual chỉ lấy từ **LP relaxation** và phải gắn nhãn "xấp xỉ". Chi phí biên thật là chênh lệch giữa hai lần giải lại.
5. **Không tuyên bố tối ưu khi chưa chứng minh.** Chỉ gọi là "tối ưu" khi status `OPTIMAL`. `FEASIBLE` phải đi kèm gap và `best_objective_bound`. Kết luận về chất lượng chỉ giới hạn ở instance và time limit đã chạy.
6. **FreshRetailNet-50K không phải dữ liệu lao động.** Là doanh số sản phẩm theo giờ đã chuẩn hóa của kho tiền phương thương mại điện tử. Không ghi vào UI hay báo cáo rằng đây là nhu cầu nhân sự hay cửa hàng vật lý 24/7. Hệ số `alpha` (giải chuẩn hóa) và `p` (năng suất) là **giả định của nhóm**, phải hiện trên UI và đưa vào phân tích độ nhạy.
7. **Ca đêm không suy từ FreshRetailNet.** Doanh số giờ 0–5 gần như bằng 0 vì hàng không được bổ sung ngoài khung 6–22h. Dùng **mức tối thiểu cố định** `r_min` cho giờ đêm (tham số, ví dụ 1–2 người).
8. **Giờ hết hàng là dữ liệu bị kiểm duyệt (censored).** Giờ có `hours_stock_status = 1` không được dùng nguyên doanh số làm nhu cầu; phải thay bằng nhu cầu ẩn ước lượng (mặc định: trung bình cùng giờ, cùng thứ trong tuần, loại giờ hết hàng) và ghi rõ phương pháp.
9. **`engine/` là package thuần Python.** Không import FastAPI, SQLAlchemy, Pydantic settings hay bất kỳ thứ gì của `backend/`. Mọi logic tối ưu, ràng buộc, KPI, độ nhạy nằm trong `engine/`; `backend/` chỉ nối dây, lưu trữ, phục vụ HTTP.
10. **Tái lập được.** Mỗi lượt giải lưu: instance đầu vào, tham số, tên và phiên bản solver, `random_seed`, `num_workers`, time limit, status, objective, bound, gap, wall time. Cùng instance + cùng tham số + `num_workers = 1` + cùng seed phải ra cùng kết quả.
11. **Không chạy solver trên event loop của FastAPI.** Giải chạy trong tiến trình con có time limit; API trả `job_id` để poll.
12. **Phá đối xứng chỉ áp cho nhóm nhân viên thật sự đồng nhất** (cùng hợp đồng, kỹ năng, không yêu cầu cá nhân). Nếu có yêu cầu riêng, không áp — có thể cắt mất nghiệm tối ưu.
13. **Không dùng tag `latest`** cho bất kỳ image/dependency nào. Mọi phiên bản phải được ghim. Giải bằng HiGHS qua `pulp.HiGHS` (`pulp[highs]`); không dựa vào CBC đóng gói sẵn (`PULP_CBC_CMD`) vì báo cáo nghiên cứu ghi PuLP 4 bỏ nó.
14. **Khi thiếu thông tin, hỏi lại thay vì đoán** (ví dụ ca đêm tính từ 22h hay theo hợp đồng riêng, `alpha` và `p` lấy giá trị nào, một "ngày" bắt đầu lúc mấy giờ).

---

## 3. Kiến trúc tổng thể

### 3.1 Luồng xử lý

```
Nhu cầu (nhập tay / CSV / FreshRetailNet / lưu lượng cuộc gọi)
  → staffing/        (xác định)  D[d,h] → r[d,h]  (tuyến tính hoặc Erlang)
  → Instance         (xác định)  nhu cầu + nhân viên + mẫu ca + LaborRules
  → models/          (solver)    set covering hoặc roster CP-SAT
  → Solution
  → validation.py    (xác định)  kiểm tra lại mọi ràng buộc cứng
  → kpi.py           (xác định)  coverage, thiếu/thừa, chi phí, công bằng
  → sensitivity/     (solver)    quét λ, chi phí biên, kịch bản
  → UI               (lịch, coverage chart, cảnh báo, what-if)
```

### 3.2 Hai tầng mô hình

| Tầng | Mô hình | Solver | Dùng để |
|---|---|---|---|
| Tổng hợp (lõi giáo khoa) | Phủ tập Dantzig (1954): `min sum c_j x_j`, `sum a_tj x_j >= r_t`, `x_j` nguyên không âm; chu kỳ 24 giờ hoặc 168 giờ có quấn vòng | PuLP + HiGHS | Số người theo kiểu ca, lấy dual của LP relaxation, benchmark, ví dụ có đáp án tay |
| Theo nhân viên (lõi sản phẩm) | `x[e,d,s]` Boolean, gán nhân viên `e` ca `s` ngày `d` | OR-Tools CP-SAT | Lịch thật có nghỉ 12 giờ, số ngày liên tiếp, công bằng, yêu cầu cá nhân |

Nghỉ giữa ca (Điều 109) mô hình hóa như **giảm năng lực phủ ở một giờ trong cửa sổ nghỉ** (biến thể Bechtold–Jacobs đơn giản, `models/implicit_breaks.py`), không liệt kê từng tổ hợp (ca, vị trí nghỉ) như Dantzig gốc.

Phân rã hai pha là chiến lược giảm kích thước khi instance lớn: pha 1 giải mô hình tổng hợp để có số người mỗi kiểu ca, pha 2 gán cá nhân.

### 3.3 Quyết định kiến trúc đã chốt

- **CP-SAT cho mô hình theo nhân viên; PuLP + HiGHS cho mô hình Dantzig và dual LP.** `solvers/cpsat.py` và `solvers/pulp_backend.py` dùng chung `SolveParams` / `SolveResult` để benchmark hai bên trên cùng instance. Gurobi chỉ là tùy chọn qua license học thuật, không phải phụ thuộc.
- **Timefold Solver Python bị loại** (repo đã archive, chậm hơn Java). Chỉ tham khảo UI và mô hình miền từ bản Java.
- **MySQL 8** (InnoDB, `utf8mb4`) cho dữ liệu ứng dụng (nhân viên, mẫu ca, nhu cầu, lượt giải, kết quả). SQLAlchemy 2 + Alembic, driver `PyMySQL` hoặc `asyncmy` (ghim version). Lịch, log solver, tham số lưu ở cột `JSON`. Không dùng SQLite thay MySQL trong test. Ghi chú Alembic: DDL của MySQL không transactional, migration lỗi giữa chừng không tự rollback; review tay kỹ.
- **Job giải = hàng trong bảng `solve_runs`; job độ nhạy = hàng trong `analysis_runs`.** API tạo job, chạy giải trong tiến trình con (`ProcessPoolExecutor`), frontend poll theo `job_id`. Khi backend khởi động lại, job đang `running` được đánh dấu `failed` với lý do rõ ràng. **Không thêm Redis/Celery, không WebSocket** ở bản đầu.
- **Hai phiên bản lịch không bao giờ trộn:** mỗi lượt giải là bất biến. Sửa tay lịch tạo bản mới và chạy lại validator.

---

## 4. Dữ liệu nhu cầu

### 4.1 FreshRetailNet-50K

Hugging Face `Dingdong-Inc/FreshRetailNet-50K`, CC BY 4.0, arXiv:2505.16319. 50.000 chuỗi store–product × 90 ngày, 898 "store" (thực chất kho tiền phương, bán kính 3 km, giao 30 phút) ở 18 thành phố, tháng 3–6/2024. Số SKU ghi 865 (dataset card) hoặc 863 (arXiv): **ghi "~863–865 SKU" khi trích dẫn.**

Cột dùng: `store_id`, `city_id`, `dt`, `hours_sale` (list 24 giá trị, đã chuẩn hóa toàn cục), `hours_stock_status` (cờ hết hàng từng giờ), `holiday_flag`, `activity_flag`, `discount`, `precpt` (mưa). Các cột danh mục sản phẩm có thể bỏ. Split eval 7 ngày chỉ là **suy luận** (350.000 / 50.000); xác nhận bằng `dt.min()/max()` trước khi dựa vào.

Dữ liệu thô tải vào `data/raw/` (gitignore). Kết quả xử lý vào `data/processed/demand_store_<id>.parquet`.

### 4.2 Quy trình chuyển đổi doanh số → số nhân viên cần

1. Chọn một `store_id` (hoặc `city_id`), cộng `hours_sale` của mọi sản phẩm theo (`dt`, giờ) → chỉ số tải `D[d,h]`.
2. Giờ có `hours_stock_status = 1`: thay bằng nhu cầu ẩn ước lượng (nguyên tắc 8).
3. `r[d,h] = max(r_min, ceil(alpha * D[d,h] / p))`. `alpha`, `p`, `r_min` là tham số nhập từ UI hoặc API, có giá trị mặc định ghi trong `staffing/linear.py`.

Chế độ tổng đài: `lambda_h → Erlang A/C → r_h`. Erlang A (có khách bỏ cuộc) ưu tiên hơn Erlang C vì Erlang C dẫn tới thừa người. Mục tiêu mặc định "80/20" (80% cuộc gọi trả lời trong 20 giây) là tham số. Square-root staffing `N = R + beta * sqrt(R)` là phương án nhanh. Dataset tổng đài công khai (ngân hàng Đông Bắc Mỹ, SEELab Technion) hoặc giả lập có seed cố định.

### 4.3 Nhập nhu cầu từ người dùng

Lưới 7×24 chỉnh sửa trực tiếp, import CSV, hoặc "tạo từ FreshRetailNet store X". Validate ở biên: số nguyên không âm, đủ 168 ô, giới hạn trên hợp lý.

---

## 5. Mô hình toán học và ràng buộc

### 5.1 Quy ước thời gian (`time_grid.py`)

- Chân trời tuần: chỉ số giờ `0..167`, ngày `d = 0` là thứ Hai. Giờ trong ngày `0..23`.
- Ca = (giờ bắt đầu `sigma`, độ dài `L`, mặc định `L = 8`). Ca qua nửa đêm **tính giờ làm vào ngày hôm sau** cho phần vượt 24h.
- Chu kỳ quấn vòng: `a_tj = 1` khi `(t - s_j) mod period` thuộc `{0..L-1}`, với `period = 24` hoặc `168`.
- Giờ đêm: 22h–06h hôm sau (Điều 106). Hàm `night_hours(shift)` là nguồn duy nhất, mọi nơi khác gọi hàm này.
- Không dùng `datetime` naive cho tính toán giờ ca; làm việc với chỉ số giờ nguyên.

### 5.2 Mô hình theo nhân viên (`roster_cpsat.py`)

Tập: `E` nhân viên, `D` ngày, `S` kiểu ca, `H` giờ. Biến: `x[e,d,s]` Boolean; `w[e,d] = sum_s x[e,d,s]`; `u_h >= 0` thiếu người, với `staff_h + u_h >= r_h`. Thừa người không cần biến riêng: chi phí lương đã phạt nó, và `kpi.py` tính số giờ thừa.

Mục tiêu: `min sum c_s x + M_u * sum u_h + lambda_F * F`.

Thứ tự ưu tiên: thiếu người `M_u` ≫ chi phí lao động ≫ công bằng ≫ sở thích. Ưu tiên **giải lexicographic** (tối thiểu thiếu người trước, cố định, rồi tối thiểu chi phí) thay vì chọn `M` tùy tiện. Mọi trọng số là hằng có tên trong config, không magic number.

### 5.3 Bảng ràng buộc

| Ràng buộc | Nguồn | Loại | Ghi chú triển khai |
|---|---|---|---|
| Tối đa 1 ca/ngày/nhân viên | Mô hình | Hard | `AddAtMostOne` |
| Phủ nhu cầu từng giờ | Đề bài | Soft (phạt `M_u`) | Ca qua đêm tính vào giờ ngày sau |
| Giờ làm ≤ 8/ngày, ≤ 48/tuần | BLLĐ 2019 Đ.105 | Hard | Tham số 40 giờ cho kịch bản |
| Nghỉ ≥ 12 giờ giữa hai ca liên tiếp | Đ.110 | Hard | Cấm cặp `(s, s')` có `24 + sigma' - (sigma + L) < 12` |
| Nghỉ ≥ 24 giờ liên tục mỗi tuần | Đ.111 | Hard | Ràng buộc ngày nghỉ **cộng kiểm tra 24 giờ liên tục trên trục giờ** |
| Tối đa `K` ngày làm liên tiếp | Đề bài, INRC-II | Hard | Cửa sổ `sum w <= K` trên `K+1` ngày; `K = 6` đảm bảo có ngày nghỉ mỗi cửa sổ 7 ngày |
| Nghỉ giữa giờ ≥ 30 phút (≥ 45 phút nếu ca đêm) | Đ.109, NĐ 145/2020 | Hard | Giảm năng lực phủ một giờ trong cửa sổ nghỉ |
| Phụ cấp đêm ≥ 30% | Đ.98 khoản 2 | Chi phí | `c_s = L*wage + 0.3*wage*|night_hours(s)|` |
| Công bằng ca đêm / cuối tuần | Van den Bergh 2013 | Soft | `F = max_e N_e - min_e N_e`, `AddMaxEquality` / `AddMinEquality` |
| Số ngày làm liên tiếp tối thiểu, số cuối tuần tối đa | INRC-II | Soft | Trọng số cấu hình |
| Yêu cầu ca / ngày nghỉ của nhân viên | OR-Tools "shift requests" | Soft | Chỉ áp cho nhân viên có yêu cầu |

Điều kiện nghỉ 12 giờ **luôn viết bằng công thức tổng quát** `24 + sigma' - (sigma + L) < 12`. Dạng rút gọn `sigma - sigma' > 4` chỉ đúng với `L = 8`; không hard-code. Ví dụ phải bị cấm: ca 14h–22h hôm trước rồi 06h–14h hôm sau (nghỉ 8 giờ). Đây là test bắt buộc.

**Bẫy Điều 111 với ca qua đêm:** ngày lịch nghỉ không tự động cho 24 giờ liên tục. Ca 22h ngày `d-1` kết thúc 06h ngày `d`; nếu `d` nghỉ và ca kế bắt đầu 00h ngày `d+1` thì chỉ nghỉ 18 giờ. Validator tính khoảng nghỉ liên tục trên trục giờ, không chỉ đếm ngày nghỉ.

### 5.4 Hằng số pháp lý

Mọi con số luật (8, 48, 12, 24, 30%, 30/45 phút, khung đêm 22–6) nằm trong một dataclass bất biến `LaborRules` (`constraints/labor_law_vn.py`) với giá trị mặc định đúng luật và docstring ghi điều khoản. Mô hình và validator đều đọc từ `LaborRules`; kịch bản what-if đổi tham số bằng cách truyền `LaborRules` khác, không sửa code.

Lưu ý khi trích dẫn: khung giờ đêm thuộc **Điều 106**, không phải Điều 105 (một số bài phổ biến ghi nhầm). Giới hạn làm thêm giờ (Đ.107: 50% giờ bình thường/ngày, 40 giờ/tháng, 200 giờ/năm, tới 300 giờ/năm với một số ngành) và hệ số làm thêm (Đ.98: 150% / 200% / 300%, đêm +20%) chỉ dùng trong mô hình ngẫu nhiên hai giai đoạn (mục 6, mức mở rộng). Bản đặc tả cuối nên trích trực tiếp văn bản 45/2019/QH14, không trích qua trang thứ cấp.

### 5.5 Phá đối xứng

Chỉ áp cho nhóm đồng nhất: thứ tự từ điển `sum_d w[e,d] >= sum_d w[e+1,d]`; gán cố định nhân viên đầu nhóm ca sớm nhất ngày đầu; hoặc phân rã hai pha (mục 3.2). Phải có test chứng minh giá trị mục tiêu không đổi khi bật/tắt phá đối xứng trên instance nhỏ.

---

## 6. Phân tích độ nhạy

Bắt buộc (1–3), kịch bản (4) nên có, (5–6) là mở rộng:

1. **Dual của LP relaxation** (`sensitivity/lp_duals.py`): mô hình Dantzig, PuLP + HiGHS, lấy `constraint.pi` và `.slack`. Luôn gắn nhãn "xấp xỉ, integrality gap có thể lớn". `.pi` có thể là `None` tùy giao diện solver — phải xử lý và có test.
2. **Cố định biến nguyên rồi giải lại LP** để lấy dual cục bộ.
3. **Quét tham số** (`sensitivity/parametric.py`): với `lambda` trong `{0.8, 0.9, ..., 1.3}` giải lại với `r_t(lambda) = ceil(lambda * r_t)`, vẽ `z(lambda)`, số người, giờ thiếu. **Chi phí biên rời rạc** của giờ `t` là `z(r + e_t) - z(r)`, tính bằng 24 lần giải lại; đây là heatmap có giá trị nhất cho UI. Mỗi lần giải dùng cùng time limit và seed; kết quả `FEASIBLE` không phải `OPTIMAL` phải được đánh dấu để chênh lệch không bị diễn giải sai.
4. **Kịch bản theo covariate** (`sensitivity/scenarios.py`): `holiday_flag`, `discount < 1` / `activity_flag`, mưa. Khuyến mãi tạo nhu cầu cao hơn doanh số quan sát (median uplift 1.43× theo bài báo), mưa và giảm giá sâu làm tăng hết hàng — nghĩa là nhu cầu thật còn cao hơn nữa.
5. *(Mở rộng)* Stochastic hai giai đoạn: giai đoạn 1 chọn lịch, giai đoạn 2 gọi thêm / làm thêm giờ trên 10–30 kịch bản (SAA).
6. *(Mở rộng)* Robust optimization với tập bất định có ngân sách.

Độ nhạy theo tham số giả định `alpha`, `p`, `r_min` là một phần của phân tích, không chỉ là hạn chế.

---

## 7. Solver

| Tiêu chí | OR-Tools CP-SAT | PuLP + HiGHS | Gurobi (tùy chọn) |
|---|---|---|---|
| Mạnh nhất ở | Boolean, ràng buộc chuỗi, rostering | LP / MIP, dual LP | MIP lớn |
| Dual / shadow price | Không trả cho người dùng | Có cho LP | Có cho LP; không cho MIP |
| Song song | `num_workers` | Hạn chế | Có |

- Trạng thái CP-SAT: `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, `UNKNOWN`, `MODEL_INVALID`. `MODEL_INVALID` là lỗi lập trình, không phải lỗi người dùng.
- Gap = `|objective_value - best_objective_bound| / max(1, |objective_value|)`.
- Tham số: `max_time_in_seconds`, `relative_gap_limit`, `num_workers`, `random_seed`, `log_search_progress`.
- `SolveParams` và `SolveResult(status, objective, bound, gap, wall_time_seconds, solver)` (`solvers/base.py`) là kiểu chung của `solvers/cpsat.py` và `solvers/pulp_backend.py`. Protocol `SolverBackend` chỉ thêm khi benchmark hai solver trên cùng instance. Lưu cả log vào `solve_runs` để hiển thị trên UI.
- Tham khảo mô hình: `examples/python/shift_scheduling_sat.py` của google/or-tools (ràng buộc chuỗi ca, tổng theo tuần, phạt chuyển ca, yêu cầu nhân viên). API hữu ích: `AddExactlyOne`, `AddAtMostOne`, `AddBoolOr`, `AddImplication`, `OnlyEnforceIf`, `AddAutomaton`, `AddMaxEquality`.
- Kết luận "CP-SAT không trả dual" là **suy luận từ tài liệu**, không phải phát biểu chính thức. Khi viết báo cáo, nói đúng như vậy.

---

## 8. Giao diện và API

### 8.1 Tính năng MVP

1. Nhập / chỉnh nhu cầu theo giờ (lưới 7×24, CSV, tạo từ FreshRetailNet).
2. Mẫu ca: giờ bắt đầu, độ dài, nghỉ, hệ số đêm.
3. Hồ sơ nhân viên: hợp đồng, giờ tối đa, ngày không thể làm, mong muốn.
4. Nút **Optimize** hiển thị trạng thái, gap, thời gian giải.
5. **Coverage chart**: cột số người theo giờ chồng đường nhu cầu; đỏ giờ thiếu, xanh giờ thừa.
6. **Lịch dạng lưới** (hàng = nhân viên, cột = ngày, ô màu theo loại ca); chế độ Gantt theo giờ là mức mở rộng.
7. **Cảnh báo tuân thủ**: vi phạm Đ.105 / 110 / 111, phát hiện cả khi người dùng sửa tay.
8. Bảng chi phí: tổng lương, phụ cấp đêm, % chi phí lao động.
9. **What-if**: thanh trượt λ, so sánh hai kịch bản cạnh nhau, heatmap chi phí biên theo giờ.
10. Xuất CSV (PDF là mức mở rộng).

Kéo-thả chỉnh tay là mức mở rộng, và nếu làm thì phải kiểm tra lại ràng buộc sau mỗi thao tác.

### 8.2 Quy tắc API

- Mỗi domain (`demand`, `employees`, `shifts`, `schedules`, `analysis`) có `router.py`, `schemas.py`, `models.py`, `service.py`; `dependencies.py`, `exceptions.py` khi cần. Router mỏng, logic trong `service.py`, tối ưu gọi sang `shiftopt`.
- Giải dài: `POST` trả `job_id` ngay, `GET` poll trạng thái. Không giữ kết nối mở chờ solver.
- Kiểu TypeScript ở frontend **sinh từ OpenAPI** của FastAPI, không viết tay.
- Mọi input qua Pydantic v2 và validate tại biên (kích thước, miền giá trị, số nhân viên và số ngày tối đa để chặn instance quá lớn).
- Lỗi nghiệp vụ trả mã và thông điệp có nghĩa (vd. "demand grid must have 168 cells"), không để lộ stack trace.

---

## 9. Đánh giá và KPI

### 9.1 KPI (định nghĩa chính xác, cài trong `kpi.py`)

| KPI | Công thức |
|---|---|
| Coverage ratio | `sum_h min(staff_h, r_h) / sum_h r_h` |
| Understaffed / Overstaffed hours | `sum_h max(0, r_h - staff_h)` / `sum_h max(0, staff_h - r_h)` |
| Schedule efficiency | `sum_h r_h / sum_h staff_h` |
| Labor cost, labor cost % | Tổng lương + phụ cấp đêm; % so với doanh thu giả định (tham số) |
| Công bằng | Độ lệch chuẩn số ca đêm / cuối tuần giữa nhân viên |
| Kỹ thuật | Thời gian giải, gap, số vi phạm cứng (phải = 0) |
| Dự báo (nếu có) | WAPE / MAPE trên tập eval của FreshRetailNet |

Schedule adherence (so lịch với chấm công) **ngoài phạm vi** vì không có dữ liệu chấm công; chỉ nhắc ở hướng phát triển.

### 9.2 Kiểm chứng mô hình

- **Ví dụ có đáp án tay** cho mô hình Dantzig (`test_set_covering.py`).
- **Benchmark Curtois & Qu (2014)**: chạy CP-SAT trên Instance1–5 (`data/benchmarks/curtois_qu/`), báo cáo khoảng cách tới cận dưới đã công bố. Đây là bằng chứng độ đúng mạnh nhất; làm sau khi mô hình lõi chạy.
- **So sánh solver:** CP-SAT và HiGHS trên cùng instance, cùng time limit.
- Trong báo cáo, mọi kết luận về hiệu năng solver chỉ áp dụng cho instance đã đo. Không trích số Mittelmann như số của chính nhóm.

---

## 10. Tech stack

| Layer | Công nghệ |
|---|---|
| Engine | Python 3.11 · OR-Tools (CP-SAT) · PuLP + HiGHS · NumPy / pandas (chỉ xử lý dữ liệu) |
| Backend | FastAPI · Python 3.11 · Pydantic v2 (async REST) |
| Database | MySQL 8 · SQLAlchemy 2 · Alembic |
| Dữ liệu | `datasets` (Hugging Face) · Parquet |
| Frontend | React 19 · react-router 8 · Vite 8 · TypeScript 5.9 · CSS thuần · TanStack Query 5 · Biome · openapi-typescript · thư viện biểu đồ chọn khi dựng UI (`docs/adr/adr-002-charting-library.md`) |
| Deploy | Docker Compose: `db` (MySQL 8.4), `migrate` (Alembic một lần), `backend` (uvicorn), `frontend` (build Vite, phục vụ bằng nginx, proxy `/api`) |
| Test | pytest · pytest-asyncio · httpx + asgi-lifespan · pytest-cov |

**Phiên bản đã ghim:** `ortools==9.15.6755`, `pulp[highs]==3.3.2` (kèm `highspy==1.13.0`). PuLP 3.3.2 là bản mới nhất khi dựng khung (2026-10-21); nó dùng được `pulp.HiGHS` và trả `constraint.pi`, nhưng phát `DeprecationWarning` báo trước API PuLP 4 (`prob.add_variable`, `prob.constraints()` trả list). Khi nâng lên PuLP 4: sửa `models/set_covering_pulp.py` và `solvers/pulp_backend.py` rồi chạy lại toàn bộ test engine. Không nâng `ortools` hoặc `pulp` đơn lẻ mà không chạy lại toàn bộ test engine và benchmark. Frontend dùng TypeScript 5.9.3 vì `openapi-typescript` 7 chỉ hỗ trợ TypeScript `^5`.

**Tuổi dependency:** chỉ ghim bản đã phát hành **ít nhất 2 tuần**. Bản quá mới có thể chưa đủ binary cho mọi nền tảng (Biome 2.6.0 lúc dựng khung thiếu binary Windows), đồng thời giảm rủi ro chuỗi cung ứng.

Không thêm SDK LLM, thư viện dự báo nặng hay dependency khác khi chưa được yêu cầu.

---

## 11. Cấu trúc thư mục

```
backend/
  pyproject.toml, uv.lock   dependency + cấu hình Ruff, mypy, pytest; uv; shiftopt là path dependency editable
  .python-version           3.11
  .env.example              biến SHIFTOPT_* cho chạy local
  Dockerfile                build từ root (cần ../engine); multi-stage, uv + python ghim tag + digest, user non-root
  openapi.json              sinh bởi scripts/export_openapi.py; CI kiểm tra khớp code
  alembic.ini, migrations/  Alembic async; versions/ có migration baseline
  scripts/export_openapi.py
  src/
    main.py                 create_app (uvicorn --factory), lifespan (engine + session factory), /health
    config.py               Settings (BaseSettings, tiền tố SHIFTOPT_), get_settings
    database.py             Base + naming convention, enum_column (VARCHAR), engine, get_session
    exceptions.py           AppError, NotFoundError, ConflictError, InstanceTooLargeError + handler
    demand/                 router, schemas, models (DemandProfile), service, dataset_loader
    employees/              router, schemas, models (EmployeeRecord), service
    shifts/                 router, schemas, models (ShiftTemplate), service
    schedules/              router, schemas, models (SolveRun, RunStatus), service, dependencies
    analysis/               router, schemas, models (AnalysisRun), service: sweep, chi phí biên, dual LP
  tests/
    conftest.py             fixture app (LifespanManager), client (ASGITransport), database_url
    unit/                   không cần DB
    integration/            marker `integration`, cần MySQL
engine/
  pyproject.toml, uv.lock
  src/shiftopt/
    domain.py               dataclass bất biến: ShiftType, Employee, Instance, Assignment, Solution
    time_grid.py            hằng số giờ/ngày/tuần, quấn vòng mod 168, giờ đêm
    staffing/               linear.py, erlang.py
    models/                 set_covering_pulp.py, implicit_breaks.py, roster_cpsat.py
    constraints/            labor_law_vn.py (LaborRules), sequences.py, fairness.py
    solvers/                base.py (SolveStatus, SolveParams, SolveResult), cpsat.py, pulp_backend.py
    sensitivity/            lp_duals.py, parametric.py, scenarios.py
    validation.py           kiểm tra hậu nghiệm mọi ràng buộc cứng, độc lập với solver
    kpi.py
  tests/
    conftest.py             fixture three_shifts, build_instance
    test_smoke.py           khai báo thật: LaborRules, validate của dataclass
    test_time_grid.py, test_labor_law_vn.py, test_validation.py, test_kpi_and_staffing.py,
    test_set_covering.py, test_roster_cpsat.py, test_sensitivity.py   kịch bản TODO
  benchmarks/run_curtois_qu.py
frontend/
  package.json, package-lock.json, vite.config.ts, tsconfig.json, biome.json, index.html
  Dockerfile, nginx.conf, .dockerignore
  src/
    main.tsx
    app/                    providers.tsx (TanStack Query), router.tsx, layout.tsx (nav), routes/*.tsx (stub)
    components/ui/          Button, Table, Modal, Slider (stub)
    config/env.ts
    lib/api-client.ts       apiFetch (stub), ApiError
    styles/global.css       token màu/khoảng cách, class .todo
    types/api.ts            sinh từ backend/openapi.json (npm run gen:api), không sửa tay
    types/models.ts         alias tên schema từ api.ts
    features/
      demand/               api/demand.ts, components/DemandGridEditor.tsx, ConversionParamsForm.tsx
      employees/            api/employees.ts, components/EmployeeTable.tsx
      shift-templates/      api/shift-templates.ts, components/ShiftTemplateList.tsx
      schedule/             api/schedules.ts, components/ScheduleGrid, CoverageChart, SolveStatusPanel, CostSummary
      compliance/           api/compliance.ts, components/ViolationList.tsx
      what-if/              api/analysis.ts, components/LambdaSlider, SensitivityHeatmap, ScenarioCompare
data/                       (chưa tạo) raw/ gitignore, processed/, benchmarks/curtois_qu/
docs/
  đặc tả.md                 (chưa có) nguồn sự thật yêu cầu
  model.md                  công thức mô hình
  adr/                      adr-001 chọn solver, adr-002 thư viện biểu đồ (chưa chốt)
scripts/check_conventions.py   cưỡng chế "không comment" + "code chỉ ASCII"; bỏ qua file sinh (GENERATED_PATHS)
docker-compose.yml, .env.example, .dockerignore, Makefile
.github/workflows/ci.yml
.pre-commit-config.yaml
```

Ranh giới module:

- `engine/` không import `backend/`. `backend/` import `shiftopt` qua public API, không đụng vào module nội bộ.
- `validation.py` và `kpi.py` chỉ phụ thuộc `domain.py`, `time_grid.py`, `constraints/labor_law_vn.py`. **Không** phụ thuộc `models/` hay `solvers/`.
- `staffing/` thuần hàm số, không I/O.
- `sensitivity/` gọi `models/` hoặc `solvers/`, không gọi trực tiếp thư viện solver.
- Frontend: luồng một chiều shared → features → app; **không import chéo giữa các feature**.
- `data/raw/` không commit. Benchmark Curtois & Qu chỉ commit nếu giấy phép cho phép, nếu không thì script tải.

---

## 12. Quy ước khi viết code

**Ngôn ngữ và comment (bắt buộc):**
- Toàn bộ code viết bằng **tiếng Anh**: tên, docstring, chuỗi lỗi, text UI, file template, metadata package. Tài liệu (`docs/`, `*.md`) có thể dùng tiếng Việt.
- **Code chỉ ASCII.** Ký hiệu toán học đặt tên bằng chữ Latin (`alpha`, `lam`, `sigma`), không dùng ký tự Hy Lạp hay dấu tiếng Việt trong code.
- **Không dùng comment**: `#` trong Python, YAML, TOML, Dockerfile, shell; `//` / `/* */` trong TS, CSS; `--` trong SQL. Code phải tự giải thích qua tên và cấu trúc; điều bắt buộc phải nói (nguồn công thức, điều luật, giả định) đặt trong **docstring** của hàm hoặc class. Ngoại lệ duy nhất: shebang.
- **Ngoại lệ lint chỉ khai báo trong file cấu hình** (`[tool.ruff.lint.per-file-ignores]`, `biome.json`), không bao giờ inline (`# noqa`, `# type: ignore`, `// biome-ignore` đều là comment).
- File sinh tự động: migration Alembic phải sạch comment (bỏ dòng `# ###`). `frontend/src/types/api.ts` và `backend/openapi.json` được loại khỏi kiểm tra bằng cấu hình (`GENERATED_PATHS` trong `check_conventions.py`, `files.includes` trong `biome.json`); không sửa tay, sinh lại bằng `make openapi`.
- `scripts/check_conventions.py` cưỡng chế hai quy tắc trên; CI và pre-commit đều chạy nó.
- Clean code: hàm nhỏ, một việc; tên rõ nghĩa; không code chết, import thừa hay magic number. Hằng số miền (số giờ, trọng số phạt, ngưỡng) có tên và nằm trong config hoặc `LaborRules`.

**Quy ước stub khi chưa triển khai:**
- Python: docstring bắt đầu bằng `TODO:` mô tả hành vi + ràng buộc liên quan (tham chiếu điều luật hoặc mục của file này), thân hàm là `raise NotImplementedError`.
- TypeScript: `throw new Error("TODO: ...")`; component React render `<p className="todo">TODO: ...</p>`.
- Test chưa viết: `@pytest.mark.skip(reason="TODO")` + docstring `TODO:` nêu kịch bản.
- Khi triển khai một hàm: bỏ `TODO:` khỏi docstring (giữ phần mô tả hợp đồng nếu còn giá trị), thay skip bằng test thật.
- Công cụ nội bộ (`scripts/`, `migrations/env.py`) và phần nối dây là code thật, không phải stub.

**Công cụ (phải sạch trước khi commit):**
- **Ruff 0.17.1**, `select` tường minh: E, F, I, B, UP, S, PT, RUF, SIM, C4, TC (engine); backend thêm ASYNC. Thêm NPY khi code dùng NumPy. `TC` coi Pydantic/SQLAlchemy base là runtime; `backend/src/**/router.py` và `dependencies.py` tắt TC vì FastAPI đọc annotation lúc chạy.
- **mypy 2.4 strict**: engine `src tests benchmarks`; backend `src tests migrations/env.py scripts` (thêm plugin Pydantic). Thư viện thiếu type (PuLP, asyncmy, asgi_lifespan) khai báo `ignore_missing_imports` trong cấu hình mypy, không bằng `# type: ignore`.
- **Biome 2.5** cho frontend (lint + format + organize imports); `tsc --noEmit` riêng vì Vite không type-check. Tham số chưa dùng được phép (`noUnusedParameters: false`, `noUnusedFunctionParameters: off`) vì stub chưa dùng tham số.
- **pytest**: `asyncio_mode = "auto"`, `--strict-markers`. Test cần MySQL đặt trong `tests/integration/` và tự skip khi thiếu `SHIFTOPT_TEST_DATABASE_URL`. **Coverage `engine/` ≥ 80%** khi đã triển khai (hiện chỉ báo cáo, chưa chặn).

**Kỹ thuật:**
- Python 3.11, type hints đầy đủ. Pydantic v2 cho mọi schema I/O ở `backend/`. Trong `engine/` dùng `dataclass(frozen=True)` cho `Instance`, `Solution`, `LaborRules`, `SolveResult` (không kéo Pydantic vào lõi).
- Hàm engine **thuần và tất định**: cùng đầu vào + cùng seed → cùng đầu ra. Không đọc biến môi trường, không đọc file, không ghi log ra ngoài từ trong mô hình.
- Mọi bất biến mô hình có test **bắt lỗi thật**: tiêm vi phạm (nghỉ 8 giờ, 7 ngày liên tiếp, 49 giờ/tuần, nghỉ tuần 18 giờ) và kiểm tra validator bắt được; không chỉ kiểm tra nghiệm đẹp pass.
- Mọi thay đổi schema DB qua **Alembic migration** (models là nguồn, có naming convention). Sửa model thì chạy autogenerate, **review tay**, bỏ comment, commit; CI chạy `alembic check`.
- Không commit secret; cấu hình qua biến môi trường tiền tố `SHIFTOPT_` (`backend/.env.example`; `.env.example` ở root cho Compose).
- Dependency mới: ghim phiên bản chính xác (`uv add "pkg==x.y.z"`, `npm install --save-exact`). Image Docker trong Dockerfile ghim **tag + digest**; image trong Compose ghim tag chính xác. GitHub Actions ghim theo **commit SHA**.
- Thời gian giải và kích thước instance có giới hạn cấu hình (`Settings.max_employees`, `Settings.max_solve_seconds`, `Settings.solve_workers`) để một request không chiếm hết CPU.
- Enum trong DB lưu `value` dạng VARCHAR qua `enum_column` (`native_enum=False`); không dùng ENUM gốc của MySQL. Cột `String` phải có độ dài (MySQL bắt buộc).

### Lệnh

Engine (trong `engine/`):

| Việc | Lệnh |
|---|---|
| Cài đặt | `uv sync --locked` |
| Test | `uv run --locked pytest -q` |
| Test + coverage | `uv run --locked pytest -q --cov=shiftopt` (thêm `--cov-fail-under=80` khi đã triển khai) |
| Lint / format | `uv run --locked ruff check .` · `uv run --locked ruff format --check .` |
| Type check | `uv run --locked mypy src tests benchmarks` |
| Benchmark | `uv run --locked python benchmarks/run_curtois_qu.py` |

Backend (trong `backend/`, copy `.env.example` thành `.env`):

| Việc | Lệnh |
|---|---|
| Cài đặt | `uv sync --locked` |
| Test | `uv run --locked pytest -q` (integration cần `SHIFTOPT_TEST_DATABASE_URL`) |
| Lint / format | `uv run --locked ruff check .` · `uv run --locked ruff format --check .` |
| Type check | `uv run --locked mypy src tests migrations/env.py scripts` |
| API | `uv run --locked uvicorn --factory src.main:create_app --reload` |
| Migration | `uv run --locked alembic revision --autogenerate -m "<msg>"` · `uv run --locked alembic upgrade head` · `uv run --locked alembic check` |
| OpenAPI | `uv run --locked python -m scripts.export_openapi` |
| Audit | `uv run --locked pip-audit` |

Frontend (trong `frontend/`): `npm ci` · `npm run dev` (proxy `/api` sang `localhost:8000`) · `npm run lint` · `npm run format` · `npm run typecheck` · `npm run gen:api` · `npm run ci` (Biome + tsc + build).

Ở root: `python scripts/check_conventions.py`; `make install|conventions|lint|typecheck|test|openapi|up|down`. Toàn bộ stack: `cp .env.example .env` rồi `docker compose up -d --build`; service `migrate` chạy `alembic upgrade head` một lần, `backend` chỉ khởi động sau khi nó xong; UI ở `http://localhost:3000`. Pre-commit: `pre-commit install` (hook: ruff engine + backend, uv-lock, check_conventions).

Autogenerate migration cần một database rỗng. Khi chưa có MySQL, có thể sinh bằng SQLite tạm (`SHIFTOPT_DATABASE_URL="sqlite+aiosqlite:///./boot.db" uv run --with aiosqlite alembic revision --autogenerate -m "<msg>"`), sau đó **review tay** cho MySQL: thay `sa.text('(CURRENT_TIMESTAMP)')` bằng `sa.func.now()`, kiểm tra mọi `String` có độ dài, bỏ dòng `# ###`, rồi chạy `alembic upgrade head` và `alembic check` trên MySQL thật (CI làm bước này).

### CI (`.github/workflows/ci.yml`, chạy trên push và PR vào `main`)

| Job | Kiểm tra |
|---|---|
| `conventions` | Không comment, code chỉ ASCII |
| `engine` | `ruff format --check`, `ruff check`, mypy strict, pytest + báo cáo coverage |
| `backend` | MySQL 8.4.10 service → lint, mypy → `alembic upgrade head` → `alembic check` → pytest → `openapi.json` khớp code |
| `frontend` | `npm ci`, `gen:api` khớp `types/api.ts`, Biome, `tsc --noEmit`, `vite build` |
| `images` | `docker compose config`, build image backend và frontend |
| `security` | gitleaks, pip-audit, `npm audit --omit=dev` |

Phiên bản đã ghim: MySQL 8.4.10, Python 3.11.16 (image), Node 22.23.3 (image + CI), nginx 1.30.5, uv 0.10.10; Python deps xem `engine/pyproject.toml`, `backend/pyproject.toml`; JS deps xem `frontend/package.json`.

---

## 13. Tiêu chí nghiệm thu bản đầu

Rút từ khuyến nghị của báo cáo nghiên cứu nền; điều chỉnh khi đặc tả chốt khác.

| Tiêu chí | Kết quả bắt buộc |
|---|---|
| Ràng buộc cứng | 0 vi phạm, xác nhận bởi `validation.py` trên mọi nghiệm |
| Phủ nhu cầu | Coverage ≥ 98% ở kịch bản cơ sở |
| Hiệu năng | Tuần 7×24, 20–40 nhân viên, giải ≤ 60 giây, gap ≤ 1% |
| So sánh solver | CP-SAT và HiGHS trên cùng instance, có bảng kết quả |
| Độ nhạy | Đường cong `z(lambda)` cho `lambda` trong `[0.8, 1.3]`; heatmap chi phí biên theo giờ |
| Pháp lý | Cặp ca 14h–22h → 06h–14h bị cấm; ca 22h–06h rồi nghỉ ngày tiếp không vi phạm Đ.111 khi đủ 24 giờ liên tục |
| Tái lập | Cùng instance + seed + `num_workers = 1` → cùng objective |
| Test | Coverage `engine/` ≥ 80% |
| UI | Nhập nhu cầu → bấm Optimize → thấy lịch, coverage chart, cảnh báo tuân thủ, chi phí; kéo thanh trượt λ thấy đường cong độ nhạy |

---

## 14. Ngoài phạm vi bản đầu (có chủ đích)

Đừng triển khai những thứ sau trừ khi được yêu cầu rõ:

| Giới hạn bản đầu | Hướng mở rộng |
|---|---|
| Một địa điểm, một loại kỹ năng | Đa địa điểm, ma trận kỹ năng |
| Độ nhạy: quét tham số, dual LP, kịch bản | Stochastic hai giai đoạn, robust optimization |
| Chỉ lịch tuần (7×24) | Chân trời nhiều tuần, chu kỳ dài |
| Chỉnh tay bằng form, kiểm tra lại ràng buộc | Kéo-thả, Gantt theo giờ |
| Không huấn luyện mô hình dự báo | TFT / TimesNet, intraday re-forecasting |
| Xuất CSV | Xuất PDF |
| Không xác thực, không phân quyền | Tổ chức, vai trò, nhật ký duyệt |
| Không đo adherence với chấm công | Tích hợp chấm công |
| Không Redis/Celery, không WebSocket | — |
| Không Timefold, không Gurobi bắt buộc | Gurobi qua license học thuật như backend tùy chọn |

---

## 15. Điểm cần cẩn trọng khi viết báo cáo hoặc tài liệu

- Số SKU FreshRetailNet mâu thuẫn giữa dataset card (865) và arXiv (863).
- Split eval 7 ngày chỉ là suy luận số học cho tới khi kiểm bằng code.
- Số liệu bài báo FreshRetailNet (WAPE, uplift khuyến mãi, đỉnh hết hàng 26% lúc 20h) lấy từ bản v5; đối chiếu lại nếu dùng phiên bản arXiv khác.
- Số liệu Mittelmann trong báo cáo nghiên cứu lấy qua nguồn thứ cấp; nếu trích, ghi nguồn và ngày, không dùng làm số đo của nhóm.
- Tính năng của các hãng WFM ngoài Deputy và NICE chưa được kiểm chứng riêng; không trích tính năng của hãng cụ thể khi chưa kiểm trên trang của hãng.
- Kiến trúc `full-stack-fastapi-template` và Netflix Dispatch chưa được khảo sát; chỉ tham khảo thêm, không viện dẫn.
