# Nội dung slide bảo vệ ShiftOpt

Cập nhật: 2026-11-10. Số liệu lấy từ [báo cáo.md](báo%20cáo.md), [benchmarks.md](benchmarks.md), [đặc tả.md](đặc%20tả.md) và `docs/experiments/` (nguồn của benchmarks.md mục 5). Không thêm số nào ngoài các file đó; số chỉ đọc từ ảnh chụp giao diện thì không đặt lên slide. Kịch bản thao tác demo chi tiết ở [demo.md](demo.md).

Cấu trúc: 12 slide chính và 2 slide phụ lục (chỉ mở khi được hỏi).

Mỗi slide có ba phần:
- **Trên slide:** chữ đặt lên slide. Giữ ngắn, tối đa 5–6 ý. Không ghi mã quyết định nội bộ (D18, D20…) lên slide; mã chỉ để người trình bày tra cứu.
- **Hình:** hình hoặc bảng nên đặt.
- **Lời nói:** ý chính người trình bày nói, khoảng 1–1,5 phút mỗi slide.

**Thời lượng:** 12 slide khoảng 15–17 phút. Demo đầy đủ theo demo.md phần C khoảng 22 phút, nên khi bị giới hạn thời gian dùng **demo rút gọn 6–7 phút**: bước 2, 4, 5, 7, 7c, 8 của phiếu thao tác C0. Kiểm lại tổng thời gian được phép trước buổi.

---

## Slide 1. Giới thiệu

**Trên slide:**
- **ShiftOpt: xếp ca nhân viên cho dịch vụ có nhu cầu biến động**
- Quy hoạch nguyên tuyến tính · OR-Tools CP-SAT · PuLP + HiGHS · Web app
- Môn: Khoa học dịch vụ (INT3501E_1) · Nhóm 11
- Thành viên: Chu Đức Ánh, Lê Đình Tú, Nguyễn Quang Vinh
- Giảng viên: Cô Phạm Thị Quỳnh Trang

**Hình:** logo ShiftOpt (`assets/logo.svg`) hoặc ảnh trang chủ (cần chụp lại).

**Lời nói:** Giới thiệu nhóm và đề tài trong một câu: cửa hàng hoặc kho mở 24/7 cần biết mỗi giờ cần bao nhiêu người, rồi xếp ca cho từng nhân viên sao cho đủ người, chi phí thấp và đúng luật lao động.

---

## Slide 2. Bài toán và mục tiêu

**Trên slide:**
- Dịch vụ không lưu kho được: thiếu người thì khách chờ, thừa người thì tốn lương
- Nhu cầu đổi theo từng giờ, từng ngày; ca dài 8 giờ, nghỉ ≥ 12 giờ giữa hai ca, số ngày làm liên tiếp có giới hạn
- **Đầu vào:** nhu cầu 7 × 24 giờ, danh sách nhân viên, mẫu ca, tham số luật
- **Đầu ra:** lịch xếp ca, KPI (tỷ lệ phủ, giờ thiếu/thừa, chi phí, công bằng), danh sách vi phạm, phân tích độ nhạy
- **Thứ tự ưu tiên:** đủ người → chi phí thấp → công bằng → mong muốn nghỉ

**Hình:** sơ đồ một dòng: doanh số theo giờ → số người cần → lịch tối ưu → validator → độ nhạy.

**Lời nói:** Đây là bài toán cân đối cung (nhân lực) và cầu (khách) của dịch vụ: năng lực phục vụ không để dành được, nên phải khớp theo từng giờ. Đề bài yêu cầu bốn việc: mô hình hóa bằng quy hoạch nguyên, giải bằng OR-Tools hoặc PuLP, phân tích độ nhạy khi nhu cầu đổi, và làm giao diện nhập nhu cầu, xem lịch. Xếp tay khó vì có 168 giờ mỗi tuần, hàng chục nhân viên, và ràng buộc luật nối giữa các ngày.

---

## Slide 3. Dữ liệu và quy đổi nhu cầu

