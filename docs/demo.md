# Kịch bản demo ShiftOpt trước lớp

Cập nhật: 2026-11-06. Thời lượng: khoảng 20 phút trình bày, cộng 5 phút hỏi đáp.

Tài liệu gồm sáu phần:

- A. Dự án làm gì: phần để hiểu trước khi lên lớp.
- B. Chuẩn bị trước buổi.
- C. Kịch bản từng bước: thao tác, lời nói, ý nghĩa, kết quả mong đợi.
- D. Câu hỏi hay gặp.
- E. Sự cố và dự phòng.
- F. Phần chưa kiểm.

---

## A. Dự án làm gì

### A1. Bài toán trong một câu

Một cửa hàng hoặc tổng đài mở 24/7 cần biết **mỗi giờ trong tuần cần bao nhiêu người**. Từ đó phải **xếp ca cho từng nhân viên** sao cho đủ người, chi phí thấp nhất, và **không vi phạm Bộ luật Lao động**. ShiftOpt làm việc đó tự động, rồi cho biết lịch sẽ thay đổi thế nào khi nhu cầu thay đổi.

### A2. Đầu vào và đầu ra

| Đầu vào | Ví dụ trong demo |
|---|---|
| Nhu cầu theo giờ: 168 con số, 7 ngày × 24 giờ | Lấy từ dữ liệu bán hàng FreshRetailNet, store 18 |
| Danh sách nhân viên | 30 người, lương 100/giờ, một người chỉ làm tối đa 24 giờ/tuần |
| Mẫu ca | 3 ca 8 giờ: Đêm 0h–8h, Ngày 8h–16h, Tối 16h–24h |
| Tham số luật | 48 giờ/tuần, tối đa 6 ngày liên tiếp |

| Đầu ra | Ý nghĩa |
|---|---|
| Lịch xếp ca | Ai làm ca nào, ngày nào |
| Biểu đồ phủ nhu cầu | Mỗi giờ có bao nhiêu người so với số cần |
| KPI | Tỷ lệ phủ, giờ thiếu, giờ thừa, chi phí lương, phụ cấp đêm, mức công bằng |
| Danh sách vi phạm | Phải bằng 0 với ràng buộc luật |
| Phân tích độ nhạy | Chi phí thay đổi ra sao khi nhu cầu tăng hoặc giảm |

### A3. Cách nó làm

1. **Quy đổi nhu cầu.** Dữ liệu bán hàng không phải số người. Công thức quy đổi: `số người = max(sàn, làm tròn lên(alpha × doanh số / p))`. Trong đó `alpha` và `p` là **giả định của nhóm**, luôn hiện trên màn hình.
2. **Tối ưu hóa.** Bài toán được viết thành mô hình **quy hoạch nguyên** và giải bằng **OR-Tools CP-SAT** (solver của Google). Biến `x[e, d, s] = 1` nghĩa là nhân viên `e` làm ca `s` vào ngày `d`.
3. **Thứ tự ưu tiên khi tối ưu (lexicographic).** Giải lần lượt theo bốn tầng:
   1. Ít giờ thiếu người nhất.
   2. Rồi chi phí lương thấp nhất.
   3. Rồi chia ca đêm công bằng nhất.
   4. Rồi tôn trọng ngày nghỉ mong muốn.

   Mỗi tầng không được làm hỏng kết quả tầng trước.
4. **Kiểm tra lại độc lập (validator).** Lịch solver trả về được một chương trình khác kiểm lại toàn bộ luật, không tin solver.
5. **Phân tích độ nhạy.** Giải lại nhiều lần với nhu cầu khác nhau để thấy chi phí thay đổi.

### A4. Ràng buộc pháp lý được cài (Bộ luật Lao động 2019)

| Điều | Nội dung | Cách cài |
|---|---|---|
| Đ.105 | Tối đa 8 giờ/ngày, 48 giờ/tuần | Ràng buộc cứng |
| Đ.106 | Giờ đêm là 22h–06h | Dùng để tính phụ cấp |
| Đ.98 | Làm đêm được trả thêm ít nhất 30% | Nằm trong chi phí ca |
| Đ.109 | Nghỉ giữa ca 30 phút (ca đêm 45 phút) | Mỗi ca mất một giờ phủ cho giờ nghỉ |
| Đ.110 | Nghỉ ít nhất 12 giờ giữa hai ca | Ràng buộc cứng |
| Đ.111 | Nghỉ ít nhất 24 giờ liên tục mỗi tuần | Ràng buộc cứng, tính trên trục giờ |

