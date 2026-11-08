# Kiến trúc hệ thống ShiftOpt

Cập nhật: 2026-11-08. Tài liệu này mô tả hệ thống theo từng tầng, kèm thuật toán và cách xử lý ở mỗi tầng, viết bằng ngôn ngữ tự nhiên. Công thức đầy đủ nằm ở [model.md](model.md).

## 1. Hệ thống làm gì

ShiftOpt nhận bốn thứ:

- nhu cầu theo giờ (mỗi giờ trong tuần cần bao nhiêu người);
- danh sách nhân viên;
- các mẫu ca;
- luật lao động.

Từ đó hệ thống xếp ca cho từng nhân viên, sao cho:

1. thiếu người ít nhất có thể;
2. chi phí lương thấp nhất;
3. không vi phạm Bộ luật Lao động 2019.

Sau đó hệ thống cho biết chi phí thay đổi ra sao khi nhu cầu hoặc giả định thay đổi.

## 2. Sơ đồ các tầng

```
┌──────────────────────────────────────────────────────────────┐
│ Tầng 1. Giao diện (React, trình duyệt)                      │
│   Nhu cầu · Nhân viên · Mẫu ca · Xếp lịch · Độ nhạy          │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP /api (JSON, file parquet)
┌──────────────────────────────▼───────────────────────────────┐
│ Tầng 2. API (FastAPI)                                        │
│   kiểm tra đầu vào · tạo job · trả kết quả · xuất CSV        │
└───────────────┬──────────────────────────────┬───────────────┘
                │ đọc/ghi                       │ giao việc nặng
┌───────────────▼──────────────┐ ┌─────────────▼───────────────┐
│ Tầng 4. Lưu trữ              │ │ Tầng 3. Xử lý nền            │
│   MySQL: hồ sơ, lượt giải    │ │   tiến trình con, giới hạn   │
│   File: dữ liệu mẫu demo     │ │   thời gian, giới hạn số job │
└──────────────────────────────┘ └─────────────┬───────────────┘
                                               │ gọi hàm thuần
┌──────────────────────────────────────────────▼───────────────┐
│ Tầng 5. Engine (thư viện Python `shiftopt`)                  │
│   5a Nhu cầu · 5b Tối ưu · 5c Kiểm tra luật · 5d KPI ·       │
│   5e Độ nhạy                                                 │
└──────────────────────────────────────────────────────────────┘
```

Quy tắc giữa các tầng:

- Các tầng chỉ gọi xuống, không gọi ngược lên. Việc nhẹ (ingest file doanh số, tính KPI, kiểm tra luật khi sửa tay) API gọi thẳng engine; việc nặng đi qua tầng xử lý nền.
- Engine không biết gì về web hay cơ sở dữ liệu. Nó chỉ nhận dữ liệu và trả kết quả, nên dễ kiểm thử và chạy lại được.
- Tầng kiểm tra luật (5c) không dùng chung mã với tầng tối ưu (5b). Nhờ vậy, nếu mô hình tối ưu có lỗi thì bộ kiểm tra vẫn bắt được.

---

## 3. Tầng 1: Giao diện

**Công nghệ:** React 19, TypeScript, Vite. Toàn bộ chữ tiếng Việt nằm trong một file duy nhất, `frontend/src/locales/vi.ts`. Biểu đồ tự vẽ bằng HTML/CSS và SVG, không dùng thư viện biểu đồ.

**Các màn hình:**

| Màn hình | Người dùng làm gì |
|---|---|
| Nhu cầu | Tạo hồ sơ nhu cầu theo một trong ba cách: lưới 7 × 24 nhập tay, nhập file CSV, hoặc ingest file doanh số (CSV hoặc parquet): người dùng chọn cột ngày, giờ, doanh số, và các giả định quy đổi |
| Nhân viên | Thêm, sửa nhân viên: lương theo giờ, giờ tối đa mỗi tuần, ngày không làm được, ngày muốn nghỉ |
| Mẫu ca | Khai báo ca: tên, giờ bắt đầu, độ dài |
| Xếp lịch | Chọn hồ sơ nhu cầu và mẫu ca, chỉnh thiết lập solver, bấm **Tối ưu**. Xem lịch, biểu đồ phủ, chi phí, cảnh báo luật. Sửa lịch bằng tay. **Xếp lại** khi có người vắng (ngày khóa, ca ghim). **Gợi ý người thay** cho một ca. Xuất CSV |
| Độ nhạy | Quét hệ số nhu cầu λ, quét giả định `alpha` / `p` / sàn, tính chi phí biên theo giờ, so sánh hai lượt giải |

**Cách xử lý:**

- **Hỏi lại trạng thái (poll).** Khi bấm **Tối ưu**, giao diện nhận ngay một mã job. Sau đó cứ mỗi giây giao diện hỏi lại cho tới khi job xong. Trang không bị treo trong lúc solver chạy.
- **Kiểu dữ liệu sinh tự động.** Kiểu dữ liệu TypeScript sinh từ mô tả API (OpenAPI) của backend, không viết tay. Vì vậy giao diện và API luôn khớp nhau.
- **Kiểm tra sớm.** Giao diện lấy bộ luật mặc định từ `GET /api/labor-rules` để hiện giới hạn luật và cảnh báo khi người dùng nhập giá trị vượt luật, ví dụ độ dài ca. Backend vẫn kiểm tra lại lần nữa.
- **Không chỉ dùng màu.** Thông tin thiếu người, thừa người, vi phạm luật luôn có thêm sọc, nét đứt, biểu tượng hoặc chữ đi kèm, không chỉ phân biệt bằng màu.

