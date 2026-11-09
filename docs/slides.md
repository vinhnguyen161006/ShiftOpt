# Nội dung 11 slide bảo vệ ShiftOpt

Cập nhật: 2026-11-09. Số liệu lấy từ [báo cáo.md](báo%20cáo.md), [benchmarks.md](benchmarks.md), [đặc tả.md](đặc%20tả.md). Không thêm số nào ngoài các file đó. Kịch bản thao tác demo chi tiết ở [demo.md](demo.md).

Mỗi slide có ba phần:
- **Trên slide:** chữ đặt lên slide. Giữ ngắn, mỗi slide tối đa 5–6 ý.
- **Hình:** hình hoặc bảng nên đặt.
- **Lời nói:** ý chính người trình bày nói, khoảng 1–2 phút mỗi slide.

Tổng thời lượng dự kiến khoảng 15 phút, chưa tính demo trực tiếp và hỏi đáp.

---

## Slide 1. Giới thiệu

**Trên slide:**
- **ShiftOpt: xếp ca nhân viên cho dịch vụ có nhu cầu biến động**
- Quy hoạch nguyên tuyến tính · OR-Tools CP-SAT · PuLP + HiGHS · Web app
- Môn: Khoa học dịch vụ
- Nhóm: *[tên thành viên]*
- Giảng viên hướng dẫn: *[tên]*
- Ngày bảo vệ: *[ngày]*

**Hình:** logo ShiftOpt (`assets/logo.svg`) hoặc ảnh trang chủ (cần chụp lại, xem mục cuối).

**Lời nói:** Giới thiệu nhóm và đề tài trong một câu: cửa hàng hoặc kho mở 24/7 cần biết mỗi giờ cần bao nhiêu người, rồi xếp ca cho từng nhân viên sao cho đủ người, chi phí thấp và đúng luật lao động.

---

## Slide 2. Bài toán và mục tiêu

**Trên slide:**
- Nhu cầu thay đổi theo từng giờ, từng ngày trong tuần
- Ca dài 8 giờ, nghỉ ≥ 12 giờ giữa hai ca, số ngày làm liên tiếp có giới hạn
- **Đầu vào:** nhu cầu 7 × 24 giờ, danh sách nhân viên, mẫu ca, tham số luật
- **Đầu ra:** lịch xếp ca, KPI (tỷ lệ phủ, giờ thiếu/thừa, chi phí), danh sách vi phạm, phân tích độ nhạy
- **Mục tiêu:** đủ người → (giờ hợp đồng) → chi phí thấp, trong ngân sách → công bằng → tôn trọng mong muốn nghỉ

**Hình:** sơ đồ một dòng: nhu cầu theo giờ → số người cần → lịch tối ưu → kiểm tra → độ nhạy.

**Lời nói:** Đề bài yêu cầu bốn việc: mô hình hóa bằng quy hoạch nguyên, giải bằng OR-Tools hoặc PuLP, phân tích độ nhạy khi nhu cầu đổi, và làm giao diện nhập nhu cầu, xem lịch. Xếp tay khó vì có 168 giờ mỗi tuần, hàng chục nhân viên, và các ràng buộc luật nối giữa các ngày.

---

## Slide 3. Dữ liệu và quy đổi nhu cầu

**Trên slide:**
- Nguồn: **FreshRetailNet-50K** (CC BY 4.0): doanh số theo giờ của kho thương mại điện tử, 90 ngày train + 7 ngày eval
- **Không phải dữ liệu nhân sự.** Số người suy ra từ giả định của nhóm
- Giờ hết hàng: thay bằng nhu cầu ẩn (trung bình cùng giờ, cùng thứ, ngày không hết hàng)
- Quy đổi: **r = max(sàn, ⌈α · D / p⌉)**, với α = 1, p = 4, sàn = 1
- Giờ đêm 22h–06h dùng mức tối thiểu cố định, không suy từ doanh số
- Nguồn khác: ingest bất kỳ file doanh số theo giờ (CSV hoặc parquet), chọn cột trên form (đặc tả D19). Chế độ tổng đài đã bỏ (D18)

**Hình:** lưới 7 × 24 số người cần của store 18 (cần chụp lại trang Nhu cầu), giờ đỉnh cần 8 người, kèm nhãn "doanh số chuẩn hóa, không phải nhu cầu nhân sự".

**Lời nói:** Nhấn mạnh tính trung thực về dữ liệu. Doanh số giờ đêm gần bằng 0 vì kho không nhập hàng ban đêm, nên giờ đêm dùng mức tối thiểu cố định. Store 18 có 90.159 ô hết hàng đã được thay bằng nhu cầu ẩn. α và p là giả định đã được nhóm duyệt (đặc tả D7–D8), luôn hiện trên giao diện và có thể quét độ nhạy (slide 10).