"Ràng buộc cứng" nghĩa là solver **không bao giờ** được vi phạm, kể cả khi thiếu người. Khi thiếu người, lịch vẫn được tạo nhưng báo rõ giờ nào thiếu.

Lưu ý khi trình bày: nội dung các điều luật chưa được đối chiếu với nguyên văn văn bản luật (xem `docs/đặc tả.md` mục 4).

### A5. Ba điểm khác biệt cần nhấn mạnh

1. **Solver đề xuất, validator phán xét.** Không tin trạng thái của solver; mọi lịch được kiểm lại.
2. **Độ nhạy tính bằng giải lại thật**, không dùng "giá bóng" (shadow price) giả của mô hình nguyên. Dual của bài toán nới lỏng (LP) chỉ hiển thị kèm nhãn "xấp xỉ".
3. **Giả định luôn hiện ra.** Dữ liệu FreshRetailNet là doanh số chuẩn hóa của kho thương mại điện tử, **không phải dữ liệu nhân sự**. `alpha` và `p` là giả định của nhóm.

### A6. Thuật ngữ sẽ xuất hiện trên màn hình

| Từ | Nghĩa |
|---|---|
| Coverage ratio | Phần trăm nhu cầu được phủ. 100% là không thiếu giờ nào |
| Understaffed hours | Tổng số giờ-người còn thiếu |
| OPTIMAL | Solver **chứng minh** được đây là lịch tốt nhất |
| FEASIBLE | Có lịch hợp lệ, nhưng **chưa chứng minh** là tốt nhất trong thời gian cho phép |
| Gap | Khoảng cách tối đa tới lịch tốt nhất. 0 nghĩa là đã tối ưu |
| Seed, workers | Tham số để chạy lại ra đúng kết quả cũ (tái lập) |
| λ (lambda) | Hệ số nhân nhu cầu: 1,2 nghĩa là nhu cầu tăng 20% |
| z(λ) | Chi phí tối ưu khi nhu cầu nhân với λ |
| Chi phí biên theo giờ | Chi phí tăng thêm khi một giờ cần thêm một người, tính bằng giải lại |

### A7. Kiến trúc (một slide)

- **Engine** (Python): mô hình, solver, validator, KPI, độ nhạy.
- **Backend** (FastAPI + MySQL): lưu dữ liệu, chạy giải trong tiến trình riêng, trả mã job để giao diện hỏi lại.
- **Frontend** (React): các màn hình.
- Chạy toàn bộ bằng Docker Compose.

---

## B. Chuẩn bị trước buổi

Làm trước ít nhất một ngày, rồi **chạy thử toàn bộ phần C một lần**. Mọi lệnh chạy trong PowerShell.

### B0. Dữ liệu FreshRetailNet (chỉ làm một lần trên mỗi máy)

Backend đọc file `data/processed/demand_store_18.parquet` qua volume khai báo trong `docker-compose.yml`. File này không nằm trong git. Kiểm tra:

```powershell
cd D:\projects\ShiftOpt
Test-Path data\processed\demand_store_18.parquet
```

Nếu in `False`, tải và xử lý dữ liệu (tải khoảng vài trăm MB):

```powershell
cd D:\projects\ShiftOpt\backend
uv run --locked python -m scripts.download_freshretailnet
uv run --locked python -m scripts.build_demand_store --store-id 18
```

### B1. Bật hệ thống

```powershell
cd D:\projects\ShiftOpt
docker compose up -d --build
docker compose ps -a
```

Đợi `backend` có `healthy` và `seed` có `Exited (0)`.

Service `seed` tự nạp dữ liệu demo qua API (`backend/scripts/seed_demo.py`):