---

## 4. Tầng 2: API

**Công nghệ:** FastAPI, Pydantic v2. Mỗi nhóm chức năng (`demand`, `employees`, `shifts`, `schedules`, `analysis`, `rules`) có bốn file:

- `router` nhận yêu cầu HTTP;
- `schemas` mô tả dữ liệu vào và ra;
- `service` chứa logic;
- `models` mô tả bảng trong cơ sở dữ liệu.

**Cách xử lý:**

1. **Kiểm tra ở cửa vào.** Mọi dữ liệu gửi lên đều được kiểm tra trước khi xử lý. Ví dụ:
   - lưới nhu cầu phải đủ 168 ô, mỗi ô là số nguyên từ 0 đến 1000;
   - giờ tối đa của một nhân viên không vượt 48;
   - số nhân viên và thời gian giải có giới hạn trên, để một yêu cầu không chiếm hết máy;
   - mẫu ca dài hơn 8 giờ bị từ chối ngay khi tạo hoặc sửa (giới hạn `max_daily_hours` của Đ.105). Vì một người làm tối đa 1 ca/ngày, điều này bảo đảm không ai làm quá 8 giờ/ngày. Solver không cần ràng buộc riêng cho giới hạn ngày, còn validator vẫn kiểm lại.

   Sai thì trả lỗi kèm thông điệp rõ ràng, ví dụ `demand grid must have 168 cells`, không lộ chi tiết lỗi nội bộ (stack trace).
2. **Việc nhẹ làm ngay.** Thêm hoặc sửa nhân viên, đọc CSV, ingest file doanh số, xuất CSV đều xong trong vài giây và trả kết quả trực tiếp.
3. **Việc nặng giao cho tầng 3.** Giải lịch và phân tích độ nhạy có thể mất hàng chục giây. API tạo một dòng job trong cơ sở dữ liệu, trả mã job ngay (`202 Accepted`), rồi giao việc cho tầng xử lý nền.
4. **Chụp ảnh đầu vào (snapshot).** Trước khi giải, API chép toàn bộ đầu vào vào lượt giải: nhu cầu, nhân viên, mẫu ca, bộ luật (`LaborRules`), tham số solver. Sau này có sửa nhân viên thì lượt giải cũ vẫn giữ nguyên dữ liệu lúc giải. Mỗi lượt giải không bao giờ bị sửa.

5. **Xếp lại và gợi ý người thay.** `POST /api/schedules/{id}/repair` tạo lượt mới từ lịch của lượt `id` (chi tiết ở mục 7.2). Trước khi tạo job, API kiểm: ngày vắng không rơi vào ngày khóa, ca ghim không rơi vào ngày khóa, và tập ca bị khóa qua được validator; sai thì trả `422` kèm danh sách. `GET /api/schedules/{id}/replacements?employee_code=&day=&limit=` trả tối đa `limit` người thay, tính ngay vì chỉ gọi validator, không gọi solver.

**Ingest file doanh số** (`POST /api/demand-profiles/ingest`):

- Nhận file CSV hoặc parquet (tối đa 200 MB), kèm mapping cột và các giả định quy đổi. Trước đó, `POST /api/demand-profiles/ingest/inspect` đọc tên cột để gợi ý mapping.
- Tính mã kiểm SHA-256 của file để biết chính xác dữ liệu vào là file nào.
- Gọi `derive_demand` (tầng 5a) để gộp doanh số thành tuần 168 giờ và quy đổi ra số người. Hồ sơ lưu tuần tải vào cột `sales_load`, còn SHA-256 của file và mapping cột vào metadata, nên quét giả định không cần file gốc nữa.

---

## 5. Tầng 3: Xử lý nền

**Mục đích:** solver tốn nhiều CPU. Nếu chạy solver ngay trong máy chủ web, mọi yêu cầu khác sẽ bị chặn trong lúc chờ.

**Cách xử lý:**