---

## Slide 4. Mô hình toán

**Trên slide:**
- Biến: **x[e, d, s] ∈ {0, 1}**: nhân viên e làm ca s ngày d; **u_h ≥ 0**: số người thiếu ở giờ h
- Phủ nhu cầu (mềm): số người có mặt ở giờ h cộng u_h ≥ r_h, nên mô hình luôn có nghiệm
- Ràng buộc cứng: tối đa 1 ca/ngày; ≤ 8 giờ/ngày, ≤ 48 giờ/tuần; nghỉ ≥ 12 giờ; nghỉ 24 giờ liên tục mỗi tuần; ≤ 6 ngày liên tiếp; nghỉ giữa ca làm mất 1 giờ phủ
- Mục tiêu **lexicographic theo tầng**: (1) ít giờ thiếu nhất → (2) chi phí lương + phụ cấp đêm 30% → (3) chia ca đêm đều → (4) tôn trọng ngày nghỉ mong muốn. Tầng phụ khi bật: giờ tối thiểu hợp đồng (sau 1), chênh giờ làm khi có dung sai chi phí (sau 3)
- Công thức **ILP đầy đủ C1–C11**, giải bằng cả **CP-SAT** (lõi sản phẩm) và **PuLP + HiGHS** (đối chiếu, integrality gap); thêm **phủ tập Dantzig** cho chi phí biên và dual LP

**Hình:** công thức gọn của hàm mục tiêu và ràng buộc phủ; sơ đồ các tầng xếp chồng; bảng C1–C11 lấy từ `báo cáo.md` mục 2.

**Lời nói:** Giải thích vì sao chọn lexicographic thay cho trọng số phạt: chọn một số M lớn tùy tiện dễ làm sai thứ tự ưu tiên. Giải theo tầng bảo đảm thiếu người luôn được ưu tiên hơn chi phí, và mỗi tầng không làm hỏng kết quả của tầng trước. Coverage để mềm nên khi thiếu nhân lực vẫn có lịch, kèm chỉ rõ giờ nào thiếu.

---

## Slide 5. Luật lao động và kiểm tra độc lập

**Trên slide:**

| Điều (BLLĐ 2019) | Nội dung | Cài đặt |
|---|---|---|
| Đ.105 | ≤ 8 giờ/ngày, ≤ 48 giờ/tuần | Ràng buộc cứng |
| Đ.106, Đ.98 | Giờ đêm 22h–06h, phụ cấp ≥ 30% | Nằm trong chi phí ca |
| Đ.109 | Nghỉ giữa ca 30 phút (đêm 45 phút) | Mất 1 giờ phủ |
| Đ.110 | Nghỉ ≥ 12 giờ giữa hai ca | Ràng buộc cứng |
| Đ.111 | Nghỉ ≥ 24 giờ liên tục mỗi tuần | Ràng buộc cứng, tính trên trục giờ |

- **Solver đề xuất, validator phán xét:** mọi lịch được một chương trình độc lập kiểm lại, kể cả khi solver báo OPTIMAL
- Ví dụ bị chặn: ca 14h–22h rồi 06h–14h hôm sau (chỉ nghỉ 8 giờ)

**Hình:** khung "Tuân thủ" của lượt sửa tay gây vi phạm Đ.110 (cần chụp lại theo `demo.md` bước 7).

**Lời nói:** Nêu "bẫy" Đ.111: ngày nghỉ trên lịch chưa chắc là 24 giờ nghỉ liên tục khi có ca qua đêm, nên validator tính khoảng nghỉ trên trục giờ. Validator không dùng chung code với mô hình, nên một lỗi trong mô hình không thể tự che giấu. Lưu ý trung thực: Điều 98, 105, 106, 109, 110, 111 đã đối chiếu với bản hợp nhất VBHN 125/VBHN-VPQH (2025); Nghị định 145/2020 chưa đối chiếu văn bản gốc.

---

## Slide 6. Kiến trúc hệ thống

**Trên slide:**
- **Engine** (Python thuần): mô hình, solver, validator, KPI, độ nhạy
- **Backend** (FastAPI + MySQL 8.4): lưu dữ liệu; giải trong tiến trình con; trả `job_id` để giao diện hỏi lại
- **Frontend** (React 19 + TypeScript): giao diện tiếng Việt, biểu đồ tự vẽ
- Chạy toàn bộ bằng **Docker Compose**; CI kiểm lint, kiểu, test, migration
- **Tái lập:** mỗi lượt giải lưu đầu vào, seed, số worker, phiên bản solver; cùng seed và 1 worker cho cùng kết quả