- 30 nhân viên `E01`–`E30`, lương 100/giờ. `E07` chỉ làm tối đa 24 giờ/tuần.
- 3 mẫu ca 8 giờ: Đêm 00:00, Ngày 08:00, Tối 16:00.
- Hồ sơ nhu cầu `Store 18 demo` (FreshRetailNet store 18, `alpha = 1`, `p = 4`, sàn ngày 1, sàn đêm 1). Hồ sơ này cần file ở B0. Nếu thiếu file, log của `seed` ghi `demand profiles: not created` và các dữ liệu khác vẫn được nạp.

Mỗi phần chỉ được nạp khi bảng tương ứng đang trống. Chạy `docker compose up` nhiều lần không tạo trùng và không ghi đè dữ liệu người dùng đã nhập. Kiểm tra lại log:

```powershell
docker compose logs seed
```

Không chạy `smoke_flow` trên stack demo: nó tự thêm 25 nhân viên và nhiều mẫu ca kiểm thử. Nút **Tối ưu** dùng **tất cả** nhân viên, nên DB demo phải giữ đúng 30 người.

### B2. Nếu cần nạp lại dữ liệu bằng tay

Chỉ dùng khi đã xóa dữ liệu demo trên web và muốn nạp lại phần đã xóa:

```powershell
docker compose run --rm seed
```

### B3. Tạo thêm dữ liệu trên web (tùy chọn)

Có thể tạo mẫu ca hoặc hồ sơ nhu cầu trước lớp để minh họa cách nhập. Với hồ sơ FreshRetailNet:

1. Mở `http://localhost:3000/demand`, bấm **Tạo hồ sơ nhu cầu**.
2. Trong cửa sổ, bấm ô chọn nguồn **FreshRetailNet**.
3. Điền **Tên hồ sơ**, **Mã store** = `18`.
4. Khung **Giả định của nhóm (không phải dữ liệu)**: **alpha (giải chuẩn hóa)** = `1`, **p (đơn vị mỗi người-giờ)** = `4`, **Sàn ban ngày (số người tối thiểu)** = `1`, **Sàn ban đêm (22:00-06:00)** = `1`. Nếu để `p = 1`, giờ cao điểm cần 29 người và 30 nhân viên không đủ.
5. Bấm **Tạo từ dữ liệu**. Hồ sơ mới ghi **cao điểm 8 người**.

Hiện chỉ store 18 đã được xử lý sẵn. Nhập store khác sẽ nhận lỗi `no processed demand for store X; build it first`.

### B4. Dữ liệu cũ

Volume DB của Compose tên là `mysql_data`. Hai volume cũ `shiftopt_db_data` (dữ liệu kiểm thử, 200 nhân viên) và `shiftopt-demo_db_data` (stack demo cũ) vẫn còn trên máy nhưng không còn được dùng. Không cần xóa chúng.

### B5. Chạy thử tổng duyệt

Làm hết phần C một lần. Mỗi lần chạy thử tạo thêm lượt giải và phân tích; điều này không ảnh hưởng buổi demo.

### B6. Chuẩn bị máy chiếu

- Mở sẵn trình duyệt ở `http://localhost:3000`, zoom 100%.
- Mở sẵn file này và `docs/benchmarks.md` để tra số liệu.
- Mở sẵn thư mục `docs/acceptance/` (ảnh dự phòng).

---

## C. Kịch bản từng bước

Thời gian trong phần này đo bằng trình duyệt tự động (Playwright) ngày 2026-11-06 trên DB sạch, với 30 nhân viên và hồ sơ store 18. Máy khác có thể chậm hơn.

### C0. Phiếu thao tác (in ra, để cạnh máy)

