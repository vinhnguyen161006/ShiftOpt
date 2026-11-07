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

Làm trước ít nhất một ngày, rồi **chạy thử toàn bộ phần C một lần**.

### B1. Dữ liệu phải sạch

Nút **Tối ưu** luôn dùng **tất cả** nhân viên có trong hệ thống. DB hiện tại có 200 nhân viên và nhiều mẫu ca thừa từ các lần kiểm thử. Với 200 nhân viên, lần giải sẽ chậm và không ra `OPTIMAL`.

Cách làm sạch là xóa dữ liệu DB của Docker. **Lệnh này xóa toàn bộ dữ liệu trong DB và không hoàn tác được**; chỉ chạy khi không cần giữ dữ liệu cũ:

```
cd D:\projects\ShiftOpt
docker compose down -v
docker compose up -d --build
```

Đợi backend sẵn sàng:

```
docker inspect -f "{{.State.Health.Status}}" shiftopt-backend-1
```

Kết quả phải là `healthy`. Không chạy `smoke_flow` sau bước này: nó tự thêm 25 nhân viên và nhiều mẫu ca.

### B2. Tạo 30 nhân viên

Chạy trong PowerShell (nhanh hơn nhập tay 30 lần). Nhân viên `E07` chỉ được làm tối đa 24 giờ/tuần:

```powershell
1..30 | ForEach-Object {
  $body = @{ code = ("E{0:D2}" -f $_); name = "Employee $_"; hourly_wage = 100; unavailable_days = @(); preferred_days_off = @() }
  if ($_ -eq 7) { $body.max_weekly_hours = 24 }
  Invoke-RestMethod -Method Post -Uri http://localhost:8000/api/employees -ContentType 'application/json' -Body ($body | ConvertTo-Json)
}
(Invoke-RestMethod http://localhost:8000/api/employees).Count
```

Dòng cuối phải in `30`.

### B3. Tạo 3 mẫu ca (trên giao diện)

Mở `http://localhost:3000/shift-templates`, bấm **Thêm mẫu ca** ba lần:

| Tên | Bắt đầu lúc | Độ dài (giờ) |
|---|---|---|
| Đêm | 0 | 8 |
| Ngày | 8 | 8 |
| Tối | 16 | 8 |

### B4. Tạo profile nhu cầu (trên giao diện)

Mở `http://localhost:3000/demand`, ở phần tạo profile mới:

1. **Nguồn**: chọn **FreshRetailNet**.
2. **Tên hồ sơ**: `Store 18 demo`.
3. **Mã store**: `18`.
4. Khung **Giả định của nhóm (không phải dữ liệu)**:
   - **alpha (giải chuẩn hóa)**: `1`
   - **p (đơn vị mỗi người-giờ)**: `4` (**bắt buộc đổi**; nếu để 1, giờ cao điểm cần 29 người và 30 nhân viên không đủ)
   - **Sàn ban ngày (số người tối thiểu)**: `1`
   - **Sàn ban đêm (22:00-06:00)**: `1`
5. Bấm **Tạo từ dữ liệu**.

### B5. Chuẩn bị máy chiếu

- Mở sẵn trình duyệt ở `http://localhost:3000`, zoom 100%.
- Mở sẵn file này và `docs/benchmarks.md` để tra số liệu.
- Mở sẵn thư mục `docs/acceptance/` (ảnh dự phòng).

---

## C. Kịch bản từng bước

Mỗi bước gồm: **Làm** (thao tác), **Nói** (gợi ý lời trình bày), **Ý nghĩa** (vì sao bước này quan trọng), **Mong đợi** (điều sẽ thấy).

### Bước 1. Giới thiệu (2 phút): trang chủ

- **Làm:** mở `http://localhost:3000`.
- **Nói:** "Bài toán của nhóm là xếp ca nhân viên cho dịch vụ có nhu cầu thay đổi theo giờ, như cửa hàng 24/7 hoặc tổng đài. Hệ thống nhận nhu cầu theo giờ, danh sách nhân viên, mẫu ca và luật lao động; trả về lịch xếp ca, các chỉ số và cảnh báo vi phạm luật, rồi phân tích chi phí khi nhu cầu thay đổi."
- **Ý nghĩa:** người nghe nắm được đầu vào, đầu ra trước khi xem chi tiết.
- **Mong đợi:** trang chủ có thanh menu Nhu cầu, Nhân viên, Mẫu ca, Xếp lịch, Độ nhạy. Trang chủ có các mục Sản phẩm, Tính năng, Cách hoạt động, Phân tích, Luật lao động; có thể cuộn qua để giới thiệu nhanh.

