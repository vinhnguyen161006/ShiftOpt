# Đặc tả ShiftOpt

**Trạng thái:** bản nháp. Claude soạn theo ủy quyền của người dùng. Nhóm chưa duyệt. Mọi quyết định ở mục 3 có thể đổi; khi đổi phải sửa config hoặc `LaborRules`, cập nhật mục này và chạy lại benchmark.

**Nguồn luật.** Điều 98, 105, 106, 109, 110, 111 đã đối chiếu với VBHN 125/VBHN-VPQH (2025) (mục 4). Nghị định 145/2020 chưa đối chiếu văn bản gốc.

## 1. Phạm vi

Trong phạm vi bản đầu (CLAUDE.md mục 13–14):
- Một địa điểm, một loại kỹ năng; lịch tuần 7×24; một chế độ nhu cầu trên một lần chạy.
- Một nguồn nhu cầu: file doanh số ingest trên web (CSV hoặc parquet), suy ra số người theo giờ. FreshRetailNet là dữ liệu mẫu cho demo. Không hỗ trợ tổng đài (D18).
- Tối ưu lịch theo nhân viên (CP-SAT), validator độc lập, KPI, độ nhạy (quét λ, chi phí biên, dual LP xấp xỉ, quét giả định quy đổi).
- Giao diện: nhập nhu cầu, mẫu ca, nhân viên, Optimize, lịch, cảnh báo tuân thủ, sửa tay, What-if, xuất CSV.

Ngoài phạm vi: đa địa điểm, ma trận kỹ năng, stochastic, robust, nhiều tuần, Gantt theo giờ, dự báo, PDF, xác thực, chấm công, Redis/Celery/WebSocket, Timefold, Gurobi bắt buộc.

## 2. Yêu cầu chức năng

| Mã | Yêu cầu | Kiểm chứng |
|---|---|---|
| FR-1 | Nhập nhu cầu bằng lưới 168 ô, CSV, hoặc ingest file doanh số (CSV/parquet, người dùng chọn cột trên form). Ô là số nguyên không âm, tối đa 1000. | `test_csv_import.py`, `test_sales_ingest.py`, `test_demand_schema.py` |
| FR-2 | Quy đổi nhu cầu ra số người: tuyến tính `r = max(floor, ceil(alpha·D/p))`. Mọi tham số hiện trên UI và trong metadata. | `test_kpi_and_staffing.py`, `test_dataset_loader.py` |
| FR-3 | Mẫu ca (giờ bắt đầu, độ dài). Nhân viên có giờ tối đa riêng (≤ luật), ngày không làm được, ngày mong muốn nghỉ. | `test_validation.py`, `test_roster_cpsat.py` |
| FR-4 | Optimize tạo một lượt giải bất biến, trả `job_id` ngay, poll theo `job_id`. Lưu đủ tái lập (nguyên tắc 10). | `test_schedules_flow.py` (MySQL) |
| FR-5 | Mọi nghiệm qua validator. Vi phạm cứng > 0 thì lượt đánh dấu `failed`, không hiện như thành công. | `test_validation.py`, smoke flow |
| FR-6 | Sửa tay tạo lượt mới, chạy lại validator, lịch gốc không đổi. | `test_crud_api` / smoke flow |
| FR-7 | KPI: coverage, giờ thiếu/thừa, hiệu suất, chi phí, phụ cấp đêm, độ lệch ca đêm và cuối tuần. Xuất CSV. | `test_kpi_and_staffing.py`, `test_schedule_views.py` |
| FR-8 | Độ nhạy: quét λ ∈ [0,8; 1,3], chi phí biên 168 giờ bằng giải lại, dual LP có nhãn xấp xỉ, quét giả định quy đổi. | `test_sensitivity.py`, `test_worker.py` |

## 3. Quyết định đã chốt (bản nháp)

Người chốt: Claude theo ủy quyền. Chờ nhóm xác nhận. Lý do ghi cạnh mỗi dòng.