1. **Một pool tiến trình dùng chung.** Backend tạo một `ProcessPoolExecutor` duy nhất với `max_concurrent_jobs` tiến trình (mặc định 2). Job giải lịch và job phân tích dùng chung pool này. Job không có tiến trình riêng: pool đang bận thì job mới chờ trong hàng đợi của pool.
2. **Giới hạn thời gian.** Mỗi job có hạn chót. Job giải lịch được time limit của solver cộng 30 giây; job phân tích được `max_analysis_seconds` cộng 30 giây. Quá hạn thì job bị đánh dấu `failed`, kèm lý do "solver exceeded its time limit". Hạn chót chỉ dừng việc **chờ** kết quả. `ProcessPoolExecutor` không hủy được tác vụ đang chạy, nên tiến trình vẫn chạy tới khi tự xong và vẫn chiếm một chỗ trong pool. Với lượt giải lịch, việc này hiếm: CP-SAT tự dừng theo time limit, trước hạn chót 30 giây. Job phân tích khác ở chỗ `max_analysis_seconds` (mặc định 900 giây) là hạn chót cho **cả job**, còn time limit chỉ áp cho **từng lần giải**. Chi phí biên giải 169 lần, quét λ giải nhiều điểm, nên tổng thời gian vẫn có thể vượt hạn chót nếu mỗi lần giải chạy dài.
3. **Giới hạn số job.** API đếm các job ở trạng thái `queued` hoặc `running` trong cơ sở dữ liệu. Đủ `max_pending_jobs` (mặc định 4) thì job mới bị từ chối với lỗi `429`. Bộ đếm này dựa trên trạng thái trong DB, không dựa trên tiến trình thật. Một job đã bị đánh dấu `failed` vì quá hạn mà tiến trình vẫn chạy thì không còn được đếm.
4. **Phục hồi sau khi khởi động lại.** Nếu backend tắt giữa chừng, lúc khởi động lại mọi job đang `queued` hoặc `running` được đánh dấu `failed` với lý do "server restarted". Không có job nào treo mãi.
5. **Kiểm tra lại sau khi giải.** Khi tiến trình con trả lịch về, tầng này gọi bộ kiểm tra luật (5c):
   - Nếu có vi phạm, lượt giải bị đánh dấu `failed`, kèm số vi phạm.
   - Nếu không có vi phạm, lượt giải là `succeeded`.

   Hệ thống không tin trạng thái của solver.

Bản đầu cố ý không dùng Redis, Celery hay WebSocket. Một bảng job trong MySQL cộng với việc giao diện hỏi lại trạng thái là đủ.

---

## 6. Tầng 4: Lưu trữ

| Nơi | Lưu gì |
|---|---|
| MySQL 8.4, bảng `demand_profiles` | Hồ sơ nhu cầu: 168 con số, nguồn, giả định quy đổi, phương pháp xử lý |
| `employees`, `shift_templates` | Nhân viên, mẫu ca |
| `solve_runs` | Mỗi lượt giải: ảnh chụp đầu vào, tham số, solver và phiên bản, seed, trạng thái, mục tiêu, cận, gap, thời gian, log solver, lịch kết quả, số vi phạm |
| `analysis_runs` | Mỗi lần phân tích độ nhạy: loại phân tích, tham số, kết quả |
| Cột `sales_load` của `demand_profiles` | Tuần tải 168 giờ của hồ sơ ingest; metadata ghi SHA-256, mapping cột, phương pháp, số ô đã thay, `night_from_sales` |
| File `data/demo/` | File dùng khi demo: `train.parquet` và CSV mẫu |

Lưu đủ các thông tin trên để có thể chạy lại một lượt giải và nhận đúng kết quả cũ (tái lập). Schema cơ sở dữ liệu chỉ đổi qua migration của Alembic.

---

## 7. Tầng 5: Engine

Engine là thư viện Python thuần, tên `shiftopt`. Hàm của engine là hàm thuần: không đọc file, không đọc biến môi trường, không ghi log. Phần tính nhu cầu, validator và KPI luôn cho cùng kết quả với cùng đầu vào. Phần solver cho cùng kết quả với cùng đầu vào, 1 worker, cùng seed, khi giải xong trước time limit (xem mục 7.2). Engine gồm năm khối.

### 7.1 Khối 5a: Từ doanh số tới số người cần

Áp dụng cho mọi file doanh số ingest, không riêng FreshRetailNet-50K. Doanh số không phải dữ liệu nhân sự: số người suy ra từ giả định của nhóm.

**Bước 1. Đọc và chọn cột.** File được đọc theo định dạng của nó: parquet, hoặc CSV với dấu phân cách tự nhận (`,`, `;`, tab). Chỉ các cột người dùng chỉ ra được dùng: ngày, giờ (nếu tách riêng), doanh số, hết hàng và sản phẩm (tùy chọn), cửa hàng (khi file có nhiều cửa hàng). Doanh số có thể là một dòng mỗi giờ, hoặc một dòng mỗi ngày-sản phẩm với 24 giá trị theo giờ. Các dòng trùng (cùng sản phẩm, ngày, giờ) được cộng lại.

**Bước 2. Ước lượng nhu cầu ẩn cho giờ hết hàng.**

- *Vấn đề:* giờ hết hàng thì doanh số thấp hơn nhu cầu thật, vì khách muốn mua mà không có hàng. Dùng thẳng doanh số sẽ đánh giá thấp nhu cầu.
- *Cách làm:* mỗi ô (sản phẩm, ngày, giờ) bị đánh dấu hết hàng được thay bằng trung bình doanh số của **cùng sản phẩm, cùng thứ trong tuần, cùng giờ**, chỉ tính các ngày còn hàng. Ví dụ: sản phẩm A hết hàng lúc 20h một thứ Sáu, thì lấy trung bình doanh số 20h của A ở các thứ Sáu còn hàng.
- Nếu không có ngày nào để đối chiếu, ô đó giữ nguyên số quan sát và được đếm riêng.
- Với store 18: 90.159 ô được thay, 1.008 ô giữ nguyên.