**Trên slide:**
- Dữ liệu mẫu: **FreshRetailNet-50K** (CC BY 4.0): doanh số theo giờ của kho thương mại điện tử, 90 ngày train + 7 ngày eval
- **Không phải dữ liệu nhân sự.** Số người suy ra từ giả định của nhóm
- Giờ hết hàng: thay bằng nhu cầu ẩn (trung bình cùng giờ, cùng thứ, ngày còn hàng)
- Quy đổi: **r = max(sàn, ⌈α · D / p⌉)**, với α = 1, p = 4, sàn = 1; giờ đêm 22h–06h dùng mức tối thiểu cố định
- Nhận bất kỳ file doanh số theo giờ (CSV hoặc parquet), chọn cột trên form

**Hình:** lưới 7 × 24 số người cần của store 18 (cần chụp lại trang Nhu cầu), giờ đỉnh 8 người, tổng 468 giờ-người mỗi tuần, kèm nhãn "doanh số chuẩn hóa, không phải nhu cầu nhân sự".

**Lời nói:** Nhấn mạnh tính trung thực về dữ liệu. Doanh số giờ đêm gần bằng 0 vì kho không nhập hàng ban đêm, nên giờ đêm dùng mức tối thiểu cố định. Store 18 có 90.159 ô hết hàng đã được thay bằng nhu cầu ẩn. α và p là giả định đã được nhóm duyệt (đặc tả D7–D8), luôn hiện trên giao diện và có thể quét độ nhạy (slide 10, 11). Chế độ tổng đài đã bỏ theo quyết định của nhóm (D18), nên hệ thống chỉ có một nguồn nhu cầu là file doanh số (D19).

---

## Slide 4. Mô hình toán

**Trên slide:**
- Biến: **x[e, d, s] ∈ {0, 1}**: nhân viên e làm ca s ngày d; **u_h ≥ 0**: số người thiếu ở giờ h
- Phủ nhu cầu mềm: **Σ người có mặt ở giờ h + u_h ≥ r_h** → mô hình luôn có nghiệm, chỉ rõ giờ nào thiếu
- Ràng buộc cứng: 1 ca/ngày; ≤ 48 giờ/tuần; nghỉ ≥ 12 giờ giữa hai ca; nghỉ 24 giờ liên tục mỗi tuần; ≤ 6 ngày liên tiếp; nghỉ giữa ca làm mất 1 giờ phủ
- Mục tiêu **lexicographic theo tầng**: (1) ít giờ thiếu → (2) chi phí lương + phụ cấp đêm 30% → (3) chia ca đêm đều → (4) tôn trọng ngày nghỉ mong muốn
- Hai solver: **CP-SAT** (lõi sản phẩm) và **PuLP + HiGHS** (cùng công thức ILP, để đối chiếu); thêm **phủ tập Dantzig** cho dual LP

**Hình:** công thức hàm mục tiêu và ràng buộc phủ; sơ đồ các tầng xếp chồng, mỗi tầng khóa giá trị tối ưu của tầng trước. Bảng ràng buộc C1–C11 để ở phụ lục A.

**Lời nói:** Giải thích vì sao chọn lexicographic thay cho trọng số phạt: số liệu ở slide 9 cho thấy trọng số đặt sai thì solver bỏ trống lịch mà không báo lỗi. Giải theo tầng bảo đảm thiếu người luôn được ưu tiên hơn chi phí. Khi bật thêm tùy chọn, có các tầng phụ: giờ tối thiểu theo hợp đồng ngay sau tầng 1, số ca thay đổi khi xếp lại, chênh giờ làm khi cho phép dung sai chi phí. Ngân sách tuần là ràng buộc cứng tùy chọn; vì độ phủ mềm nên ngân sách chặt chỉ làm tăng giờ thiếu chứ không làm mô hình vô nghiệm.

---

## Slide 5. Luật lao động và kiểm tra độc lập

**Trên slide:**

| Điều | Nội dung | Cài đặt |
|---|---|---|
| BLLĐ Đ.105 | ≤ 8 giờ/ngày, ≤ 48 giờ/tuần | Ràng buộc cứng |
| Đ.106, Đ.98 | Giờ đêm 22h–06h, phụ cấp ≥ 30% | Nằm trong chi phí ca |
| Đ.109, NĐ 145 Đ.64 | Nghỉ giữa ca 30 phút (đêm 45 phút), không đặt ở đầu hoặc cuối ca | Mất 1 giờ phủ, chặt hơn luật |
| Đ.110 | Nghỉ ≥ 12 giờ giữa hai ca | Ràng buộc cứng |
| Đ.111 | Nghỉ ≥ 24 giờ liên tục mỗi tuần | Ràng buộc cứng, tính trên trục giờ |