| # | Trang | Thao tác | Thấy gì |
|---|---|---|---|
| 1 | Trang chủ | Mở `localhost:3000`, cuộn qua các mục | Menu Nhu cầu, Nhân viên, Mẫu ca, Xếp lịch, Độ nhạy |
| 2 | Nhu cầu | Bấm **Nhu cầu** → chọn `Store 18 demo` | Lưới 7 × 24, cao điểm 8 người, nhãn giả định |
| 3 | Nhân viên, Mẫu ca | Bấm **Nhân viên**, chỉ E07 → bấm **Mẫu ca** | E07 tối đa 24 giờ; 3 ca 8 giờ |
| 4 | Xếp lịch | Chọn hồ sơ → mở **Thiết lập solver và luật lao động** → **Số worker của solver** = 1 → bấm **Tối ưu** | Tự chuyển sang trang lượt mới, khoảng 7 giây |
| 5 | Kết quả | Cuộn: trạng thái, lịch, biểu đồ phủ, chi phí | `OPTIMAL`, tỷ lệ phủ 100,0% |
| 6 | Kết quả | Chỉ khung **Tuân thủ** | **0 vi phạm cứng** |
| 7 | Kết quả | **Sửa lịch bằng tay** → tạo cặp ca Tối rồi Ngày cho một người → **Lưu thành lượt mới và kiểm tra lại** | 1 vi phạm Điều 110 |
| 7b | Kết quả | **Tất cả lượt** → mở lượt gốc | Vẫn 0 vi phạm |
| 8 | Độ nhạy | **Chạy quét nhu cầu** → kéo **Hệ số nhu cầu lambda** | Đường z(λ), khoảng 13 giây |
| 9 | Độ nhạy | Chọn `alpha`, nhập `0.8, 1.0, 1.2` → **Chạy quét giả định** | Bảng 3 dòng, khoảng 20 giây |
| 10 | Độ nhạy | Lương = `100` → **Tính chi phí biên theo giờ** | Bản đồ nhiệt, khoảng 5 giây |
| 11 | Kết quả lượt gốc | Bấm **CSV độ phủ** hoặc **CSV KPI** | Tải file CSV |
| 12 | — | Kết luận | — |

Chi tiết từng bước ở dưới. Mỗi bước gồm: **Làm** (thao tác), **Nói** (gợi ý lời trình bày), **Ý nghĩa** (vì sao bước này quan trọng), **Mong đợi** (điều sẽ thấy).

### Bước 1. Giới thiệu (2 phút): trang chủ

- **Làm:** mở `http://localhost:3000`. Cuộn chậm qua các mục Sản phẩm, Tính năng, Cách hoạt động, Phân tích, Luật lao động.
- **Nói:** "Bài toán của nhóm là xếp ca nhân viên cho dịch vụ có nhu cầu thay đổi theo giờ, như cửa hàng 24/7 hoặc tổng đài. Hệ thống nhận nhu cầu theo giờ, danh sách nhân viên, mẫu ca và luật lao động; trả về lịch xếp ca, các chỉ số và cảnh báo vi phạm luật, rồi phân tích chi phí khi nhu cầu thay đổi."
- **Ý nghĩa:** người nghe nắm được đầu vào, đầu ra trước khi xem chi tiết.
- **Mong đợi:** thanh menu có Nhu cầu, Nhân viên, Mẫu ca, Xếp lịch, Độ nhạy. Số liệu trên trang chủ là số minh họa, không phải kết quả thật.

### Bước 2. Nhu cầu (2 phút)

- **Làm:** bấm **Nhu cầu** trên menu, chọn hồ sơ `Store 18 demo` trong danh sách.
- **Nói:** "Nhu cầu lấy từ bộ dữ liệu công khai FreshRetailNet-50K. Đây là doanh số bán hàng theo giờ của một kho thương mại điện tử, **không phải** dữ liệu nhân sự. Để đổi doanh số thành số người, nhóm dùng công thức với hai giả định là alpha và p. Ở đây p = 4 nghĩa là giả định một người xử lý được 4 đơn vị doanh số mỗi giờ. Giờ đêm không suy từ doanh số mà dùng mức tối thiểu cố định là 1 người."
- **Ý nghĩa:** cho thấy giả định không bị giấu. Nếu có người hỏi "số 4 ở đâu ra", trả lời rằng đó là giả định, và bước 9 cho thấy chi phí đổi thế nào khi giả định đổi.
- **Mong đợi:** lưới 7 × 24 số người cần mỗi giờ, cao điểm 8 người, nhãn "Doanh số chuẩn hóa, không phải nhu cầu nhân sự". Lưới chỉ đọc vì suy ra từ dữ liệu.

### Bước 3. Nhân viên và mẫu ca (1 phút)

