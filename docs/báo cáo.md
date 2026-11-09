# Xếp ca nhân viên cho dịch vụ có nhu cầu biến động: báo cáo cuối

Cập nhật: 2026-11-09. Trạng thái: bản để nhóm duyệt. Mọi số liệu truy được tới lệnh và bảng nguồn ghi trong ngoặc. Kết luận hiệu năng chỉ áp cho các instance đã đo.

## 1. Bài toán

Xếp ca cho nhân viên sao cho số người có mặt đáp ứng nhu cầu theo giờ, trong ràng buộc pháp lý về giờ làm, nghỉ giữa ca, nghỉ hằng tuần và số ngày làm liên tiếp. Phạm vi bản đầu: một địa điểm, lịch tuần 7×24, một loại kỹ năng ([đặc tả.md](đặc%20tả.md) mục 1).

Đầu ra: lịch xếp ca, KPI, danh sách vi phạm, và phân tích độ nhạy khi nhu cầu hoặc giả định quy đổi thay đổi. Ngoài ra hệ thống hỗ trợ vận hành: xếp lại khi có người vắng, gợi ý người thay, cảnh báo trước khi giải, giải thích giờ thiếu, ngân sách tuần, giờ tối thiểu theo hợp đồng và nhãn kết quả cũ (mục 6d).

## 2. Mô hình

Hai tầng:

- **Tổng hợp (Dantzig, phủ tập).** Số người theo kiểu ca, `min sum c_s x_s`, `sum a_ts x_s >= r_t`, `x` nguyên không âm. Giải bằng PuLP + HiGHS. Dùng để benchmark, lấy dual LP xấp xỉ, và đối chiếu với chi phí biên. Nghỉ giữa ca được mô hình hóa như mất một giờ phủ (Bechtold–Jacobs đơn giản).
- **Theo nhân viên (CP-SAT).** Biến `x[e,d,s]` Boolean, nghỉ giữa giờ `b[e,d,s,k]`, thiếu người `u_h`, cửa sổ nghỉ 24 giờ `v[e,t]`. Hàm mục tiêu lexicographic theo tầng: thiếu người, giờ tối thiểu theo hợp đồng (chỉ khi có), chi phí lương có phụ cấp đêm, chênh lệch ca đêm, chênh giờ làm (chỉ khi có dung sai chi phí), vi phạm sở thích. Mỗi tầng một lần giải, tầng sau bị khóa bởi tối ưu tầng trước. `OPTIMAL` chỉ khi mọi tầng `OPTIMAL` ([model.md](model.md) mục 2).

Chọn lexicographic thay vì trọng số phạt `M` tùy ý (quyết định D11). Coverage là mềm, có biến thiếu người, nên mô hình luôn khả thi và UI chỉ rõ giờ thiếu.

Validator độc lập (`validation.py`) kiểm lại mọi nghiệm trên trục giờ quấn vòng, không import `models/` hay `solvers/`. Mọi lượt giải đi qua validator trước khi lưu; vi phạm cứng > 0 thì lượt đánh dấu `failed`.

### Công thức ILP theo nhân viên

Mô hình theo nhân viên được viết thành quy hoạch nguyên đầy đủ và giải theo hai cách: CP-SAT (lõi sản phẩm) và HiGHS qua PuLP (`roster_mip.py`, để so sánh). Hai bản dùng cùng các nhóm ràng buộc C1–C11; chi tiết và ánh xạ sang hàm trong code ở [model.md](model.md) mục 2a.

