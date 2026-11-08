# Đặc tả ShiftOpt

**Trạng thái:** bản nháp. Claude soạn theo ủy quyền của người dùng (WORKLOG 0.1, 0.2). Nhóm chưa duyệt. Mọi quyết định ở mục 3 có thể đổi; khi đổi phải sửa config hoặc `LaborRules`, cập nhật mục này và chạy lại benchmark.

**Nguồn luật chưa đối chiếu nguyên văn.** Tải toàn văn 45/2019/QH14 và NĐ 145/2020 không được (trang trả HTTP 403; tìm kiếm chỉ cho tóm tắt thứ cấp). Mục 4 ghi rõ từng điều đã đối chiếu tới đâu. Trước khi nộp báo cáo, phải đối chiếu với văn bản chính thức.

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
| D6 | Nghỉ giữa giờ (Đ.109) | Ca từ 6 giờ có nghỉ 30 phút (ca đêm 45 phút), tính là mất một giờ phủ | Bảo thủ. Ngưỡng 6 giờ chưa đối chiếu nguyên văn (xem mục 4) |
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

## 4. Ràng buộc pháp lý

Mọi hằng nằm trong `LaborRules` (`engine/src/shiftopt/constraints/labor_law_vn.py`). Mô hình và validator cùng đọc từ đó.

| Điều | Nội dung dùng trong code | Mặc định | Trạng thái đối chiếu |
|---|---|---|---|
| 98 khoản 2 | Phụ cấp ca đêm tối thiểu 30% | 30% | Chưa đối chiếu nguyên văn |
| 105 | ≤ 8 giờ/ngày; ≤ 48 giờ/tuần | 8; 48 | Chưa đối chiếu nguyên văn |
| 106 | Khung đêm 22h–06h | 22; 6 | Chưa đối chiếu nguyên văn (CLAUDE.md ghi là Đ.106) |
| 109 | Nghỉ giữa giờ 30 phút; 45 phút ca đêm; ca từ 6 giờ | 30; 45; 6 | Ngưỡng 6 giờ chưa xác minh. Một nguồn thứ cấp nêu ngưỡng 6 giờ liên quan đến việc nghỉ có được tính vào giờ làm |
| 110 | Nghỉ ≥ 12 giờ giữa hai ca | 12 | Chưa đối chiếu nguyên văn |
| 111 | Nghỉ ≥ 24 giờ liên tục mỗi tuần | 24 | Chưa đối chiếu nguyên văn |

Nguồn đã tra (thứ cấp): [Điều kiện để thời gian nghỉ giữa giờ được tính vào thời giờ làm việc](https://thuvienphapluat.vn/lao-dong-tien-luong/dieu-kien-de-thoi-gian-nghi-giua-gio-duoc-tinh-vao-thoi-gio-lam-viec-la-gi-35337.html); [Bố trí ca làm việc như thế nào cho đúng luật?](https://thuvienphapluat.vn/lao-dong-tien-luong/bo-tri-ca-lam-viec-nhu-the-nao-cho-dung-luat-12112.html).

Bẫy Đ.111 với ca qua đêm: validator tính khoảng nghỉ liên tục trên trục giờ, không chỉ đếm ngày nghỉ.

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
- Ngưỡng Đ.109 (6 giờ) và các điều luật ở mục 4 chưa đối chiếu nguyên văn.
- Chưa có chấm công; không đo adherence.