| # | Câu hỏi | Giá trị | Lý do |
|---|---|---|---|
| D1 | Ca đêm tính theo luật hay hợp đồng | 22h–06h theo Đ.106 cho mọi nhân viên | Luật là sàn; hợp đồng riêng ngoài phạm vi |
| D2 | "Ngày" bắt đầu lúc mấy giờ | 00:00; thứ Hai là ngày 0; phần ca qua đêm tính vào ngày sau | Khớp `time_grid.py` và validator |
| D3 | `K` ngày làm liên tiếp tối đa | 6 | Mỗi cửa sổ 7 ngày có ít nhất một ngày nghỉ |
| D4 | 48 hay 40 giờ/tuần | 48 cho kịch bản cơ sở; 40 là kịch bản what-if | Luật cho phép 48 |
| D5 | Đ.110 áp cho cặp ca nào | Mọi cặp ca liên tiếp, công thức tổng quát `24 + σ' − (σ + L) ≥ 12` | Cách hiểu chặt, không bao giờ sai luật |
| D6 | Nghỉ giữa giờ (Đ.109) | Ca từ 6 giờ có nghỉ 30 phút (ca đêm 45 phút), tính là mất một giờ phủ | Bảo thủ. Ngưỡng 6 giờ và thời lượng khớp Đ.109 (mục 4) |
| D7 | `alpha` | 1,0 | Không có hệ số chuẩn hóa công khai; gộp vào `p` |
| D8 | `p` (đơn vị doanh số chuẩn hóa mỗi người mỗi giờ) | 4,0 cho kịch bản cơ sở (truyền tường minh) | Với store 18, giờ đỉnh cần 8 người. Tải đỉnh 28,3. `DEFAULT_PRODUCTIVITY` trong code vẫn là 1,0; chưa đổi để không đổi hành vi smoke và test, cần đổi kèm chạy lại test |
| D9 | Sàn `min_staff`, `night_min_staff` | 1 và 1 | Nguyên tắc 7 gợi ý 1–2 |
| D10 | Doanh thu cho tỷ lệ chi phí lao động | Không mặc định; nhập trên UI | Không có dữ liệu doanh thu thật |
| D11 | Trọng số `M_u`, `λ_F` | Không dùng trọng số; giải lexicographic 4 tầng | Tránh chọn `M` tùy tiện (CLAUDE.md 5.2) |
| D12 | So sánh CP-SAT với HiGHS | Trên mô hình tổng hợp có nghỉ ngầm, không trên mô hình theo nhân viên | Mô hình theo nhân viên chỉ có CP-SAT; sai lệch nghiệm thu dòng 4 |
| D13 | Kịch bản cơ sở | Store 18, D7–D9, 3 ca 0/8/16 h, 30 nhân viên, 48 giờ | Dữ liệu thật, không sinh ngẫu nhiên |
| D14 | Dataset tổng đài công khai | Bỏ, thay bằng D18 | — |
| D15 | Giết tiến trình con khi quá hạn | Không làm; ghi là giới hạn đã biết | CP-SAT tự dừng theo time limit |
| D16 | Hợp đồng nhân viên | Chỉ thêm giờ tối đa riêng; không thêm loại hợp đồng | Đủ cho bán thời gian; MVP mục 8.1 |
| D17 | Báo cáo nghiên cứu nền | Không có trong repo; đặc tả thay vai trò nguồn | File không tồn tại |
| D18 | Chế độ tổng đài (Erlang A/C) | Bỏ khỏi sản phẩm (người dùng quyết định 2026-11-07) | Nhóm không hỗ trợ tổng đài; giữ một chế độ bán lẻ |
| D19 | Nguồn nhu cầu | Ingest file doanh số tổng quát, không gắn FreshRetailNet. Người dùng ingest file (CSV hoặc parquet) và chọn cột trên form; hệ thống gợi ý cột theo tên. FreshRetailNet là dữ liệu mẫu cho demo | Yêu cầu của người dùng: chỉ là ingest doanh số rồi suy ra nhu cầu; dữ liệu khác FreshRetailNet cũng phải chạy. Hồ sơ lưu tuần tải để quét giả định không cần file gốc |
| D20 | Xếp lại lịch (repair) | Lịch gốc là bất biến. Repair tạo lượt mới: ngày trước `from_day` và ca ghim là cố định, người vắng không được xếp; tầng "thay đổi so với gốc" đặt sau thiếu người và trước chi phí. Gợi ý người thay chỉ dùng validator, không gọi solver | Giữ ổn định lịch đã công bố (nghiệp vụ người báo ốm); kiểm tra khả thi bằng tính đơn điệu của ràng buộc cứng, không để solver báo INFEASIBLE |

## Phiếu duyệt

Người duyệt: ______________ · Ngày duyệt: ______________ · Chữ ký: ______________