| Ký hiệu | Ràng buộc | Điều luật |
|---|---|---|
| C1 | Tối đa một ca mỗi ngày | mô hình |
| C2 | Giờ tuần không quá giới hạn | Điều 105 |
| C3 | Nghỉ ít nhất 12 giờ giữa hai ca | Điều 110 |
| C4 | Không quá K ngày làm liên tiếp | đề bài |
| C5 | Nghỉ liên tục ít nhất 24 giờ mỗi tuần, viết theo cặp | Điều 111 |
| C6 | Mỗi ca cần nghỉ có đúng một giờ nghỉ | Điều 109 |
| C7 | Phủ nhu cầu theo giờ, thiếu người là biến mềm `u_h` | đề bài |
| C8 | Chênh lệch ca đêm giữa các nhân viên | công bằng |
| C9 | Tổng chi phí không vượt ngân sách tuần (tùy chọn) | đặc tả D26 |
| C10 | Giờ dưới mức tối thiểu theo hợp đồng, biến mềm | đặc tả D25 |
| C11 | Chênh giờ làm giữa các nhân viên (chỉ khi có dung sai chi phí) | đặc tả D21 |

Mục tiêu giải theo tầng: thiếu người, rồi giờ tối thiểu (khi có), rồi (khi sửa lịch) số ca thay đổi, rồi chi phí lương có phụ cấp đêm, rồi chênh lệch ca đêm, rồi chênh giờ làm (khi có dung sai), rồi sở thích. Mỗi tầng là một lần giải và được khóa bằng tối ưu của tầng trước.

## 3. Ràng buộc pháp lý

Các hằng nằm trong `LaborRules`: giờ/ngày 8, giờ/tuần 48, nghỉ 12 giờ giữa ca, nghỉ 24 giờ hằng tuần, khung đêm 22h–06h, phụ cấp đêm 30%, nghỉ giữa giờ 30 phút (45 phút ban đêm), `K = 6` ngày liên tiếp.

**Đối chiếu luật.** Điều 98, 105, 106, 109, 110, 111 đã đối chiếu với VBHN 125/VBHN-VPQH (2025); Đ.111 khoản 1 và Đ.105 khoản 2 của code chặt hơn luật. Nghị định 145/2020 chưa đối chiếu văn bản gốc. Xem [đặc tả.md](đặc%20tả.md) mục 4.

Hai ca pháp lý của nghiệm thu được kiểm bằng test: ca 14h–22h rồi 06h–14h bị cấm; ca qua đêm rồi nghỉ đủ 24 giờ không bị báo vi phạm (`test_afternoon_then_morning_breaks_rest_rule`, `test_overnight_shift_then_full_24_hour_rest_is_allowed`) (CLAUDE.md mục 13, dòng 6).

## 4. Dữ liệu và giả định

- **Nguồn nhu cầu.** FreshRetailNet-50K (`Dingdong-Inc/FreshRetailNet-50K`, CC BY 4.0, arXiv:2505.16319). Đây là doanh số chuẩn hóa của kho tiền phương thương mại điện tử, **không phải dữ liệu nhân sự và không phải cửa hàng vật lý 24/7**. Số SKU ghi là ~863–865 (dataset card ghi 865, arXiv ghi 863; mâu thuẫn chưa giải quyết).
- **Split.** Đã xác nhận bằng `dt.min()/max()` ([mô tả dữ liệu.md](mô%20tả%20dữ%20liệu.md) mục 2): train 2024-03-28 đến 2024-06-25 (90 ngày), eval 2024-06-26 đến 2024-07-02 (7 ngày). Nhu cầu lấy từ train; eval giữ lại làm tập đánh giá. Chưa tính WAPE/MAPE vì chưa có mô hình dự báo.
- **Nhu cầu ẩn.** Ô hết hàng (`hours_stock_status = 1`) được thay bằng trung bình doanh số cùng sản phẩm, cùng thứ, cùng giờ trên các ngày không hết hàng. Store 18: 90159 ô được thay; 1008 ô không có ngày không hết hàng để học nên giữ giá trị quan sát.
- **Quy đổi.** `r = max(sàn, ceil(alpha·D/p))`. Giả định của nhóm, đã duyệt (đặc tả D7–D9): `alpha = 1,0`, `p = 4,0` (giờ đỉnh cần 8 người với store 18), sàn 1 và 1. Giờ đêm được đặt bằng sàn đêm trước khi quy đổi ([đặc tả.md](đặc%20tả.md) mục 3).
- **Phạm vi.** Chỉ hỗ trợ bán lẻ / kho; chế độ tổng đài (Erlang A/C) đã bỏ (D18).