**Hình:** sơ đồ khối: Trình duyệt → Frontend → Backend API → (MySQL, tiến trình giải → Engine).

**Lời nói:** Solver có thể chạy hàng chục giây, nên không chạy trong luồng xử lý request. API trả mã job ngay, giao diện hỏi lại cho tới khi xong. Lượt giải là bất biến: sửa tay tạo lượt mới và chạy lại validator, lịch gốc giữ nguyên.

---

## Slide 7. Giao diện và demo

**Trên slide:**
1. **Nhu cầu:** lưới 7 × 24, nhập CSV, ingest file doanh số (CSV hoặc parquet)
2. **Nhân viên và mẫu ca:** giờ tối đa và tối thiểu riêng, ngày không làm được, ngày muốn nghỉ
3. **Tối ưu:** cảnh báo trước khi giải, ngân sách tuần, dung sai chi phí; trạng thái solver, gap, thời gian giải
4. **Kết quả:** lịch nhân viên × ngày, biểu đồ phủ nhu cầu (giờ thiếu có sọc chéo), chi phí, cảnh báo luật, bảng "vì sao còn giờ thiếu", nhãn "đầu vào đã đổi", xuất CSV
5. **What-if:** thanh trượt λ, heatmap chi phí biên theo giờ, so sánh kịch bản, so với baseline greedy, quét dung sai chi phí
6. **Xếp lại:** người vắng đột xuất, ngày khóa, ca ghim; gợi ý người thay (đặc tả D20)

**Hình:** ảnh có sẵn trong `docs/images/`: `repair.png` (xếp lại), `replacements.png` (gợi ý người thay), `reroster.png` (báo nghỉ), `schedule_dark.png` (giao diện tối), chụp 2026-11-08 trên stack demo. Ảnh trang Nhu cầu, kết quả và What-if cần chụp lại.

**Lời nói:** Chuyển sang demo trực tiếp theo [demo.md](demo.md) phần C, hoặc dùng ảnh nếu máy chiếu có sự cố. Điểm cần cho thấy: thiếu và thừa người phân biệt được bằng hình dạng chứ không chỉ bằng màu; trạng thái FEASIBLE luôn kèm gap.

---

## Slide 8. Kết quả thực nghiệm

**Trên slide:**

| Thực nghiệm | Kết quả |
|---|---|
| Lịch tuần, 20/30/40 nhân viên, 3 seed | 18/18 lần **OPTIMAL**, gap 0, phủ 100%, 0 vi phạm; lâu nhất 31,5 s (1 worker) |
| Store 18, 30 nhân viên | 3/3 **OPTIMAL**, phủ 100%, 0 vi phạm, 12–20 s |
| Store 18, chỉ 8 nhân viên (thiếu người) | **FEASIBLE**, phủ 70,3%, thiếu 139 giờ-người, gap 100%, 0 vi phạm |
| Benchmark Curtois & Qu (8 worker, 120 s) | Instance1–3 đạt đúng tối ưu công bố và chứng minh được; Instance4 đạt nhưng chưa chứng minh; Instance5 cách 5 đơn vị |
| CP-SAT với HiGHS (mô hình tổng hợp) | Cùng OPTIMAL, cùng objective trên 3 instance, đều dưới 0,1 s |
| CP-SAT với HiGHS (theo nhân viên, 10–30 người, 3 seed) | 20 và 30 người: cả hai chứng minh, cùng kết quả, 17–28 s; 10 người: CP-SAT chưa chứng minh, HiGHS chứng minh 2/3 seed |
| Integrality gap | Mô hình tổng hợp 0–40%; theo nhân viên: tầng chi phí dưới 0,4%, tầng thiếu người 6–15% |

- Engine: 236 test, coverage 98,13%; backend: 168 test (131 unit, 37 integration trên MySQL 8.4 trong CI)

**Hình:** bảng trên; có thể thêm biểu đồ cột thời gian giải theo số nhân viên.

**Lời nói:** Đọc kết quả trung thực. Kịch bản 30 nhân viên đang dư sức chứa (cần 468 giờ-người, có 1.440), nên phủ 100% chưa chứng minh khả năng xử lý khi thiếu người. Ở kịch bản 8 nhân viên, solver không chứng minh được tối ưu trong 60 giây, và hệ thống ghi đúng là FEASIBLE thay vì tự nhận tối ưu. Mọi kết luận chỉ áp dụng cho các instance đã đo.

---

## Slide 9. So với baseline và đánh đổi chi phí, công bằng