**Bước 3. Gộp thành một tuần điển hình.** Cộng doanh số mọi sản phẩm theo từng giờ, rồi lấy trung bình theo thứ trong tuần qua tất cả các tuần có trong dữ liệu. Kết quả là 168 con số gọi là "tải". Ví dụ, giờ 19h thứ Hai là trung bình tải lúc 19h của mọi thứ Hai.

**Bước 4. Giờ đêm.** Mặc định, giờ 22h–06h đặt tải bằng 0, vì doanh số ban đêm không mô tả nhu cầu nhân sự. Số người giờ đêm lấy theo "sàn đêm" do người dùng nhập. Nếu bật `night_from_sales` và dữ liệu có doanh số đêm thật, dùng doanh số đêm như các giờ khác.

**Bước 5. Quy đổi ra số người.** Mỗi giờ:

```
số người = max(sàn, làm tròn lên(alpha × tải / p))
```

- `alpha` (giải chuẩn hóa) đổi chỉ số doanh số chuẩn hóa về đơn vị thật.
- `p` (năng suất) là lượng tải một người xử lý được trong một giờ.
- `sàn` là số người tối thiểu, có sàn ngày và sàn đêm riêng.
- Cả bốn là **giả định của nhóm**. Chúng luôn hiện trên giao diện và được đưa vào phân tích độ nhạy (mục 7.5).
- **`alpha` và `p` thực chất là một giả định.** Công thức chỉ dùng tỷ số `alpha / p`: `alpha = 1, p = 4` và `alpha = 0,5, p = 2` cho cùng số người. Hệ thống giữ hai ô riêng để tách hai câu hỏi (đổi đơn vị doanh số, và năng suất một người), nhưng khi phân tích chỉ cần quét một trong hai.

Hai cách tạo nhu cầu khác không qua khối này:

- **Nhập tay:** gõ thẳng 168 số.
- **CSV:** đọc file có 7 dòng × 24 cột, hoặc một cột 168 giá trị. Bộ đọc tự nhận dấu phân cách (`,`, `;`, tab) và bỏ qua dòng tiêu đề. Ô sai thì báo đúng dòng và cột.

### 7.2 Khối 5b: Tối ưu hóa, tức xếp ca

Hệ thống có hai mô hình. Mô hình theo nhân viên tạo lịch thật. Mô hình tổng hợp dùng cho phân tích độ nhạy và đối chiếu.

#### Mô hình theo nhân viên (lõi sản phẩm), giải bằng OR-Tools CP-SAT

**Biến quyết định.** Với mỗi nhân viên `e`, mỗi ngày `d`, mỗi ca `s` có một biến có/không: `x[e, d, s] = 1` nghĩa là `e` làm ca `s` vào ngày `d`. Với 30 nhân viên, 7 ngày, 3 ca, mô hình có 630 biến chính. Ngoài ra còn biến giờ nghỉ, biến thiếu người mỗi giờ, và biến phục vụ ràng buộc nghỉ tuần.

**Tuần vòng.** Tuần được coi là một vòng tròn: sau Chủ nhật là thứ Hai. Nhờ vậy, khi lịch lặp lại tuần sau, ca tối Chủ nhật và ca sáng thứ Hai vẫn được kiểm tra nghỉ 12 giờ.

**Ràng buộc cứng.** Solver không bao giờ được vi phạm:

| Ràng buộc | Cách cài, nói dễ hiểu |
|---|---|
| Tối đa 1 ca/ngày | Với mỗi người, mỗi ngày, tổng các ca ≤ 1 |
| Tối đa 48 giờ/tuần (Đ.105) | Tổng giờ các ca của một người trong tuần ≤ 48, hoặc ≤ giới hạn riêng nếu thấp hơn (ví dụ E07 chỉ 24 giờ) |
| Nghỉ ≥ 12 giờ giữa hai ca (Đ.110) | Trước khi giải, liệt kê mọi cặp (ca hôm trước, ca hôm sau) có khoảng nghỉ dưới 12 giờ. Khoảng nghỉ tính bằng công thức tổng quát `24 × số ngày cách + giờ bắt đầu ca sau − (giờ bắt đầu ca trước + độ dài)`. Mỗi cặp bị cấm thì một người không được làm cả hai. Ví dụ ca Tối 16h–24h rồi ca Ngày 8h hôm sau chỉ nghỉ 8 giờ, nên bị cấm |
| Tối đa 6 ngày làm liên tiếp | Mọi cửa sổ 7 ngày liên tiếp (tính vòng) phải có ít nhất 1 ngày nghỉ |
| Nghỉ ≥ 24 giờ liên tục mỗi tuần (Đ.111) | Với mỗi người, mỗi giờ trong tuần có một biến "khoảng nghỉ 24 giờ bắt đầu từ đây". Nếu chọn biến này thì 24 giờ tiếp theo người đó không làm. Bắt buộc chọn ít nhất một giờ bắt đầu. Ràng buộc này tính trên trục giờ, không chỉ đếm ngày nghỉ, vì ca qua đêm có thể làm ngày nghỉ không đủ 24 giờ |
| Nghỉ giữa ca (Đ.109) | Mỗi ca từ 6 giờ trở lên có đúng một giờ nghỉ, đặt ở giờ thứ 2 đến giờ áp chót của ca. Trong giờ nghỉ, người đó không được tính vào số người có mặt. Nghỉ 30 hoặc 45 phút được làm tròn thành cả giờ, tức chọn phương án an toàn |
| Ngày không làm được | Không xếp ca vào ngày nhân viên đã báo bận |