## 5. Kết quả benchmark

Mọi số ở đây chạy lại được; máy và phiên bản ở [benchmarks.md](benchmarks.md) đầu file.

**Curtois & Qu (2014), Instance1–5 (CP-SAT).** Với 8 worker và 120 giây: Instance1–3 đạt tối ưu công bố và được chứng minh; Instance4 đạt công bố nhưng chưa chứng minh; Instance5 còn cách công bố 5 đơn vị ([benchmarks.md](benchmarks.md) mục 1b). Với 1 worker chỉ Instance1 được chứng minh. Kết quả phụ thuộc số worker.

**Lịch theo nhân viên, 20/30/40 nhân viên, 3 seed.** 18/18 lần `OPTIMAL`, gap 0, coverage 1,0, 0 vi phạm, thời gian tối đa 31,5 s (1 worker) và 25,9 s (8 worker) ([benchmarks.md](benchmarks.md) mục 3). Nhu cầu sinh theo seed, không phải dữ liệu thật.

**Kịch bản cơ sở, store 18, 30 nhân viên, 3 seed.** 3/3 `OPTIMAL`, coverage 1,0, 0 vi phạm, 12–20 giây ([benchmarks.md](benchmarks.md) mục 4). Nhu cầu 468 giờ-người mỗi tuần trên sức chứa 1440: kịch bản dư sức chứa.

**Kịch bản căng, store 18, 8 nhân viên, 3 seed.** Không đạt tối ưu trong 60 giây: `FEASIBLE`, gap 1,0, coverage 0,703, 139 giờ thiếu, 0 vi phạm cứng. Lịch vẫn hợp lệ; chất lượng chưa được chứng minh ([benchmarks.md](benchmarks.md) mục 4). Đây là giới hạn đã đo, không hạ ràng buộc.

## 6. So sánh solver

Trên mô hình tổng hợp có nghỉ ngầm, 3 instance (đều, đỉnh, đỉnh có ca cách đều): HiGHS và CP-SAT cùng `OPTIMAL` và cùng objective ở 10 và 60 giây, đều dưới 0,1 giây ([benchmarks.md](benchmarks.md) mục 2). Instance quá nhỏ để phân biệt hiệu năng. Không suy ra cho mô hình theo nhân viên (đoạn sau). Không trích số Mittelmann.

Trên mô hình theo nhân viên (10, 20, 30 nhân viên; 3 seed; 60 giây; 1 worker), HiGHS đối chiếu với CP-SAT ([benchmarks.md](benchmarks.md) mục 2b):

- Ở 20 và 30 nhân viên, cả hai chứng minh tầng thiếu người và tầng chi phí, cùng kết quả, thời gian 17–28 giây.
- Ở 10 nhân viên, nhu cầu vượt sức chứa nên khó hơn. CP-SAT không chứng minh được trong 60 giây; HiGHS chứng minh được 2 trên 3 seed.
- Khi cả hai có lời giải, thiếu người và chi phí khớp nhau.

Lõi sản phẩm vẫn là CP-SAT. Số ràng buộc của HiGHS lớn hơn đáng kể vì viết từng cặp nghỉ 24 giờ ([benchmarks.md](benchmarks.md) mục 2c).

### Integrality gap

Gap giữa nghiệm nới lỏng và nghiệm nguyên ([benchmarks.md](benchmarks.md) mục 7). Mô hình tổng hợp: 40% ở instance đều, 21% ở instance đỉnh, 0% ở instance ca cách đều. Mô hình theo nhân viên: tầng chi phí dưới 0,4%, tầng thiếu người 6–15%. Dual LP của mô hình tổng hợp vì vậy chỉ là xấp xỉ, đúng như nhãn trên giao diện.