**Trên slide:**
- **Greedy** (heuristic, không bao giờ báo tối ưu) trên 3 store 18, 84, 578: greedy thường thiếu người nhiều hơn; chỉ so chi phí khi cùng số giờ thiếu, khi đó CP-SAT rẻ hơn 0–5,7%
- Báo nghỉ 1 người: xếp lại đổi 4–13 ca, greedy chạy lại đổi 16–52 ca
- **Lexicographic so với trọng số:** trọng số thiếu người quá nhỏ thì không xếp ai mà không báo lỗi
- **Dung sai chi phí:** 20 nhân viên, lương lệch, trả thêm 2–10% thì chênh ca đêm 6 → 1, chênh giờ làm 48 → 24 (mọi điểm FEASIBLE trong 60 s)

**Hình:** bảng rút từ `benchmarks.md` mục 5, 6, 8.

**Lời nói:** Chi phí thấp hơn của greedy đến từ việc thiếu người nhiều hơn, nên không phải lợi thế. Dung sai chi phí cho quản lý một nút vặn rõ ràng: trả thêm bao nhiêu để lịch công bằng hơn. Các điểm đo của dung sai chưa được chứng minh tối ưu, nên chỉ đọc như xu hướng.

---

## Slide 10. Phân tích độ nhạy

**Trên slide:**
- **Quét nhu cầu λ ∈ [0,8; 1,3]:** giải lại với nhu cầu ⌈λ · r⌉, vẽ đường chi phí z(λ) và giờ thiếu
- **Chi phí biên theo giờ:** z(r + 1 người ở giờ t) − z(r), bằng **168 lần giải lại**, hiển thị thành heatmap 7 × 24
- **Dual của bài toán nới lỏng LP:** chỉ dùng để so sánh, luôn gắn nhãn **"xấp xỉ"**
- **Quét giả định quy đổi** α, p, sàn: thấy lịch thay đổi khi giả định thay đổi
- Điểm giải lại không OPTIMAL được đánh dấu "chưa chứng minh"

**Hình:** đường cong z(λ), bảng quét p và heatmap chi phí biên của trang What-if (store 18, 30 nhân viên; cần chụp lại). Quét p trên ảnh: p = 3, 4, 5 cho chi phí tuần 115.200, 88.920, 71.660, đều 0 giờ thiếu. Các số này chỉ là ảnh chụp một lần chạy, chưa được đưa vào `benchmarks.md`.

**Lời nói:** Mô hình nguyên không có "giá bóng" (shadow price) hợp lệ, nên nhóm tính chi phí biên bằng cách giải lại thật. Dual LP chỉ dùng để thấy khoảng cách với bài toán nguyên, và luôn ghi rõ là xấp xỉ. Ví dụ kiểm tay: 3 ca, nhu cầu 1 người mỗi giờ, chi phí biên ở giờ 3 bằng 100 × 980, khớp với tính tay.

---

## Slide 11. Kết luận, hạn chế và hướng phát triển

**Trên slide:**
- **Đạt được:** mô hình quy hoạch nguyên đủ ràng buộc luật lao động, viết ILP và giải bằng hai solver; giải tối ưu 20–40 nhân viên dưới 32 s; validator độc lập; độ nhạy bằng giải lại; xếp lại khi có người vắng; web app chạy bằng Docker
- **Hạn chế:**
  - Kịch bản cơ sở một store, so baseline 3 store; dữ liệu là doanh số, không phải nhu cầu nhân sự
  - α, p là giả định của nhóm; Nghị định 145/2020 chưa đối chiếu văn bản gốc
  - Khi thiếu người, chưa chứng minh được tối ưu trong 60 giây
  - Tuần quấn vòng, chưa nối với tuần trước
- **Hướng phát triển:** tuần nối tuần trước, dự báo nhu cầu, nhiều kỹ năng, nhiều cửa hàng, mô hình ngẫu nhiên
- **Cảm ơn thầy cô và các bạn đã lắng nghe. Mời đặt câu hỏi.**

**Hình:** ảnh trang chủ hoặc ảnh lịch kết quả làm nền mờ.

**Lời nói:** Tóm lại ba điểm khác biệt: solver đề xuất, validator phán xét; độ nhạy tính bằng giải lại thật; mọi giả định đều hiện trên giao diện. Sau đó mời hỏi đáp; bảng câu hỏi thường gặp chuẩn bị sẵn ở [demo.md](demo.md) phần D.

---

## Việc cần làm trước buổi bảo vệ

- Điền tên thành viên, giảng viên, ngày bảo vệ (slide 1).
- Chụp lại các màn hình cần dùng cho slide 1, 3, 5, 7, 10 (ảnh 2026-11-07 đã bỏ khỏi repo; ảnh trong `docs/images/` chỉ có xếp lại, gợi ý người thay, báo nghỉ, giao diện tối).
- Nếu nhóm đổi α, p hoặc kịch bản cơ sở (đặc tả D7–D9, D13), cập nhật số ở slide 3 và 8.