- **Làm:** bấm **Nhân viên**, chỉ vào dòng `E07`. Sau đó bấm **Mẫu ca**.
- **Nói:** "Có 30 nhân viên. Riêng E07 chỉ làm tối đa 24 giờ một tuần, ví dụ một người làm bán thời gian; những người khác theo mức luật 48 giờ. Có 3 ca 8 tiếng phủ đủ 24 giờ. Ca Đêm nằm trong khung đêm 22h–6h nên có phụ cấp đêm."
- **Ý nghĩa:** đây là các ràng buộc mà solver phải tôn trọng.
- **Mong đợi:** 30 dòng nhân viên; cột **Giờ tối đa/tuần** của E07 là 24. Có 3 mẫu ca, có cột giờ đêm.

### Bước 4. Tối ưu hóa (2 phút)

- **Làm:**
  1. Bấm **Xếp lịch**. Làm việc trong khung **Tối ưu mới**.
  2. **Hồ sơ nhu cầu**: chọn `Store 18 demo`.
  3. Kiểm tra dòng **Nhân viên** ghi "Tất cả 30 nhân viên". Nếu khác 30, xem mục E.
  4. Kiểm tra **Các mẫu ca solver được dùng**: cả Đêm, Ngày, Tối đều được tick.
  5. Bấm **Thiết lập solver và luật lao động** để mở phần thiết lập. Đổi **Số worker của solver** thành **1** (mặc định là 8). Kiểm tra các ô còn lại:
     - **Giới hạn thời gian (giây)**: 60
     - **Ngưỡng gap**: 0.01
     - **Seed ngẫu nhiên**: 0
     - **Giờ tối đa mỗi tuần**: 48
     - **Số ngày làm liên tiếp tối đa**: 6
  6. Bấm **Tối ưu**.
- **Nói (trong lúc chờ):** "Bấm Tối ưu không chặn giao diện. Hệ thống tạo một job, chạy solver trong tiến trình riêng, và trang tự hỏi lại trạng thái. Đặt 1 worker và seed 0 thì chạy lại bao nhiêu lần cũng ra cùng kết quả; đây là yêu cầu tái lập. Solver giải bốn tầng: ít thiếu người nhất, rồi rẻ nhất, rồi công bằng ca đêm, rồi tôn trọng mong muốn nghỉ."
- **Ý nghĩa:** đây là chức năng chính của dự án.
- **Mong đợi:** trang tự chuyển sang trang của lượt mới. Lần đo ngày 2026-11-06 mất 6,5 giây từ lúc bấm tới khi hiện `OPTIMAL`.

### Bước 5. Đọc kết quả (3 phút)

- **Làm:** cuộn từ trên xuống, chỉ vào từng khung.
- **Nói và chỉ vào:**
  - **Trạng thái solver:** "Kết quả là OPTIMAL, gap 0: solver đã **chứng minh** không có lịch nào tốt hơn theo thứ tự ưu tiên. Nếu là FEASIBLE thì hệ thống ghi rõ và kèm gap, không gọi là tối ưu."
  - **Lưới lịch:** "Mỗi hàng là một nhân viên, mỗi cột là một ngày, ô màu là ca được giao."
  - **Biểu đồ phủ:** "Cột là số người có mặt, vạch nét đứt là số người cần. Nếu thiếu người, phần thiếu được tô sọc chéo; ở đây không thiếu giờ nào."
  - **Chi tiết lượt giải:** tỷ lệ phủ, giờ thiếu, giờ thừa, hiệu suất, độ lệch số ca đêm giữa các nhân viên.
  - **Chi phí lao động:** tổng lương và phụ cấp đêm. Nhập một số vào ô **Doanh thu tuần giả định (giả định của nhóm)** để ra tỷ lệ chi phí lao động. Nói: "Doanh thu là giả định, nên tỷ lệ này chỉ để minh họa."
- **Ý nghĩa:** chứng minh hệ thống trả đủ các đầu ra đã hứa.
- **Mong đợi:** `OPTIMAL`, tỷ lệ phủ 100,0%, 0 giờ thiếu. E07 có tối đa 3 ca (24 giờ).