### Mục tiêu có trọng số và lexicographic

Trọng số thiếu người đặt thấp hơn ngưỡng sẽ không xếp ai, vì một giờ-người phục vụ thêm không bù được chi phí một ca (khoảng 10 000 mỗi giờ). Với 12 nhân viên, trọng số 10⁵ đổi 9 giờ thiếu lấy tiết kiệm 4,5% chi phí ([benchmarks.md](benchmarks.md) mục 8). Lexicographic không cần chọn trọng số, nên không có nguy cơ mất độ phủ âm thầm, nhưng mỗi tầng phải giải riêng và chia thời gian.

## 6b. Tối ưu so với baseline greedy

Greedy (`engine/src/shiftopt/baseline.py`) là heuristic để so sánh: không báo `OPTIMAL`, và mọi lần gán đều được kiểm bằng validator. Trên ba store đã chọn (18, 84, 578), với 30 giây mỗi lượt CP-SAT, greedy thường thiếu người nhiều hơn. Chi phí thấp hơn của greedy vì vậy không phải lợi thế. Chỉ khi cùng số giờ thiếu (store 578 với nhu cầu tăng 10–30% hoặc khi bớt 5 người), CP-SAT rẻ hơn từ 0 đến 5,7%. Với báo nghỉ, `repair` đổi ít phân công hơn greedy chạy lại từ đầu (4–13 so với 16–52). Chi tiết và giới hạn: [benchmarks.md](benchmarks.md) mục 5.

## 6c. Đánh đổi chi phí và công bằng

Thứ tự mặc định đặt chi phí trước công bằng, nên lịch rẻ nhất có thể dồn ca đêm vào người lương thấp. Tham số `cost_tolerance_percent` (0–10%, mặc định 0, đặc tả D21) cho tầng chi phí tăng tối đa tỷ lệ đó so với tối ưu của nó, rồi thêm tầng chênh giờ làm sau chênh ca đêm ([model.md](model.md) mục 7). Trên dữ liệu sinh với lương lệch 100/120/150, 20 nhân viên, dung sai 2–10% kéo chênh ca đêm từ 6 xuống 1 và chênh giờ làm từ 48 xuống 24, chi phí tăng 2–10% ([benchmarks.md](benchmarks.md) mục 6). Mọi điểm chỉ `FEASIBLE` trong 60 giây, nên đây là xu hướng quan sát được, không phải tối ưu đã chứng minh. Giao diện What-if có quét dung sai với hai biểu đồ và bảng.

## 6d. Hỗ trợ vận hành

- **Xếp lại (repair) và báo nghỉ đột xuất** (đặc tả D20): khóa các ngày trước `from_day`, ghim ca, người vắng không được xếp; tầng "số ca thay đổi" ngay sau thiếu người. Tập ca bị khóa được validator kiểm trước, nên solver luôn có lời giải ([model.md](model.md) mục 6).
- **Gợi ý người thay:** thử từng người còn trống, chỉ giữ người không gây vi phạm, không gọi solver.
- **Cảnh báo trước khi giải:** năm điều kiện cần (không còn ngày làm, sức chứa dưới nhu cầu, không ca đêm, giờ tối thiểu không đạt được, ngân sách dưới chi phí phủ rẻ nhất). Không chặn nút Optimize.
- **Giải thích giờ thiếu:** với mỗi giờ thiếu, thử thêm một ca cho từng người rảnh, báo luật chặn. Khi tầng thiếu người `OPTIMAL` thì không ai còn xếp được ([model.md](model.md) mục 9).
- **Ngân sách tuần và giờ tối thiểu** (đặc tả D25, D26): ngân sách là trần cứng, ngân sách chặt làm tăng giờ thiếu chứ không làm mô hình vô nghiệm; giờ tối thiểu là mục tiêu mềm ([model.md](model.md) mục 8).
- **Nhãn kết quả cũ** (đặc tả D27): mỗi lượt lưu hash của ảnh chụp đầu vào; sửa hay xóa hồ sơ nhu cầu, mẫu ca, nhân viên sau khi giải thì lượt cũ hiện "Đầu vào đã đổi". Lượt không bị sửa.