### Bước 2. Nhu cầu (2 phút): trang Demand

- **Làm:** bấm **Nhu cầu**, mở profile `Store 18 demo`.
- **Nói:** "Nhu cầu lấy từ bộ dữ liệu công khai FreshRetailNet-50K. Đây là doanh số bán hàng theo giờ của một kho thương mại điện tử, **không phải** dữ liệu nhân sự. Để đổi doanh số thành số người, nhóm dùng công thức với hai giả định: alpha và p. Ở đây p = 4 nghĩa là giả định một người xử lý được 4 đơn vị doanh số mỗi giờ. Giờ đêm không suy từ doanh số mà dùng mức tối thiểu cố định 1 người."
- **Ý nghĩa:** cho thấy giả định không bị giấu. Nếu ai hỏi "số 4 ở đâu ra", câu trả lời là đó là giả định, và bước 9 sẽ cho thấy chi phí đổi thế nào khi giả định đổi.
- **Mong đợi:** lưới 7 × 24 số người cần mỗi giờ; giờ cao điểm cần 8 người; nhãn cảnh báo "Doanh số chuẩn hóa, không phải nhu cầu nhân sự".

### Bước 3. Nhân viên và mẫu ca (1 phút)

- **Làm:** bấm **Nhân viên**, chỉ dòng `E07`. Sau đó bấm **Mẫu ca**.
- **Nói:** "Có 30 nhân viên. Riêng E07 chỉ làm tối đa 24 giờ một tuần, ví dụ một người làm bán thời gian; những người khác theo mức luật 48 giờ. Có 3 ca 8 tiếng phủ đủ 24 giờ. Ca Đêm nằm trong khung đêm 22h–6h nên có phụ cấp đêm."
- **Ý nghĩa:** đây là các ràng buộc mà solver phải tôn trọng.
- **Mong đợi:** 30 dòng nhân viên; cột **Giờ tối đa/tuần** của E07 là 24, những người khác ghi giới hạn luật. 3 mẫu ca, có cột giờ đêm.

### Bước 4. Tối ưu hóa (3 phút): trang Schedule

- **Làm:**
  1. Bấm **Xếp lịch**. Ở khung **Tối ưu mới**:
  2. **Hồ sơ nhu cầu**: chọn `Store 18 demo`.
  3. Dòng **Nhân viên** ghi "Tất cả 30 nhân viên": kiểm tra đúng 30.
  4. **Các mẫu ca solver được dùng**: tick cả Đêm, Ngày, Tối.
  5. Mở **Thiết lập solver và luật lao động**, đặt:
     - **Giới hạn thời gian (giây)**: 60
     - **Ngưỡng gap**: 0.01
     - **Số worker của solver**: **1** (mặc định là 8, phải đổi)
     - **Seed ngẫu nhiên**: 0
     - **Giờ tối đa mỗi tuần**: 48
     - **Số ngày làm liên tiếp tối đa**: 6
  6. Bấm **Tối ưu**.
- **Nói (trong lúc chờ):** "Bấm Optimize không chặn giao diện: hệ thống tạo một job, chạy solver trong tiến trình riêng, và trang tự hỏi lại trạng thái. Đặt 1 worker và seed 0 để chạy lại bao nhiêu lần cũng ra cùng kết quả; đây là yêu cầu tái lập. Solver giải bốn tầng: ít thiếu người nhất, rồi rẻ nhất, rồi công bằng ca đêm, rồi tôn trọng mong muốn nghỉ."
- **Ý nghĩa:** đây là chức năng chính của dự án.
- **Mong đợi:** trang tự chuyển sang trang kết quả của lượt giải. Trên máy đã đo, cấu hình này mất khoảng 12–20 giây.

### Bước 5. Đọc kết quả (3 phút): trang Kết quả xếp lịch

- **Làm:** cuộn từ trên xuống.
- **Nói và chỉ vào:**
  - **Trạng thái solver:** "Kết quả là OPTIMAL, gap 0: solver đã **chứng minh** không có lịch nào tốt hơn theo thứ tự ưu tiên. Nếu là FEASIBLE thì hệ thống ghi rõ và kèm gap, không gọi là tối ưu."
  - **Lưới lịch:** "Mỗi hàng là một nhân viên, mỗi cột là một ngày, ô màu là ca được giao."
  - **Biểu đồ phủ:** "Cột là số người có mặt, vạch nét đứt là số người cần. Nếu thiếu người, phần thiếu được tô sọc chéo; ở đây không thiếu giờ nào."
  - **Chi tiết lượt giải:** coverage, giờ thiếu, giờ thừa, hiệu suất, độ lệch số ca đêm giữa các nhân viên.
  - **Chi phí lao động:** tổng lương và phụ cấp đêm. Nhập một số vào ô **Doanh thu tuần giả định (giả định của nhóm)** để ra tỷ lệ chi phí lao động: "Doanh thu là giả định, nên tỷ lệ này cũng chỉ là minh họa."