### Bước 6. Kiểm tra luật (1 phút)

- **Làm:** chỉ vào khung **Tuân thủ** trên cùng trang.
- **Nói:** "Lịch này vừa được một chương trình kiểm tra độc lập rà lại toàn bộ luật: giờ mỗi ngày, mỗi tuần, nghỉ 12 giờ giữa ca, nghỉ 24 giờ liên tục mỗi tuần, số ngày làm liên tiếp. Chương trình này không dùng chung mã với solver, nên nếu mô hình có lỗi thì nó vẫn bắt được."
- **Ý nghĩa:** điểm khác biệt số 1: không tin solver.
- **Mong đợi:** **0 vi phạm cứng**.

### Bước 7. Cố ý sửa sai để thấy cảnh báo (3 phút)

- **Làm:**
  1. Trong khung **Tuân thủ**, bấm **Sửa lịch bằng tay**. Cửa sổ hiện bảng mọi ca đã xếp; mỗi dòng có 4 ô chọn: Nhân viên, Ngày, Ca, Bắt đầu nghỉ.
  2. Tìm một dòng có ca **Tối** vào một ngày từ Thứ Hai tới Thứ Bảy. Ghi nhớ nhân viên đó, gọi là X, và ngày đó.
  3. Tìm dòng của X vào ngày kế tiếp:
     - Nếu có: đổi ô **Ca** của dòng đó thành **Ngày**.
     - Nếu không có: bấm **Thêm ca** (dòng mới ở cuối bảng), chọn Nhân viên = X, Ngày = ngày kế tiếp, Ca = **Ngày**.
  4. Ở dòng vừa đổi hoặc thêm, chọn **Bắt đầu nghỉ** là một giờ bất kỳ. **Không để "Không nghỉ"**; nếu để, sẽ có thêm lỗi thiếu giờ nghỉ (Đ.109) làm rối phần trình bày.
  5. Bấm **Lưu thành lượt mới và kiểm tra lại**.
- **Nói:** "Giả sử quản lý tự sửa lịch: cho X làm ca tối, kết thúc lúc 24h, rồi ca ngày hôm sau bắt đầu lúc 8h. X chỉ được nghỉ 8 giờ, ít hơn 12 giờ theo Điều 110. Hệ thống không ghi đè lịch cũ: bản sửa là một lượt mới và được kiểm lại ngay."
- **Ý nghĩa:** chứng minh validator bắt được vi phạm do người sửa tay, và lịch gốc không bị phá.
- **Mong đợi:**
  - Trang chuyển sang lượt mới, tiêu đề ghi "Lượt …, sửa từ lượt …".
  - Khung **Tuân thủ** báo đúng 1 vi phạm, nhóm **Điều 110 · nghỉ giữa hai ca dưới 12 giờ**.
  - Lượt mới bị đánh dấu thất bại vì có vi phạm cứng. Khung báo thất bại có một câu tiếng Anh từ backend ("validator found 1 hard-constraint violations"). Cột chi tiết của vi phạm cũng là tiếng Anh. Nói trước: "Thông báo kỹ thuật từ backend giữ tiếng Anh."
- **Làm tiếp:** bấm **Tất cả lượt**, mở lại lượt gốc: vẫn **0 vi phạm cứng**.

### Bước 8. Độ nhạy theo nhu cầu (3 phút)

- **Làm:**
  1. Bấm **Độ nhạy**. Trong khung **Thiết lập phân tích**, kiểm tra hồ sơ là `Store 18 demo` và cả 3 ca đều được tick. Form mặc định đặt time limit 20 giây và 1 worker cho phân tích.
  2. Bấm **Chạy quét nhu cầu**.
  3. Khi đường cong hiện ra, kéo thanh **Hệ số nhu cầu lambda** qua lại.