## 7. Độ nhạy

- **Chi phí biên rời rạc** `z(r + e_t) − z(r)` cho 168 giờ, bằng giải lại. Đây là chi phí biên của mô hình nguyên, không phải shadow price. Kiểm bằng ví dụ tay (3 ca, nhu cầu 1, giờ 3 = 100 × 980).
- **Dual LP** từ bản relax của cùng mô hình, luôn gắn nhãn xấp xỉ, integrality gap có thể lớn. Dual không bao giờ lấy từ CP-SAT hoặc MIP.
- **Quét λ** trong {0,8; …; 1,3}: `z(λ)` không giảm. Điểm không `OPTIMAL` được đánh dấu `proven = False`.
- **Quét giả định quy đổi** (`alpha`, `p`, sàn): chạy lại được qua API `staffing-sweep` và trên UI (what-if).
- **So với baseline greedy** và **quét dung sai chi phí**: hai phân tích nữa trên trang What-if (mục 6b, 6c).
- Hệ số khuyến mãi 1,43 là gợi ý từ bài báo (v5), không phải ước lượng của nhóm; ngày lễ và mưa không có hệ số mặc định.

## 8. Nghiệm thu

Đối chiếu từng dòng của CLAUDE.md mục 13. Tóm tắt:

- **Đạt:** ràng buộc cứng; hiệu năng 20–40 nhân viên; pháp lý (kiểm bằng test); tái lập; coverage engine 98,13% (236 test).
- **Đạt có điều kiện:** coverage 98% ở kịch bản cơ sở (kịch bản dư sức chứa); so sánh solver trên cả mô hình tổng hợp và mô hình theo nhân viên, trong phạm vi 10–30 nhân viên, 3 seed, 60 giây (đặc tả D12).
- **Chờ:** độ nhạy và UI cần người duyệt trên trình duyệt. Smoke flow trên Compose chạy đạt.

Backend có 168 test: 131 unit, 37 integration chạy trên MySQL 8.4.10 trong CI, không skip. Migration head `8c4a2e9d6f31` khớp model (`alembic check` sạch).

## 9. Hạn chế

- Kịch bản cơ sở chỉ đo store 18 (3 seed); so với greedy đo 3 store. Không suy ra cho store khác.
- Coverage khi thiếu người chỉ đo ở một kịch bản; solver không chứng minh tối ưu trong 60 giây khi thiếu nhân viên.
- Tuần quấn vòng: ca Chủ nhật nối với thứ Hai cùng tuần, không nối với tuần trước (đặc tả D22, chưa làm).
- Giờ tối thiểu theo hợp đồng là mềm: lịch có thể để một người dưới mức tối thiểu.
- Quét dung sai chi phí mới đo trên dữ liệu sinh, mọi điểm `FEASIBLE`.
- Giải thích giờ thiếu chỉ thử thêm một ca cho một người, không xét đổi chéo.
- Nghỉ giữa giờ xấp xỉ bằng một giờ phủ, bảo thủ.
- Nghị định 145/2020 chưa đối chiếu văn bản gốc.
- Nhu cầu là doanh số kho tiền phương, không phải nhu cầu nhân sự; mọi quy đổi là giả định của nhóm.
- Chưa có chấm công, nên không đo adherence. Không hỗ trợ tổng đài.
- Không có dự báo; không tính WAPE/MAPE.
- Giết tiến trình con khi quá hạn chưa làm; CP-SAT tự dừng theo time limit.

## 10. Lệnh tái chạy