- **Solver đề xuất, validator phán xét:** mọi lịch được chương trình độc lập kiểm lại, kể cả khi solver báo OPTIMAL
- Ví dụ bị chặn: ca 14h–22h rồi 06h–14h hôm sau (chỉ nghỉ 8 giờ)

**Hình:** khung "Tuân thủ" của lượt sửa tay gây vi phạm Đ.110 (cần chụp lại theo demo.md bước 7).

**Lời nói:** Nêu "bẫy" Đ.111: ngày nghỉ trên lịch chưa chắc là 24 giờ nghỉ liên tục khi có ca qua đêm, nên validator tính khoảng nghỉ trên trục giờ. Validator không dùng chung code với mô hình, nên một lỗi trong mô hình không thể tự che giấu. Nguồn luật: BLLĐ 45/2019 đối chiếu bản gốc và bản hợp nhất VBHN 125/VBHN-VPQH (2025); Nghị định 145/2020 đối chiếu bản gốc. NĐ 145 chỉ bắt buộc nghỉ 45 phút khi làm ít nhất 3 giờ đêm; code áp cho mọi ca có giờ đêm, tức chặt hơn luật, có chủ đích.

---

## Slide 6. Kiến trúc hệ thống

**Trên slide:**
- **Engine** (Python thuần): mô hình, solver, validator, KPI, độ nhạy
- **Backend** (FastAPI + MySQL 8.4): lưu dữ liệu, giải trong tiến trình con, trả mã job để giao diện hỏi lại
- **Frontend** (React 19 + TypeScript): giao diện tiếng Việt, sáng/tối, biểu đồ tự vẽ
- **Tài khoản riêng:** mỗi người dùng chỉ thấy dữ liệu của mình; đăng ký xong có sẵn 30 nhân viên và 3 mẫu ca mẫu
- **Triển khai:** Docker Compose khi chạy máy; bản công khai: frontend trên Vercel, backend qua Cloudflare tunnel. CI kiểm lint, kiểu, test, migration
- **Tái lập:** mỗi lượt giải lưu đầu vào, seed, số worker, phiên bản solver; cùng seed và 1 worker cho cùng kết quả

**Hình:** sơ đồ khối: Trình duyệt → Frontend → Backend API → (MySQL, tiến trình giải → Engine).

**Lời nói:** Solver có thể chạy hàng chục giây, nên không chạy trong luồng xử lý request. API trả mã job ngay, giao diện hỏi lại tới khi xong. Lượt giải là bất biến: sửa tay hay xếp lại đều tạo lượt mới và chạy lại validator, lịch gốc giữ nguyên. Khi sửa nhân viên hoặc nhu cầu sau khi giải, lượt cũ hiện nhãn "Đầu vào đã đổi" (so hash đầu vào).

---

## Slide 7. Giao diện và demo

**Trên slide:**
1. **Nhu cầu:** lưới 7 × 24, nhập CSV, ingest file doanh số
2. **Nhân viên và mẫu ca:** nhập tay hoặc CSV; giờ tối đa và tối thiểu, ngày không làm được, ngày muốn nghỉ
3. **Tối ưu:** cảnh báo trước khi giải, ngân sách tuần; trạng thái solver, gap, thời gian
4. **Kết quả:** lịch, biểu đồ phủ (giờ thiếu có sọc chéo), chi phí, cảnh báo luật, "vì sao còn giờ thiếu", xuất CSV
5. **Xếp lại:** người vắng đột xuất, ngày khóa, ca ghim; gợi ý người thay
6. **What-if:** thanh trượt λ, heatmap chi phí biên, so sánh kịch bản, so với greedy, quét dung sai chi phí

**Hình:** ảnh có sẵn trong `docs/images/`: `repair.png` (xếp lại), `replacements.png` (gợi ý người thay), `reroster.png` (báo nghỉ), `schedule_dark.png` (giao diện tối), chụp 2026-11-08 trên stack demo. Ảnh trang Nhu cầu, kết quả và What-if cần chụp lại.