- **Ý nghĩa:** chứng minh hệ thống trả đủ các đầu ra đã hứa.
- **Mong đợi:** OPTIMAL, coverage 100%, 0 giờ thiếu. E07 có tối đa 3 ca (24 giờ).

### Bước 6. Kiểm tra luật (1 phút): khung Compliance

- **Làm:** chỉ vào khung **Tuân thủ** trên cùng trang.
- **Nói:** "Lịch này vừa được một chương trình kiểm tra độc lập rà lại toàn bộ luật: giờ mỗi ngày, mỗi tuần, nghỉ 12 giờ giữa ca, nghỉ 24 giờ liên tục mỗi tuần, số ngày làm liên tiếp. Chương trình này không dùng chung mã với solver, nên nếu mô hình có lỗi thì nó vẫn bắt được."
- **Ý nghĩa:** điểm khác biệt số 1: không tin solver.
- **Mong đợi:** 0 vi phạm.

### Bước 7. Cố ý sửa sai để thấy cảnh báo (3 phút)

- **Làm:**
  1. Trong khung **Tuân thủ**, bấm **Sửa lịch bằng tay**. Một cửa sổ hiện bảng mọi ca đã xếp, mỗi dòng gồm Nhân viên, Ngày, Ca, Bắt đầu nghỉ.
  2. Tìm một dòng có ca **Tối** (ví dụ nhân viên X, ngày T2). Ghi nhớ X.
  3. Tìm dòng của X vào ngày tiếp theo (T3):
     - Nếu có: đổi **Ca** của dòng đó thành **Ngày**.
     - Nếu không có: bấm **Thêm ca**, chọn Nhân viên = X, Ngày = T3, Ca = Ngày.
  4. Ở dòng vừa đổi hoặc thêm, chọn **Bắt đầu nghỉ** là một giờ, ví dụ 11:00. **Không để "Không nghỉ"**, nếu không sẽ có thêm lỗi thiếu giờ nghỉ (Đ.109) che mất lỗi cần trình bày.
  5. Bấm **Lưu thành lượt mới và kiểm tra lại**.
- **Nói:** "Giả sử quản lý tự sửa lịch: cho X làm ca tối thứ Hai, kết thúc 24h, rồi ca ngày thứ Ba bắt đầu 8h. X chỉ được nghỉ 8 giờ, ít hơn 12 giờ theo Điều 110. Hệ thống không ghi đè lịch cũ: bản sửa là một lượt mới và được kiểm lại ngay."
- **Ý nghĩa:** chứng minh validator bắt được vi phạm do người sửa tay, và lịch gốc không bị phá.
- **Mong đợi:** trang chuyển sang lượt mới, tiêu đề ghi "sửa từ lượt …". Khung Compliance báo vi phạm **nghỉ giữa hai ca dưới 12 giờ** cho X, kèm căn cứ Điều 110. Lượt mới được đánh dấu thất bại vì có vi phạm cứng.
- **Làm tiếp:** bấm **Tất cả lượt**, mở lại lượt gốc: vẫn 0 vi phạm.

### Bước 8. Độ nhạy theo nhu cầu (3 phút): trang What-if

- **Làm:**
  1. Bấm **Độ nhạy**. Trong khung **Thiết lập phân tích** chọn `Store 18 demo`, tick 3 ca. Form mặc định đã đặt time limit 20 giây và 1 worker cho phân tích.
  2. Bấm **Chạy quét nhu cầu**.
- **Nói (trong lúc chờ):** "Câu hỏi quản lý hay hỏi: nếu nhu cầu tăng 20% thì tốn thêm bao nhiêu? Hệ thống giải lại toàn bộ lịch với nhu cầu nhân 0,8; 0,9; 1,0; 1,1; 1,2; 1,3. Mỗi điểm là một lần giải thật, không phải ước lượng."
- **Ý nghĩa:** đây là phần "phân tích độ nhạy khi nhu cầu thay đổi" trong đề bài.
- **Mong đợi** (thời gian chạy qua giao diện chưa đo; mỗi điểm tối đa 20 giây):
  - Đường cong **z(λ)**: chi phí không giảm khi λ tăng.
  - Kéo thanh **Hệ số nhu cầu lambda**: số liệu và cột theo giờ đổi theo.
  - Điểm nào chưa chứng minh tối ưu được vẽ vòng tròn rỗng và ghi "chưa chứng minh tối ưu".