**Phủ nhu cầu là ràng buộc mềm.** Mỗi giờ có một biến "thiếu người" `u`, với điều kiện:

```
số người có mặt − số người đang nghỉ giữa ca + u ≥ nhu cầu
```

Nhờ có biến `u`, mô hình luôn có lời giải kể cả khi thiếu nhân viên. Khi đó giao diện chỉ ra giờ nào thiếu, thay vì báo "vô nghiệm".

**Mục tiêu: giải theo tầng (lexicographic).** Thay vì gộp mọi thứ vào một hàm có trọng số tùy chọn, hệ thống giải lần lượt bốn lần:

1. **Tầng 1:** tối thiểu tổng giờ thiếu người.
2. **Tầng 2:** giữ nguyên số giờ thiếu vừa đạt, rồi tối thiểu chi phí lương. Chi phí một ca = lương × độ dài + 30% × lương × số giờ đêm của ca (phụ cấp đêm, Đ.98). Ví dụ với lương 100: ca Ngày tốn 800, ca Đêm 0h–8h tốn 980 (có 6 giờ đêm).
3. **Tầng 3:** giữ nguyên hai kết quả trên, rồi chia ca đêm công bằng nhất, tức tối thiểu chênh lệch giữa người làm nhiều ca đêm nhất và người làm ít nhất.
4. **Tầng 4:** chỉ khi có người đăng ký ngày muốn nghỉ, tối thiểu số lần xếp ca vào ngày đó.

**Giờ nghỉ được lưu theo từng ca.** Solver chọn giờ nghỉ cho mỗi ca cần nghỉ. Lịch lưu giờ này thành `break_offset` trong từng dòng phân ca: số giờ tính từ đầu ca, ví dụ ca Ngày 8h có `break_offset = 4` là nghỉ lúc 12h. KPI dùng `break_offset` để trừ người đang nghỉ khỏi số người có mặt; validator kiểm tra `break_offset` nằm trong khoảng cho phép. Khi sửa lịch bằng tay, **người dùng chọn** giờ nghỉ ở cột **Bắt đầu nghỉ**. Đổi ca thì giờ nghỉ bị xóa và phải chọn lại. Để trống ở ca cần nghỉ thì validator báo vi phạm Đ.109.

Mỗi tầng không được làm xấu kết quả tầng trước. Thời gian giải chia đều cho các tầng. Lời giải tầng trước được dùng làm gợi ý khởi đầu cho tầng sau, giúp solver tìm nhanh hơn.

**Trạng thái trả về:**

- `OPTIMAL`: mọi tầng đều được chứng minh tối ưu.
- `FEASIBLE`: có lịch hợp lệ nhưng chưa chứng minh tốt nhất trong thời gian cho phép. Luôn kèm gap, tức khoảng cách tối đa tới lịch tốt nhất.

**Tái lập.** Với 1 worker và cùng seed, cùng đầu vào cho cùng lịch **khi mọi tầng giải xong trước time limit** (trạng thái `OPTIMAL`). Nếu hết giờ ở trạng thái `FEASIBLE`, lịch trả về là lịch tốt nhất tìm được tới lúc dừng, nên phụ thuộc tốc độ và tải của máy lúc chạy.

**Phá đối xứng (tùy chọn, chưa bật trong API).** Hai nhân viên cùng lương và không có yêu cầu riêng thì hoán đổi được cho nhau. Engine có thể sắp xếp họ theo số ca để không phải xét các lịch chỉ khác nhau ở việc đổi tên người. Không áp cho người có yêu cầu riêng, vì có thể làm mất lời giải tốt nhất. Backend hiện gọi solver không bật tùy chọn này, và cũng không bật chế độ phân rã hai pha.

#### Xếp lại từ lịch gốc (repair)

Dùng khi lịch đã công bố và có biến động giữa tuần, ví dụ người báo ốm (đặc tả D20).

- **Đầu vào:** lịch gốc (một lượt đã có lịch), ngày bắt đầu xếp lại `from_day`, danh sách người vắng theo ngày, các ca ghim. Có thể đổi hồ sơ nhu cầu.
- **Khóa:** mọi ngày trước `from_day` giữ nguyên lịch gốc, kể cả giờ nghỉ giữa ca. Ca ghim bắt buộc có mặt. Ngày vắng được thêm vào ngày không làm được của người đó.
- **Mục tiêu:** chèn một tầng mới ngay sau tầng thiếu người: tối thiểu **số ca thay đổi** so với lịch gốc, đếm theo bộ (nhân viên, ngày, ca); đổi giờ nghỉ trong cùng ca không tính. Thứ tự là thiếu người, thay đổi, chi phí, công bằng ca đêm, mong muốn nghỉ. Lịch gốc được dùng làm gợi ý khởi đầu.
- **Luôn có lời giải.** Mọi luật cứng đều "đơn điệu": bỏ bớt ca không bao giờ tạo vi phạm mới. Vì vậy nếu riêng tập ca bị khóa qua được validator thì lịch "chỉ gồm các ca bị khóa" đã hợp lệ, và solver luôn tìm được lời giải. API kiểm tập này trước khi tạo job.
- Không bật phá đối xứng hay phân rã khi repair, vì lịch gốc làm các nhân viên không còn hoán đổi được cho nhau.
- Lượt repair lưu lịch gốc, `from_day` và ca ghim trong ảnh chụp đầu vào, nên chạy lại được. Giao diện đánh dấu ô khác lịch gốc bằng chữ "đổi" và ngày khóa bằng nhãn "khóa".