**Lời nói:** Chuyển sang demo trực tiếp theo demo.md phần C (bản rút gọn ở đầu file này), hoặc dùng ảnh nếu máy chiếu có sự cố. Điểm cần cho thấy: thiếu và thừa người phân biệt được bằng hình dạng chứ không chỉ bằng màu; trạng thái FEASIBLE luôn kèm gap; xếp lại chỉ đổi ít ca và lịch gốc vẫn còn.

---

## Slide 8. Kết quả thực nghiệm

**Trên slide:**

| Thực nghiệm | Kết quả |
|---|---|
| Lịch tuần, 20/30/40 nhân viên, dữ liệu sinh, 3 seed | 18/18 **OPTIMAL**, gap 0, phủ 100%, 0 vi phạm; lâu nhất 31,5 s (1 worker) |
| Store 18 (dữ liệu thật), 30 nhân viên | 3/3 **OPTIMAL**, phủ 100%, 0 vi phạm, 12–20 s |
| Store 18, chỉ 8 nhân viên (thiếu người) | **FEASIBLE**, phủ 70,3%, thiếu 139 giờ-người, gap 100%, 0 vi phạm |
| Benchmark công khai Curtois & Qu (8 worker, 120 s) | Instance1–3 đạt và chứng minh đúng tối ưu công bố; Instance4 đạt, chưa chứng minh; Instance5 cách 5 đơn vị |
| CP-SAT với HiGHS, cùng mô hình theo nhân viên | 20 và 30 người: cả hai chứng minh, cùng kết quả, 17–28 s; 10 người: CP-SAT chưa chứng minh, HiGHS chứng minh 2/3 seed |
| Integrality gap, store 18, 30 nhân viên | Tầng chi phí 0,72%; hai mô hình cùng OPTIMAL, cùng chi phí nguyên |

- Engine 236 test, coverage 98,13%; backend 219 test (53 integration trên MySQL 8.4 trong CI)

**Hình:** bảng trên; có thể thêm biểu đồ cột thời gian giải theo số nhân viên (benchmarks.md mục 3a).

**Lời nói:** Đọc kết quả trung thực. Kịch bản 30 nhân viên dư sức chứa (cần 468 giờ-người, có 1.440), nên phủ 100% chưa chứng minh khả năng xử lý khi thiếu người. Ở kịch bản 8 nhân viên, solver không chứng minh được tối ưu trong 60 giây, và hệ thống ghi đúng là FEASIBLE thay vì tự nhận tối ưu. Trên dữ liệu sinh, integrality gap lớn hơn nhiều (mô hình tổng hợp 0–40%; theo nhân viên, tầng thiếu người 6–15%), đó là lý do dual LP luôn ghi "xấp xỉ". Mọi kết luận chỉ áp dụng cho các instance đã đo.

---

## Slide 9. So với baseline, xếp lại và đánh đổi

**Trên slide:**
- **Greedy** (heuristic) trên 3 store 18, 84, 578: greedy thường thiếu người nhiều hơn; khi cùng số giờ thiếu, CP-SAT rẻ hơn 0–5,7%
- **Xếp lại khi 1 người báo nghỉ:** CP-SAT đổi 4–13 ca, greedy chạy lại đổi 16–52 ca
- **Lexicographic so với trọng số:** trọng số thiếu người 1 hoặc 1.000 → không xếp ai (thiếu 414/414 giờ), không báo lỗi
- **Dung sai chi phí** (20 nhân viên, lương lệch): trả thêm 2–10% thì chênh ca đêm 6 → 1, chênh giờ làm 48 → 24

**Hình:** bảng rút từ benchmarks.md mục 5, 6, 8.

**Lời nói:** Chi phí thấp hơn của greedy đến từ việc thiếu người nhiều hơn, nên không phải lợi thế. Với xếp lại, greedy được chạy lại từ đầu nên đây là so sánh số ca thay đổi, không phải so sánh thuật toán. Ví dụ trọng số cho thấy rủi ro của cách phạt: một giờ-người phục vụ chỉ được thưởng w, trong khi tốn khoảng 10.000 tiền lương, nên solver chọn bỏ trống. Dung sai chi phí cho quản lý một nút vặn rõ ràng: trả thêm bao nhiêu để lịch công bằng hơn. Các điểm dung sai đều FEASIBLE trong 60 giây, chỉ đọc như xu hướng.

---

## Slide 10. Phân tích độ nhạy