### Bước 9. Độ nhạy theo giả định (2 phút)

- **Làm:** vẫn ở **Độ nhạy**:
  1. **Giả định quy đổi cần thay đổi**: chọn `alpha`.
  2. **Các giá trị thử**: `0.8, 1.0, 1.2`.
  3. Bấm **Chạy quét giả định**.
- **Nói:** "Số người cần phụ thuộc vào giả định của nhóm. Ở đây hệ thống tính lại nhu cầu từ dữ liệu gốc với từng giá trị alpha rồi giải lại. Bảng kết quả luôn ghi rõ đây là giả định của nhóm, không phải dữ liệu nhân sự."
- **Ý nghĩa:** trả lời trước câu hỏi "giả định của nhóm có đáng tin không": cho thấy kết luận thay đổi bao nhiêu khi giả định thay đổi.
- **Mong đợi:** khung **Quét giả định quy đổi** có bảng 3 dòng (Giá trị, Chi phí tuần, Giờ thiếu, Giờ trả lương, Kết quả solver); chi phí tăng khi alpha tăng. Phân tích chạy tuần tự, tối đa khoảng 3 × 20 giây.

### Bước 10 (tùy chọn, nếu còn thời gian). Chi phí biên theo giờ

- **Làm:** nhập **Lương theo giờ cho mô hình chi phí biên (giả định của nhóm)** = `100`, bấm **Tính chi phí biên theo giờ**.
- **Nói:** "Với từng giờ trong tuần, hệ thống thêm yêu cầu một người ở giờ đó rồi giải lại, tức 169 lần giải. Chênh lệch chi phí là chi phí biên thật của giờ đó. Bản đồ nhiệt cho thấy giờ nào đắt nhất nếu cần thêm người. Dual của bài toán nới lỏng chỉ hiện kèm nhãn xấp xỉ."
- **Mong đợi:** bản đồ nhiệt 7 × 24 trong khung **Chi phí biên theo giờ**. Thời gian chạy trên dữ liệu store 18 chưa đo; nếu chậm, bỏ qua bước này.

### Bước 11. Xuất dữ liệu (30 giây)

- **Làm:** về trang kết quả lượt gốc, bấm một link xuất CSV, ví dụ **CSV độ phủ** hoặc **CSV KPI**.
- **Nói:** "Lịch và chỉ số xuất được ra CSV để dùng ở nơi khác."

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
| Trang không mở được | Kiểm `docker compose ps`; nếu container dừng, chạy `docker compose up -d` và đợi `healthy` |
| Dòng Nhân viên không ghi "Tất cả 30 nhân viên" | DB chưa sạch (mục B1). Không demo Optimize trên DB này; dùng ảnh dự phòng |
| Optimize chạy quá lâu | Đợi hết time limit; kết quả sẽ là FEASIBLE kèm gap. Dùng đó để giải thích nguyên tắc "không tự nhận tối ưu" |
| Sweep What-if chậm | Nói trong lúc chờ (bước 8); nếu quá lâu, chuyển sang bước 11 và quay lại sau |
| Mọi thứ hỏng | Mở ảnh trong `docs/acceptance/`: `schedule_run.png` (kết quả lịch), `schedule_violation.png` (cảnh báo Đ.110 sau khi sửa tay), các ảnh trang Nhu cầu, Nhân viên, Mẫu ca, Độ nhạy (giao diện tiếng Việt, chụp 2026-11-07) |

---

## F. Phần chưa kiểm

- Toàn bộ phần C chưa được bấm thử trên trình duyệt theo đúng thứ tự này. Nhãn nút lấy từ mã nguồn. Phải chạy thử trước buổi.
- Kết quả bước 4–5 (OPTIMAL, 12–20 giây) dựa trên lần đo bằng script với cùng dữ liệu, chưa đo qua giao diện.
- Thời gian bước 8, 9, 10 qua giao diện chưa đo.
- Ảnh trong `docs/acceptance/` chụp tự động ngày 2026-11-07, chưa qua duyệt tay. Ảnh `what_if.png` có kết quả quét nhu cầu, quét p và chi phí biên.
- Nội dung điều luật chưa đối chiếu nguyên văn (`docs/đặc tả.md` mục 4).