**Gợi ý người thay.** Với một ca (người vắng, ngày), thử lần lượt từng nhân viên còn trống ngày đó, giao đúng ca đó với cùng giờ nghỉ, rồi chạy validator trên cả lịch. Chỉ giữ người không gây vi phạm. Xếp theo: người có đăng ký muốn nghỉ ngày đó xếp sau, rồi chi phí thêm thấp hơn, rồi số giờ trong tuần ít hơn. Bấm **Áp dụng** thì tạo lượt sửa tay mới, validator kiểm lại như mọi lượt sửa tay.

#### Mô hình tổng hợp (phủ tập Dantzig), giải bằng PuLP + HiGHS

Mô hình này không hỏi "ai làm ca nào" mà chỉ hỏi "mỗi ngày, mỗi loại ca cần **bao nhiêu người**".

- Biến: số người bắt đầu ca `s` vào ngày `d`, là số nguyên không âm.
- Ràng buộc: mỗi giờ, tổng số người của các ca phủ giờ đó (trừ người đang nghỉ giữa ca) ≥ nhu cầu. Ở mô hình này, phủ nhu cầu là ràng buộc cứng.
- Mục tiêu: tối thiểu tổng chi phí, với mọi người cùng một mức lương do người dùng nhập.
- **Nghỉ giữa ca ngầm (kiểu Bechtold–Jacobs).** Thêm biến "số người nghỉ ở giờ k của ca s". Tổng số người nghỉ của một ca bằng số người làm ca đó. Cách này cho cùng kết quả với việc liệt kê mọi tổ hợp (ca, giờ nghỉ), nhưng ít biến hơn nhiều.

Mô hình này nhỏ và giải rất nhanh, nên được dùng để:

- tính chi phí biên theo giờ, cần 169 lần giải;
- lấy dual của bài toán nới lỏng (mục 7.5);
- đối chiếu CP-SAT với HiGHS trong benchmark.

### 7.3 Khối 5c: Kiểm tra luật độc lập (validator)

**Nguyên tắc:** solver đề xuất, validator phán xét. Validator kiểm tra lại toàn bộ luật **trên lịch kết quả**, bằng mã viết riêng, không dùng chung bất kỳ phần nào với mô hình tối ưu.

**Cách kiểm tra:**

1. Đổi mỗi ca được giao thành một đoạn trên trục giờ tuyệt đối, từ giờ 0 đến giờ 167 và quấn vòng. Ví dụ ca Tối thứ Hai là đoạn [16, 24).
2. Với từng nhân viên, xếp các đoạn theo thời gian rồi kiểm tra:
   - không có hai ca trong cùng một ngày;
   - giờ mỗi ngày ≤ 8, giờ mỗi tuần ≤ 48 hoặc ≤ giới hạn riêng;
   - mọi khoảng trống giữa hai ca liên tiếp ≥ 12 giờ (Đ.110);
   - khoảng trống dài nhất trong tuần ≥ 24 giờ (Đ.111);
   - số ngày làm liên tiếp dài nhất (tính vòng) ≤ 6;
   - mỗi ca cần nghỉ có giờ nghỉ nằm trong khoảng cho phép (Đ.109);
   - không có ca nào vào ngày nhân viên đã báo không làm được.
3. Trả về danh sách vi phạm. Mỗi vi phạm gồm loại, nhân viên và chi tiết. Giao diện gắn loại vi phạm với điều luật tương ứng (Đ.105, Đ.109, Đ.110, Đ.111) khi hiển thị.

**Khi nào chạy:** sau mỗi lượt giải (kể cả repair), sau mỗi lần người dùng sửa lịch bằng tay, trên tập ca bị khóa trước khi tạo job repair, và với từng ứng viên khi gợi ý người thay.

**Trạng thái khi có vi phạm.** Quy tắc giống nhau cho lượt do solver tạo và lượt sửa tay: có ít nhất một vi phạm cứng thì lượt đó có trạng thái `failed`, kèm thông điệp "validator found N hard-constraint violations". Ở đây `failed` nghĩa là **"đây không phải lịch hợp lệ để dùng"**, không phải lỗi hệ thống. Lượt vẫn được lưu đầy đủ: lịch, biểu đồ, KPI và danh sách vi phạm vẫn xem được. Khung **Tuân thủ** liệt kê từng vi phạm theo điều luật.