**Trên slide:**
- **Quét nhu cầu λ ∈ [0,8; 1,3]:** giải lại với nhu cầu ⌈λ · r⌉, vẽ chi phí z(λ) và giờ thiếu
- **Chi phí biên theo giờ:** z(r + 1 người ở giờ t) − z(r), bằng **168 lần giải lại**, hiển thị heatmap 7 × 24
- **Dual của bài toán nới lỏng LP:** chỉ để so sánh, luôn gắn nhãn **"xấp xỉ"**
- **Quét giả định quy đổi** α, p, sàn: thấy lịch thay đổi khi giả định thay đổi
- Điểm giải lại không OPTIMAL được đánh dấu "chưa chứng minh"

**Hình:** đường cong z(λ) và heatmap chi phí biên của trang What-if (store 18, 30 nhân viên; cần chụp lại). Không ghi số từ ảnh lên slide; số đo của quét p nằm ở slide 11.

**Lời nói:** Mô hình nguyên không có "giá bóng" (shadow price) hợp lệ, nên nhóm tính chi phí biên bằng cách giải lại thật. Dual LP chỉ dùng để thấy khoảng cách với bài toán nguyên, và luôn ghi rõ là xấp xỉ. Kiểm tay (có test tự động): 3 ca 8 giờ, cần 1 người mỗi giờ. Giờ 3 thuộc ca 0h–8h, nên thêm 1 người ở giờ 3 buộc mở thêm đúng một ca này. Chi phí biên bằng chi phí ca đó: 8 giờ lương cộng phụ cấp 30% cho 6 giờ đêm (0h–6h), tức 9,8 giờ lương (báo cáo ghi dạng 100 × 980 theo đơn vị phần trăm). Kết quả giải lại khớp đúng con số này.

---

## Slide 11. Nhận xét cho người quản lý

**Trên slide** (store 18, 15 nhân viên, 30 s, seed 0):
- **Thiết kế ca quan trọng hơn thêm người:** 3 → 6 giờ bắt đầu ca: giờ thiếu 12 → 0, giờ thừa 174 → 71, chi phí −15,8%, cùng 15 người
- **Mỗi người bớt đi làm thiếu nhanh dần:** bớt 1 người → 18 giờ thiếu, bớt 2 → 30, bớt 5 → 81
- **Nhu cầu tăng 10%** (λ = 1,1) → 56 giờ thiếu; tăng 30% → 101
- **Giả định năng suất p** tác động ngang biến động nhu cầu: p = 3 → 60 giờ thiếu; p = 5 → phủ đủ
- **Công bằng có giá rõ ràng:** trả thêm khoảng 2% chi phí → chênh ca đêm 6 → 1 (dữ liệu sinh, 20 người)

**Hình:** bảng benchmarks.md mục 5b; có thể vẽ cột giờ thiếu theo kịch bản.

**Lời nói:** Đây là các câu trả lời mà quản lý dịch vụ cần: nên thêm người hay đổi mẫu ca, bớt người thì mất bao nhiêu độ phủ, nhu cầu tăng thì sao. Kịch bản này dùng 15 nhân viên (khoảng 1,25 lần nhu cầu chia 40 giờ), khác kịch bản cơ sở 30 người ở slide 8. Các lượt bớt 5 người và λ = 1,3 chỉ FEASIBLE ở tầng thiếu người, nên số đó là cận trên. Chi phí giảm khi thiếu người tăng không phải là tiết kiệm, mà là phần không được phục vụ. Kết quả là một store, một seed; không suy ra cho cửa hàng khác.

---

## Slide 12. Kết luận, hạn chế và hướng phát triển

**Trên slide:**
- **Đạt được:** mô hình quy hoạch nguyên đủ ràng buộc luật lao động, giải bằng hai solver; tối ưu 20–40 nhân viên (dữ liệu sinh) dưới 32 s và store 18 (30 người) dưới 20 s; validator độc lập; độ nhạy bằng giải lại; xếp lại khi có người vắng; web app công khai
- **Hạn chế:**
  - Dữ liệu là doanh số, không phải nhu cầu nhân sự; α, p là giả định của nhóm
  - Kịch bản cơ sở một store; so baseline 3 store
  - Khi thiếu người, chưa chứng minh được tối ưu trong 60 giây
  - Tuần quấn vòng, chưa nối với tuần trước; nghỉ giữa giờ làm tròn thành 1 giờ