- **Nói (trong lúc chờ):** "Câu hỏi quản lý hay hỏi: nếu nhu cầu tăng 20% thì tốn thêm bao nhiêu? Hệ thống giải lại toàn bộ lịch với nhu cầu nhân 0,8; 0,9; 1,0; 1,1; 1,2; 1,3. Mỗi điểm là một lần giải thật, không phải ước lượng."
- **Ý nghĩa:** đây là phần "phân tích độ nhạy khi nhu cầu thay đổi" trong đề bài.
- **Mong đợi:** sau khoảng 13 giây:
  - Khung **Đường chi phí z(lambda)**: chi phí không giảm khi λ tăng.
  - Khi kéo thanh trượt, số liệu và cột theo giờ đổi theo.
  - Lần đo ngày 2026-11-06 cả 6 điểm đều đã chứng minh tối ưu. Nếu có điểm chưa chứng minh, điểm đó vẽ bằng vòng tròn rỗng và ghi "chưa chứng minh tối ưu".

### Bước 9. Độ nhạy theo giả định (2 phút)

- **Làm:** vẫn ở trang **Độ nhạy**:
  1. **Giả định quy đổi cần thay đổi**: chọn `alpha`.
  2. **Các giá trị thử**: nhập `0.8, 1.0, 1.2`.
  3. Bấm **Chạy quét giả định**.
- **Nói:** "Số người cần phụ thuộc vào giả định của nhóm. Hệ thống tính lại nhu cầu từ dữ liệu gốc với từng giá trị alpha rồi giải lại. Bảng luôn ghi rõ đây là giả định của nhóm, không phải dữ liệu nhân sự."
- **Ý nghĩa:** trả lời trước câu hỏi "giả định của nhóm có đáng tin không" bằng cách cho thấy kết luận thay đổi bao nhiêu khi giả định thay đổi.
- **Mong đợi:** sau khoảng 20 giây, khung **Quét giả định quy đổi** có bảng 3 dòng. Lần đo ngày 2026-11-06:

  | alpha | Chi phí tuần | Kết quả solver |
  |---|---|---|
  | 0,8 | 71.660 | tối ưu (đã chứng minh) |
  | 1,0 | 88.920 | tối ưu (đã chứng minh) |
  | 1,2 | 104.880 | tối ưu (đã chứng minh) |

  Nói: "alpha tăng 20% thì chi phí tăng khoảng 18%." Cột Giá trị hiện `1` thay cho `1,0`; đây là cách hiển thị, không phải lỗi số liệu.

### Bước 10 (tùy chọn). Chi phí biên theo giờ

- **Làm:** nhập ô **Lương theo giờ cho mô hình chi phí biên (giả định của nhóm)** = `100`, bấm **Tính chi phí biên theo giờ**.
- **Nói:** "Với từng giờ trong tuần, hệ thống thêm yêu cầu một người ở giờ đó rồi giải lại, tức 169 lần giải trên mô hình tổng hợp. Chênh lệch chi phí là chi phí biên thật của giờ đó. Bản đồ nhiệt cho thấy giờ nào đắt nhất nếu cần thêm người. Dual của bài toán nới lỏng chỉ hiện kèm nhãn xấp xỉ."
- **Mong đợi:** sau khoảng 5 giây, bản đồ nhiệt 7 × 24 trong khung **Chi phí biên theo giờ**.

### Bước 11. Xuất dữ liệu (30 giây)

- **Làm:** bấm **Xếp lịch** → **Tất cả lượt** → mở lượt gốc (lượt có `OPTIMAL`). Bấm **CSV độ phủ** hoặc **CSV KPI**.
- **Nói:** "Lịch và chỉ số xuất được ra CSV để dùng ở nơi khác."
- **Mong đợi:** trình duyệt tải về file CSV. Ngoài hai file trên còn có **CSV lịch**.

### Bước 12. Kết luận (2 phút)

- **Nói:**
  - "Dự án mô hình hóa bài toán xếp ca bằng quy hoạch nguyên, giải bằng OR-Tools CP-SAT, có đủ ràng buộc luật lao động."
  - "Kết quả đo được: với 20–40 nhân viên, mọi lần giải đều tối ưu trong dưới 32 giây, 0 vi phạm. Trên dữ liệu store 18 với 30 nhân viên: tối ưu, phủ 100%."
  - "Giới hạn: khi chỉ có 8 nhân viên, solver không chứng minh được tối ưu trong 60 giây (phủ 70%). Đó là lý do hệ thống luôn ghi FEASIBLE kèm gap thay vì tự nhận là tối ưu."
  - "Giả định alpha, p và nội dung điều luật cần được nhóm xác nhận thêm; số liệu chỉ áp dụng cho các trường hợp đã đo."