Đánh dấu "Đồng ý" hoặc ghi "Sửa" và nội dung sửa. Mọi "Sửa" phải đổi `LaborRules` hoặc config, rồi chạy lại benchmark (mục 3).

| Mã | Quyết định | Đồng ý / Sửa | Ghi chú |
|---|---|---|---|
| D1 | Ca đêm tính theo luật hay hợp đồng | | |
| D2 | "Ngày" bắt đầu lúc mấy giờ | | |
| D3 | `K` ngày làm liên tiếp tối đa | | |
| D4 | 48 hay 40 giờ/tuần | | |
| D5 | Đ.110 áp cho cặp ca nào | | |
| D6 | Nghỉ giữa giờ (Đ.109) | | |
| D7 | `alpha` | | |
| D8 | `p` (đơn vị doanh số chuẩn hóa mỗi người mỗi giờ) | | |
| D9 | Sàn `min_staff`, `night_min_staff` | | |
| D10 | Doanh thu cho tỷ lệ chi phí lao động | | |
| D11 | Trọng số `M_u`, `λ_F` | | |
| D12 | So sánh CP-SAT với HiGHS | | |
| D13 | Kịch bản cơ sở | | |
| D14 | Dataset tổng đài công khai | | |
| D15 | Giết tiến trình con khi quá hạn | | |
| D16 | Hợp đồng nhân viên | | |
| D17 | Báo cáo nghiên cứu nền | | |
| D18 | Chế độ tổng đài (Erlang A/C) | | |
| D19 | Nguồn nhu cầu | | |
| D20 | Xếp lại lịch (repair) | | |

**Điểm code chặt hơn luật (cần nhóm xác nhận có chủ đích):**

- Đ.105 khoản 2: code chỉ cho 8 giờ mỗi ngày, luật cho tới 10 giờ khi quy định theo tuần.
- Đ.109 khoản 1: code mất một giờ phủ cho mọi ca cần nghỉ, luật chỉ yêu cầu 30 hoặc 45 phút.
- Đ.111 khoản 1: code không có ngoại lệ bình quân 04 ngày nghỉ mỗi tháng.

**Việc còn mở để nhóm quyết:** kịch bản cơ sở D13; sai lệch CLAUDE mục 13 dòng 4 (so sánh solver); dùng Playwright (CLAUDE mục 10); F, H, I (mỗi mục đổi đặc tả).

## 4. Ràng buộc pháp lý

Mọi hằng nằm trong `LaborRules` (`engine/src/shiftopt/constraints/labor_law_vn.py`). Mô hình và validator cùng đọc từ đó.

**Nguồn đã đối chiếu:** Bộ luật Lao động 45/2019/QH14, bản hợp nhất VBHN 125/VBHN-VPQH (2025) của Văn phòng Quốc hội, đã gồm sửa đổi theo Luật 71/2025/QH15 (hiệu lực từ 01/01/2026). PDF tải từ `static.luatvietnam.vn` ngày 2026-11-08 và trích bằng `pdftotext`. Bản trích bị lỗi font nên dấu tiếng Việt trong cột "Nội dung" được chép lại theo ngữ cảnh, không phải chép ký tự gốc; trước khi nộp, đối chiếu lại với PDF của Văn phòng Quốc hội.

**Chưa đối chiếu:** Nghị định 145/2020/NĐ-CP (Điều 64, nghỉ giữa giờ). Chỉ có nguồn thứ cấp, xem ghi chú dưới bảng.