```
cd engine
uv run --locked pytest -q --cov=shiftopt --cov-fail-under=80
uv run --locked python -u benchmarks/run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60 --workers 1
uv run --locked python benchmarks/compare_solvers.py
uv run --locked python -u benchmarks/run_roster_scale.py --solver both --sizes 10 20 30 --seeds 0 1 2 --time-limit 60 --workers 1
uv run --locked python -u -m benchmarks.integrality_gap
uv run --locked python -u -m benchmarks.weighted_vs_lexicographic
uv run --locked python -u -m benchmarks.cost_tolerance

cd ../backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 30 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 8 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
```


## Phụ lục: nguồn UI/UX tham chiếu

Gộp từ file riêng ngày 2026-11-08 để giữ ngày xem và giấy phép.
Theo CLAUDE.md mục 8.3: mỗi pattern UI lấy từ một nguồn có thật, đã mở xem trực tiếp. Ở mọi màn hình, phần nhìn (màu, font, khung blueprint, nút) theo trang chủ (`frontend/src/features/home/`); bảng dưới chỉ ghi phần bố cục và hành vi lấy từ đâu.

Không chép mã từ nguồn nào dưới đây. Mọi thứ được viết lại bằng token và class của trang chủ.

### Nguồn

| # | Nguồn | URL | Ngày xem / commit | Giấy phép | Lấy gì |
|---|---|---|---|---|---|
| R1 | Timefold Quickstarts, employee scheduling (Java, Quarkus) | https://github.com/TimefoldAI/timefold-quickstarts/tree/stable/use-cases/employee-scheduling (`src/main/resources/META-INF/resources/index.html`, `app.js`) | 2026-10-28, commit `76993a3` | Apache-2.0 | Thanh công cụ Solve / Stop kèm điểm số cạnh nút; xem lịch theo nhân viên (mỗi hàng một nhân viên); tô nền các ngày không làm được / không muốn làm trên hàng của nhân viên đó; poll lại lịch theo chu kỳ khi solver đang chạy; hộp "score analysis" liệt kê vi phạm theo từng ràng buộc |
| R2 | GOV.UK Design System, Error summary | https://design-system.service.gov.uk/components/error-summary/ | 2026-10-28 | Nội dung OGL v3.0 (không lấy mã) | Hộp "There is a problem" đầu form, mỗi lỗi là link tới ô lỗi, focus chuyển vào hộp; thông điệp lỗi ngay cạnh ô, nối bằng `aria-describedby` |
| R3 | WAI-ARIA APG, Grid pattern | https://github.com/w3c/aria-practices/blob/main/content/patterns/grid/grid-pattern.html (trang w3.org trả 403 với công cụ đọc, đọc bản nguồn trên GitHub) | 2026-10-28 | W3C Document License | Lưới 7 × 24 nhu cầu: phím mũi tên di chuyển giữa ô, Home/End đầu/cuối hàng, mỗi ô có nhãn riêng |
| R4 | WAI-ARIA APG, Slider pattern | https://github.com/w3c/aria-practices/blob/main/content/patterns/slider/slider-pattern.html | 2026-10-28 | W3C Document License | Thanh trượt lambda: nhãn hiển thị, `aria-valuetext` đọc giá trị có nghĩa ("1.1x demand") thay vì chỉ số thứ tự |
| R5 | WAI-ARIA APG, Dialog (modal) pattern | https://github.com/w3c/aria-practices/blob/main/content/patterns/dialog-modal/dialog-modal-pattern.html | 2026-10-28 | W3C Document License | Modal: focus vào trong khi mở, Tab không thoát ra ngoài, Escape đóng, trả focus về nút mở; hộp xác nhận xóa focus vào lựa chọn ít phá hủy nhất |
| R6 | WAI-ARIA APG, Tabs pattern | https://github.com/w3c/aria-practices/blob/main/content/patterns/tabs/tabs-pattern.html | 2026-10-28 | W3C Document License | Đối chiếu khi chọn dạng điều khiển chọn ngày của coverage chart. Giữ dạng nút bật/tắt (`aria-pressed`) như trang chủ vì nút đổi dữ liệu của một biểu đồ, không đổi panel |
| R7 | Carbon Design System, Data table usage | https://carbondesignsystem.com/components/data-table/usage/ | 2026-10-28 | Apache-2.0 (repo carbon-design-system/carbon) | Thanh công cụ trên bảng (tối đa vài hành động), hành động theo hàng hiển thị dạng nút khi ít hơn ba, hover trên hàng để dò |
| R8 | Carbon Design System, Empty states pattern | https://carbondesignsystem.com/patterns/empty-states-pattern/ | 2026-10-28 | Apache-2.0 | Trạng thái rỗng thay chỗ bảng: tiêu đề tích cực, một câu nói bước tiếp theo, một hành động chính; trạng thái lỗi nói nguyên nhân và cách xử lý |
| R9 | Carbon Design System, Notification usage | https://carbondesignsystem.com/components/notification/usage/ | 2026-10-28 | Apache-2.0 | Thông báo inline ở đầu vùng nội dung hoặc ngay trên nút gửi của form; mỗi trạng thái có biểu tượng riêng, không chỉ dựa vào màu |
| R10 | Carbon Design System, Loading usage | https://carbondesignsystem.com/components/loading/usage/ | 2026-10-28 | Apache-2.0 | Chờ cục bộ cạnh hành động, nhãn trạng thái ngắn, không đặt nhiều chỉ báo cùng lúc |
| R11 | Cal-Heatmap | https://github.com/wa0x6e/cal-heatmap (README và ảnh ví dụ) | 2026-10-28, commit `279e4ee` | MIT | Heatmap dạng lưới lịch: mỗi ô một khoảng thời gian, chú giải thang ngưỡng bên dưới, tooltip theo ô |
| R12 | web.dev, bài về `prefers-color-scheme` (tác giả ghi trên trang: Thomas Steiner; trang không hiện tiêu đề và ngày trong phần đọc được) | https://web.dev/articles/prefers-color-scheme | 2026-11-07 | Trang không ghi giấy phép trong phần đọc được; không lấy mã | Mẫu "theo tín hiệu của trình duyệt trước, cho người dùng ghi đè sau"; khai báo `color-scheme` để ô nhập và thanh cuộn của trình duyệt cũng tối |
| R13 | MDN, thuộc tính CSS `color-scheme` | https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme | 2026-11-07, trang ghi sửa lần cuối 2026-07-21 | Creative Commons (chân trang không nêu rõ loại nào); không lấy mã | `color-scheme: dark` đổi màu nền canvas, thanh cuộn và mặc định của ô nhập; kiểm tra tín hiệu hệ thống bằng `prefers-color-scheme` |
| R14 | Timefold quickstarts, employee scheduling (`use-cases/employee-scheduling`) | https://github.com/TimefoldAI/timefold-quickstarts (mục use-cases/employee-scheduling) | 2026-11-08 | Apache-2.0 (ghi trên trang repo); không lấy mã | Ý tưởng pinning và replanning từ chủ đề bài toán: giữ phần đã chạy, xếp lại phần còn lại. README của mục không đọc được qua công cụ, nên bố cục lưới lấy từ dự án ShiftOpt (`ScheduleGrid`), không từ mẫu Timefold |
| R15 | Deputy, Find replacement (trợ giúp quản lý) | https://help.deputy.com/hc/en-au/articles/4688987465743 | 2026-11-08 | Trang trả 403 khi mở; không dùng làm nguồn | Không dùng. Thay bằng R17 |
| R16 | Timefold docs, Employee Shift Scheduling, "Real-time planning" | https://docs.timefold.ai/employee-shift-scheduling/latest/real-time-planning | 2026-11-08 | Không ghi giấy phép trong phần đọc được; không lấy mã | Xếp lại: cập nhật đầu vào (người vắng) rồi giải lại; ca được ghim giữ nguyên, ca khác có thể đổi người; báo mức thay đổi (tỷ lệ ca và nhân viên bị ảnh hưởng) |
| R17 | Connecteam, "Shift swap or shift replacement" (trợ giúp) | https://help.connecteam.com/en/articles/16644414-let-s-settle-this-once-and-for-all-shift-swap-or-shift-replacement | 2026-11-08 | Không ghi giấy phép trong phần đọc được; không lấy mã | Gợi ý người thay: tách thay ca (một chiều) và đổi ca (hai chiều); ứng viên được cảnh báo trùng ca hoặc không khả dụng; quản lý duyệt trước khi có hiệu lực. Trang không nói quản lý thấy gì trong danh sách, nên chỉ lấy hành vi chung |