Sửa tay luôn tạo một lượt mới, ghi "sửa từ lượt …"; lịch gốc không bị đổi. Demo dùng đúng hành vi này: lượt sửa tay có ca Tối rồi ca Ngày hôm sau (nghỉ 8 giờ) bị đánh dấu `failed` với 1 vi phạm Đ.110, còn lượt gốc vẫn `succeeded` với 0 vi phạm.

### 7.4 Khối 5d: Chỉ số (KPI)

Tính trực tiếp từ lịch, không lấy từ solver:

| Chỉ số | Cách tính, nói dễ hiểu |
|---|---|
| Số người có mặt mỗi giờ | Đếm người đang trong ca ở giờ đó, trừ người đang nghỉ giữa ca |
| Tỷ lệ phủ | Tổng phần nhu cầu được đáp ứng ÷ tổng nhu cầu. 100% là không thiếu giờ nào |
| Giờ thiếu / giờ thừa | Cộng phần thiếu / phần dư của từng giờ |
| Hiệu suất lịch | Tổng nhu cầu ÷ tổng người có mặt. Càng gần 1 càng ít thừa |
| Chi phí lao động | Tổng lương các ca cộng phụ cấp đêm 30% |
| Tỷ lệ chi phí lao động | Chi phí ÷ doanh thu giả định do người dùng nhập |
| Công bằng | Độ lệch chuẩn số ca đêm và số ca cuối tuần giữa các nhân viên |

### 7.5 Khối 5e: Phân tích độ nhạy

**Nguyên tắc:** bài toán có biến nguyên thì không có "giá bóng" (shadow price) đáng tin. Vì vậy độ nhạy được tính bằng **giải lại thật**.

**(1) Quét hệ số nhu cầu λ.**

- Với λ = 0,8; 0,9; 1,0; 1,1; 1,2; 1,3: nhân mọi ô nhu cầu với λ rồi làm tròn lên, giải lại toàn bộ lịch bằng mô hình theo nhân viên.
- Kết quả là đường chi phí z(λ), số giờ thiếu và số người theo giờ ở từng mức. Thanh trượt trên giao diện cho xem từng điểm.
- Các điểm có thể giải song song.
- Điểm nào không đạt `OPTIMAL` được đánh dấu "chưa chứng minh tối ưu", để không đọc nhầm khoảng gap thành thay đổi chi phí.

**(2) Quét giả định quy đổi.**

- Chọn một giả định (`alpha`, `p`, sàn ngày hoặc sàn đêm) và vài giá trị thử.
- Với mỗi giá trị, tính lại số người từ tải gốc của store (khối 5a, bước 4–5), rồi giải lại lịch.
- Kết quả trả lời câu hỏi: nếu giả định của nhóm sai đi một chút, chi phí thay đổi bao nhiêu.
- Quét `alpha` và quét `p` là thừa nhau, vì chỉ tỷ số `alpha / p` ảnh hưởng tới kết quả: tăng `alpha` 20% tương đương chia `p` cho 1,2. Chọn một trong hai, cộng thêm một lần quét sàn nếu cần.
- Ví dụ store 18: `alpha` = 0,8 / 1,0 / 1,2 cho chi phí tuần 71.660 / 88.920 / 104.880.

**(3) Chi phí biên theo giờ.**

- Giải mô hình tổng hợp một lần với nhu cầu gốc, được chi phí z.
- Với mỗi giờ t trong 168 giờ: thêm 1 người vào nhu cầu giờ t, giải lại, được z'. Chi phí biên của giờ t là z' − z.
- Tổng cộng 169 lần giải số nguyên (1 lần gốc và 168 lần cho từng giờ). Kết quả hiện thành bản đồ nhiệt 7 × 24: giờ nào đắt nhất nếu cần thêm một người.
- Cùng job này giải thêm 1 lần bài toán nới lỏng để lấy dual (mục (4)), rồi đặt dual cạnh chi phí biên của từng giờ.
- Chi phí biên thường là một bậc: thêm 1 người có thể buộc mở thêm cả một ca 8 tiếng, hoặc tốn 0 nếu giờ đó đang thừa người.

**(4) Dual của bài toán nới lỏng (LP).**

- Bỏ điều kiện "số người phải nguyên" trong mô hình tổng hợp, giải bằng HiGHS, rồi lấy dual của ràng buộc phủ từng giờ.
- Dual là ước lượng chi phí của một đơn vị nhu cầu thêm, nhưng chỉ đúng cho bài toán nới lỏng. Vì vậy luôn gắn nhãn **"xấp xỉ"**.
- Bảng so sánh dual với chi phí biên thật ở (3) cho thấy chênh lệch do tính nguyên ở từng giờ.

**Lưu ý chung cho (3) và (4).** Hai phân tích này chạy trên **mô hình tổng hợp**, không trên đội 30 người thật. Mô hình tổng hợp:

- không giới hạn số người, nên luôn thuê thêm được;
- định giá mọi ca bằng một mức lương do người dùng nhập;
- bỏ các luật theo từng người: 48 giờ/tuần, nghỉ 12 giờ giữa ca, 6 ngày liên tiếp, nghỉ 24 giờ mỗi tuần, ngày bận, giờ tối đa riêng.