- **Ý nghĩa:** trình bày trung thực phạm vi của kết quả.

---

## D. Câu hỏi hay gặp

| Câu hỏi | Trả lời ngắn |
|---|---|
| Tại sao dùng OR-Tools CP-SAT mà không dùng PuLP? | CP-SAT mạnh với biến 0/1 và ràng buộc chuỗi ngày, nghỉ giữa ca. PuLP + HiGHS được dùng cho mô hình tổng hợp và để lấy dual LP. Hai solver được so sánh trên cùng mô hình tổng hợp (`docs/benchmarks.md` mục 2). |
| Sao không dùng trọng số phạt cho giờ thiếu? | Chọn trọng số lớn tùy tiện dễ sai. Giải theo tầng bảo đảm thiếu người luôn ưu tiên hơn chi phí. |
| Nếu không đủ người thì sao? | Lịch vẫn được tạo, giờ thiếu hiện trên biểu đồ. Luật vẫn không bị vi phạm. |
| Kết quả có đúng không? | Mô hình được kiểm trên benchmark công khai Curtois & Qu: 3/5 instance đạt và chứng minh được đúng tối ưu đã công bố (8 worker, 120 giây). Mọi lịch đều qua validator độc lập. |
| Dữ liệu có phải nhu cầu nhân sự thật không? | Không. Đó là doanh số chuẩn hóa của kho thương mại điện tử. Số người suy ra từ giả định của nhóm. |
| Shadow price của mô hình là gì? | Mô hình nguyên không có shadow price hợp lệ. Chi phí biên được tính bằng giải lại; dual LP chỉ là xấp xỉ và luôn có nhãn. |
| Chạy lại có ra kết quả khác không? | Với 1 worker và cùng seed thì ra cùng kết quả; có test tự động kiểm tra điều này. |

---

## E. Sự cố và dự phòng

| Sự cố | Cách xử lý |
|---|---|
| Trang không mở được | Chạy `docker compose ps -a`. Nếu container dừng, chạy `docker compose up -d` và đợi `healthy` |
| Báo cổng 3000 hoặc 8000 đang bận | Stack cũ `shiftopt-demo` còn chạy. Chạy `docker compose -p shiftopt-demo stop` rồi `docker compose up -d` |
| Tạo hồ sơ FreshRetailNet báo lỗi không có dữ liệu | Thiếu file `data/processed/demand_store_18.parquet` (mục B0) |
| Dòng Nhân viên không ghi "Tất cả 30 nhân viên" | DB đã có thêm nhân viên (ví dụ do chạy `smoke_flow`). Xóa các nhân viên thừa trên trang **Nhân viên**, hoặc dùng ảnh dự phòng |
| Tối ưu chạy quá lâu | Kiểm tra **Số worker của solver** và số nhân viên. Đợi hết time limit; kết quả sẽ là FEASIBLE kèm gap. Dùng nó để giải thích nguyên tắc "không tự nhận tối ưu" |
| Phân tích Độ nhạy chậm | Nói trong lúc chờ (bước 8); nếu quá lâu, chuyển sang bước 11 rồi quay lại |
| Mọi thứ hỏng | Mở ảnh trong `docs/acceptance/`: `schedule_run.png` (kết quả lịch) và các ảnh trang Nhu cầu, Nhân viên, Mẫu ca, Độ nhạy (chụp trước khi Việt hóa giao diện) |

---

## F. Phần chưa kiểm

- Phần C đã chạy hết bằng trình duyệt tự động (Playwright) ngày 2026-11-06, trên DB sạch: mọi bước đạt, không có lỗi JavaScript. Chưa có người bấm tay theo đúng thứ tự này.
- Thời gian ở phần C đo trên một máy; máy chiếu hoặc laptop khác có thể chậm hơn.
- Ảnh trong `docs/acceptance/` chụp trước khi Việt hóa giao diện.
- Nội dung điều luật chưa đối chiếu nguyên văn (`docs/đặc tả.md` mục 4).