- **Hướng phát triển:** tuần nối tuần trước, dự báo nhu cầu, nhiều kỹ năng, nhiều cửa hàng, mô hình ngẫu nhiên
- **Cảm ơn thầy cô và các bạn đã lắng nghe. Mời đặt câu hỏi.**

**Hình:** ảnh trang chủ hoặc ảnh lịch kết quả làm nền mờ.

**Lời nói:** Tóm lại ba điểm khác biệt: solver đề xuất, validator phán xét; độ nhạy tính bằng giải lại thật; mọi giả định đều hiện trên giao diện. Sau đó mời hỏi đáp; bảng câu hỏi thường gặp ở demo.md phần D. Không trích mức "vừa đủ người" của kịch bản 30 người vì chưa đo.

---

## Phụ lục A. Bảng ràng buộc C1–C11

**Trên slide:**

| Ký hiệu | Ràng buộc | Nguồn |
|---|---|---|
| C1 | Tối đa một ca mỗi ngày | mô hình |
| C2 | Giờ tuần không quá giới hạn | Đ.105 |
| C3 | Nghỉ ít nhất 12 giờ giữa hai ca | Đ.110 |
| C4 | Không quá K = 6 ngày làm liên tiếp | đề bài |
| C5 | Nghỉ liên tục ít nhất 24 giờ mỗi tuần | Đ.111 |
| C6 | Mỗi ca cần nghỉ có đúng một giờ nghỉ | Đ.109 |
| C7 | Phủ nhu cầu theo giờ, thiếu người là biến mềm u_h | đề bài |
| C8 | Chênh lệch ca đêm giữa các nhân viên | công bằng |
| C9 | Chi phí không vượt ngân sách tuần (tùy chọn) | quản lý |
| C10 | Giờ dưới mức tối thiểu hợp đồng, mềm | hợp đồng |
| C11 | Chênh giờ làm (khi có dung sai chi phí) | công bằng |

**Lời nói:** Chỉ mở khi được hỏi về công thức. Chi tiết ở báo cáo.md mục 2 và model.md mục 2a.

---

## Phụ lục B. Tài liệu tham khảo

**Trên slide:**
- Bộ luật Lao động số 45/2019/QH14; Văn bản hợp nhất 125/VBHN-VPQH (2025); Nghị định 145/2020/NĐ-CP
- Dantzig, G. B. (1954). A comment on Edie's "Traffic delays at toll booths". *Operations Research*, 2(3)
- Bechtold, S. E. & Jacobs, L. W. (1990). Implicit modeling of flexible break assignments in optimal shift scheduling. *Management Science*, 36(11)
- Van den Bergh, J. et al. (2013). Personnel scheduling: A literature review. *European Journal of Operational Research*, 226(3)
- Curtois, T. & Qu, R. (2014). Computational results on new staff scheduling benchmark instances. schedulingbenchmarks.org
- FreshRetailNet-50K, Dingdong-Inc, Hugging Face, CC BY 4.0, arXiv:2505.16319
- Google OR-Tools (CP-SAT) 9.15; PuLP 3.3 + HiGHS

**Lời nói:** Không trình bày; để trên slide cho hội đồng tra cứu. Nhóm kiểm lại thông tin xuất bản (năm, số tập) trước khi in.

---

## Việc cần làm trước buổi bảo vệ

- Slide 1 đã điền môn, nhóm, thành viên, giảng viên (không ghi ngày bảo vệ). Nếu môn yêu cầu, thêm slide phân công thành viên sau slide 1.
- Chụp lại màn hình cho slide 1, 3, 5, 7, 10 (ảnh 2026-11-07 đã bỏ khỏi repo; `docs/images/` chỉ có xếp lại, gợi ý người thay, báo nghỉ, giao diện tối).
- Nếu demo trên bản công khai (Vercel + tunnel), kiểm lại URL tunnel ngay trước buổi; chuẩn bị Compose chạy máy làm dự phòng.
- Chạy thử demo rút gọn và bấm giờ cả bài; cắt bớt bước demo nếu vượt thời gian.
- Nếu nhóm đổi α, p hoặc kịch bản cơ sở (đặc tả D7–D9, D13), cập nhật số ở slide 3, 8, 11.