Vì vậy kết quả **không phải** chi phí thêm một người cho đội hiện tại. Nó là chi phí biên của một cửa hàng lý tưởng, thuê bao nhiêu ca cũng được. Với đội thật, thêm nhu cầu có thể tốn hơn, hoặc không đáp ứng được vì hết người hay vướng luật nghỉ. Muốn biết tác động lên đội thật, dùng quét λ ở (1), vì (1) giải lại bằng mô hình theo nhân viên.

**(5) So sánh hai kịch bản.** Chọn hai lượt giải bất kỳ, đặt cạnh nhau tỷ lệ phủ, giờ thiếu, chi phí và các chỉ số khác.

---

## 8. Một lần bấm "Tối ưu" đi qua các tầng thế nào

1. **Giao diện:** người dùng chọn hồ sơ `Store 18 demo`, 3 ca, 1 worker, seed 0, rồi bấm **Tối ưu**.
2. **API:**
   - kiểm tra đầu vào (số nhân viên, thời gian giải, ca có tồn tại không);
   - chụp ảnh đầu vào;
   - tạo dòng `solve_runs` ở trạng thái `queued`;
   - trả mã job.
3. **Giao diện:** chuyển sang trang lượt giải và bắt đầu hỏi lại trạng thái.
4. **Xử lý nền:** đổi trạng thái sang `running`, giao việc cho một tiến trình trong pool, kèm hạn chót.
5. **Engine, khối 5b:** dựng mô hình CP-SAT rồi giải bốn tầng: thiếu người, chi phí, công bằng ca đêm, mong muốn nghỉ.
6. **Xử lý nền:**
   - nhận lịch;
   - gọi **khối 5c** kiểm tra lại toàn bộ luật;
   - lưu trạng thái solver, gap, thời gian, log, lịch và số vi phạm;
   - đánh dấu `succeeded`, hoặc `failed` nếu có vi phạm hoặc không tìm được lịch.
7. **Giao diện:** nhận kết quả, gọi API lấy KPI (**khối 5d**) và danh sách vi phạm. Hiện trạng thái `OPTIMAL`, lưới lịch, biểu đồ phủ, chi phí và khung tuân thủ.

Lần đo ngày 2026-11-06 với 30 nhân viên và store 18: toàn bộ mất khoảng 7 giây, phủ 100%, 0 vi phạm.

---

## 9. Triển khai

Docker Compose dựng năm dịch vụ:

| Dịch vụ | Vai trò |
|---|---|
| `db` | MySQL 8.4 |
| `migrate` | Chạy migration một lần để tạo hoặc nâng cấp bảng |
| `backend` | API FastAPI (uvicorn) |
| `seed` | Nạp 30 nhân viên và 3 mẫu ca demo khi bảng còn trống. Không nạp hồ sơ nhu cầu: nhu cầu được tạo bằng ingest trên web |
| `frontend` | Giao diện đã build, phục vụ bằng nginx; chuyển `/api` sang backend; nhận file tải lên tới 200 MB |

Lệnh: `docker compose up -d --build`, rồi mở `http://localhost:3000`.

## 10. Giới hạn đã biết

- Nhu cầu từ file doanh số là tuần trung bình của dữ liệu quá khứ, chưa phải dự báo tuần tới. Chưa đo sai số dự báo.
- Giờ nghỉ giữa ca được làm tròn thành cả giờ.
- Tái lập chỉ chắc chắn khi lượt giải kết thúc `OPTIMAL` trước time limit.
- Giới hạn số job đếm trạng thái trong DB rồi mới thêm job, không khóa. Khi nhiều yêu cầu đến cùng lúc, số job thật có thể vượt nhẹ `max_pending_jobs`.
- Chi phí biên và dual LP tính trên mô hình tổng hợp, không trên đội thật (mục 7.5).
- Xử lý nền (mục 5), chưa sửa trong code (đặc tả D15):
  - Hạn chót của job tính từ lúc job được gửi vào pool, nên **thời gian chờ trong hàng đợi cũng bị tính**. Một job xếp sau hai phân tích dài có thể bị đánh dấu `failed` vì quá hạn trước khi kịp chạy.
  - Job quá hạn không bị dừng thật; tiến trình chạy tiếp tới khi tự xong.
  - Quét λ mở thêm một pool con để giải các điểm song song, nên số tiến trình thật có thể nhiều hơn `max_concurrent_jobs`.
- Chỉ hỗ trợ một địa điểm, một loại kỹ năng, một tuần. Không hỗ trợ tổng đài (đặc tả D18).
- Repair khóa theo ngày, không theo giờ. Tuần vẫn quấn vòng, nên ca của ngày bị khóa vẫn ràng buộc ca Chủ nhật qua luật nghỉ 12 giờ và 24 giờ.
- Gợi ý người thay chỉ xét giao nguyên ca cho một người khác; không đổi chéo hai người, không đổi loại ca.
- Repair và gợi ý người thay chưa chạy integration test trên MySQL và chưa duyệt trên trình duyệt.
- Nội dung điều luật chưa được đối chiếu với nguyên văn văn bản luật ([đặc tả.md](đặc%20tả.md) mục 4).
- Mọi số liệu hiệu năng chỉ đúng cho các trường hợp đã đo ([benchmarks.md](benchmarks.md)).