| Điều | Nội dung (trích, rút gọn) | Giá trị trong code | Kết quả |
|---|---|---|---|
| 98 khoản 2 | Làm việc vào ban đêm được trả thêm ít nhất bằng 30% tiền lương tính theo giờ hoặc theo sản phẩm của ngày làm việc bình thường | 30% | Khớp |
| 105 khoản 1 | Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần | 8 giờ/ngày; 48 giờ/tuần | Khớp |
| 105 khoản 2 | Khi quy định theo tuần: không quá 10 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần | Chỉ 8 giờ/ngày | Chặt hơn luật, có chủ đích |
| 106 | Giờ làm việc ban đêm được tính từ 22 giờ đến 06 giờ sáng ngày hôm sau | 22; 6 | Khớp |
| 109 khoản 1 | Làm việc theo thời giờ Điều 105 từ 06 giờ trở lên trong một ngày thì được nghỉ giữa giờ ít nhất 30 phút liên tục; làm việc ban đêm thì ít nhất 45 phút liên tục. Ca liên tục từ 06 giờ trở lên thì thời gian nghỉ giữa giờ được tính vào giờ làm việc | Ngưỡng 6 giờ; 30 phút; 45 phút ban đêm | Khớp về ngưỡng và thời lượng. Code mất một giờ phủ cho mọi ca cần nghỉ (chặt hơn, có chủ đích). Ca một ngày một người nên "theo ngày" và "theo ca" trùng nhau |
| 110 | Làm việc theo ca được nghỉ ít nhất 12 giờ trước khi chuyển sang ca làm việc khác | 12 | Khớp |
| 111 khoản 1 | Mỗi tuần được nghỉ ít nhất 24 giờ liên tục. Trường hợp đặc biệt không nghỉ hằng tuần được: bình quân ít nhất 04 ngày nghỉ mỗi tháng | 24 | Chặt hơn luật: code không có ngoại lệ 04 ngày/tháng |

Đ.98 khoản 1 (hệ số 150%, 200%, 300% làm thêm) và Đ.107 chưa dùng trong mô hình bản đầu (mục 9, mức mở rộng).

**Nghị định 145/2020/NĐ-CP, Điều 64 (chưa đối chiếu, nguồn thứ cấp):** nguồn tra được nêu thêm điều kiện làm ít nhất 03 giờ ban đêm để áp mức 45 phút. Nếu đúng, code vẫn áp 45 phút cho ca có giờ đêm và mất một giờ phủ, nên vẫn chặt hơn; không cần đổi code. Vẫn cần đối chiếu với văn bản gốc.

Bẫy Điều 111 với ca qua đêm: validator tính khoảng nghỉ liên tục trên trục giờ, không chỉ đếm ngày nghỉ.
## 5. Tiêu chí nghiệm thu

Lấy từ CLAUDE.md mục 13. Kết quả đo nằm trong [benchmarks.md](benchmarks.md).

| Tiêu chí | Ngưỡng |
|---|---|
| Ràng buộc cứng | 0 vi phạm trên mọi nghiệm |
| Phủ nhu cầu | Coverage ≥ 98% ở kịch bản cơ sở |
| Hiệu năng | 20–40 nhân viên, giải ≤ 60 giây, gap ≤ 1% |
| So sánh solver | CP-SAT và HiGHS trên cùng instance, có bảng |
| Độ nhạy | `z(λ)` cho λ ∈ [0,8; 1,3]; heatmap chi phí biên theo giờ |
| Pháp lý | Cặp 14h–22h → 06h–14h bị cấm; ca đêm rồi nghỉ 24 giờ không vi phạm Đ.111 |
| Tái lập | Cùng instance, seed, `num_workers = 1` → cùng objective |
| Test | Coverage `engine/` ≥ 80% |
| UI | Nhập nhu cầu → Optimize → lịch, coverage, cảnh báo, chi phí; kéo λ |

## 6. Mô hình và lệch có chủ đích

- Nghỉ giữa ca là giảm một giờ phủ (xấp xỉ bảo thủ, `docs/model.md` mục 1b).
- Thứ tự tối ưu là lexicographic: thiếu người, chi phí, chênh ca đêm, sở thích. Không dùng trọng số phạt.
- Công bằng: model tối thiểu hóa max − min (tuyến tính); KPI báo độ lệch chuẩn (mô tả). Hai đại lượng khác nhau.
- Phá đối xứng và phân rã hai pha đều tắt mặc định (đo trên benchmark: không nhanh hơn trên seed đã đo).

## 7. Giới hạn đã biết

- Kịch bản cơ sở (store 18, 30 nhân viên) dư sức chứa: 468 giờ-người nhu cầu trên 1440 sức chứa. Đạt 98% không chứng minh được khi thiếu người.
- Kịch bản căng (8 nhân viên, sức chứa 384 < 468) không đạt tối ưu trong 60 giây: coverage 70,3%, gap 100%. Kết quả là `FEASIBLE`, không được gọi là tối ưu.
- Chỉ đo một store, 3 seed, 1 và 8 worker; không suy ra cho store khác.
- Nghị định 145/2020 chưa đối chiếu văn bản gốc. Các điều luật còn lại ở mục 4 đã đối chiếu.
- Chưa có chấm công; không đo adherence.