### Bố cục lấy từ chính trang chủ

Màn hình Schedule (kết quả một run) và What-if (đường cong z(lambda)) dựng lại hai panel minh họa của trang chủ, dùng chung token và hằng số khoảng cách: `WorkspacePreview` (header có chấm accent, dải KPI bốn ô, khối "Weekly roster" với ô ca một chữ cái, khối "Staffing coverage" với tab ngày, cột nhân sự và dòng meta solver) và `ScenarioPanel` ("Demand vs. staffing": cột theo giờ, thanh lambda, đường cong chi phí kèm hai số và ghi chú). Nguồn là mã của dự án (`frontend/src/features/home/components/WorkspacePreview.tsx`, `ScenarioPanel.tsx`, `home.css`), không phải bên thứ ba. Khác trang chủ: lịch hiển thị mọi nhân viên (cuộn dọc), dòng phụ dưới tên là số ca thay vì loại hợp đồng, vì dữ liệu hợp đồng chưa có; mỗi điểm sweep không tối ưu vẫn được đánh dấu theo nguyên tắc 5.

### Màn hình → nguồn

| Màn hình ShiftOpt | Nguồn |
|---|---|
| Khung app (header, nav) | Trang chủ; R1 (thanh điều hướng trên, vùng làm việc bên dưới) |
| Nút chuyển giao diện sáng/tối (header của trang chủ và khung app) | R12, R13 (hành vi: theo hệ thống, người dùng ghi đè, lưu lại). Nhãn `aria-label` và biểu tượng mặt trời/trăng do nhóm tự đặt, các nguồn trên không bàn về nhãn của nút |
| Demand (lưới 7 × 24, CSV, ingest file doanh số) | R3, R2, R5, R8 |
| Employees, Shift templates | R7, R5, R2, R8, R1 (ngày không làm được / không muốn làm) |
| Schedule (Optimize, trạng thái, lịch, coverage, chi phí) | R1, R10, R9, R6 |
| Compliance (danh sách vi phạm, sửa tay) | R1 (score analysis), R2, R9 |
| What-if (lambda, đường cong, heatmap chi phí biên, so sánh kịch bản) | R4, R11, R9 |
| Schedule: Xếp lại (repair) và đánh dấu ô đổi | R14, R16, R1, R9 (khóa ngày dùng nhãn chữ, không chỉ màu) |
| Schedule / Compliance: Gợi ý người thay | R17, R9, R10 |
| Schedule, What-if: cảnh báo trước khi giải (G1) | R9 (thông báo inline ngay trên nút gửi, có biểu tượng). **Chưa có nguồn thứ hai đã mở** (plan D3) |
| Schedule: bảng "Vì sao còn giờ thiếu người" (G2) | R1 (score analysis liệt kê vi phạm theo ràng buộc), R7 (bảng). Nhãn luật dùng lại của khung Tuân thủ |
| Schedule: nhãn "Đầu vào đã đổi sau lượt này" (G4) | R9. **Chưa có nguồn thứ hai đã mở** (plan D3) |
| What-if: quét dung sai chi phí (F) | Bố cục của `SweepView` trong dự án (đường cong, điểm rỗng khi chưa chứng minh), R7 (bảng dữ liệu). **Chưa có nguồn bên ngoài cho biểu đồ đánh đổi** (plan D3) |
