# Đặc tả ShiftOpt

**Trạng thái:** đã duyệt ngày 2026-11-08. Người dùng (Vinh) ủy quyền cho Claude quyết định mọi mục ở mục 3 và phiếu duyệt; kết quả ghi ở phiếu duyệt. Bổ sung ngày 2026-11-09: sửa D16, thêm D25–D28, theo câu trả lời của người dùng. Các thành viên khác của nhóm chưa xem bản này: ai không đồng ý thì sửa dòng tương ứng ở phiếu. Mọi quyết định ở mục 3 có thể đổi; khi đổi phải sửa config hoặc `LaborRules`, cập nhật mục này và chạy lại benchmark.

**Chưa đóng:** Nghị định 145/2020 chưa đối chiếu văn bản gốc (mục 4). Điểm này không chặn duyệt vì code đang chặt hơn nguồn thứ cấp.

**Nguồn luật.** Điều 98, 105, 106, 109, 110, 111 đã đối chiếu với VBHN 125/VBHN-VPQH (2025) (mục 4). Nghị định 145/2020 chưa đối chiếu văn bản gốc.

## 1. Phạm vi

Trong phạm vi bản đầu (CLAUDE.md mục 13–14):
- Một địa điểm, một loại kỹ năng; lịch tuần 7×24; một chế độ nhu cầu trên một lần chạy.
- Một nguồn nhu cầu: file doanh số ingest trên web (CSV hoặc parquet), suy ra số người theo giờ. FreshRetailNet là dữ liệu mẫu cho demo. Không hỗ trợ tổng đài (D18).
- Tối ưu lịch theo nhân viên (CP-SAT), validator độc lập, KPI, độ nhạy (quét λ, chi phí biên, dual LP xấp xỉ, quét giả định quy đổi, so với baseline greedy, quét dung sai chi phí).
- Giao diện: nhập nhu cầu, mẫu ca, nhân viên, Optimize, cảnh báo trước khi giải, lịch, cảnh báo tuân thủ, giải thích giờ thiếu, nhãn đầu vào đã đổi, sửa tay, xếp lại và báo nghỉ, gợi ý người thay, What-if, xuất CSV.

Ngoài phạm vi: đa địa điểm, ma trận kỹ năng, stochastic, robust, Gantt theo giờ, PDF, xác thực, chấm công, Redis/Celery/WebSocket, Timefold, Gurobi bắt buộc.

Mở rộng được phép làm có điều kiện (D21–D23): đánh đổi chi phí và công bằng (D21, **đã làm** 2026-11-09), tuần nối với tuần trước (D22, chưa làm), dự báo nhu cầu bằng baseline mùa vụ (D23, chưa làm). Mục chưa làm thì không được ghi vào báo cáo như đã có.

## 2. Yêu cầu chức năng

| Mã | Yêu cầu | Kiểm chứng |
|---|---|---|
| FR-1 | Nhập nhu cầu bằng lưới 168 ô, CSV, hoặc ingest file doanh số (CSV/parquet, người dùng chọn cột trên form). Ô là số nguyên không âm, tối đa 1000. | `test_csv_import.py`, `test_sales_ingest.py`, `test_demand_schema.py` |
| FR-2 | Quy đổi nhu cầu ra số người: tuyến tính `r = max(floor, ceil(alpha·D/p))`. Mọi tham số hiện trên UI và trong metadata. | `test_kpi_and_staffing.py`, `test_sales_ingest.py` |
| FR-3 | Mẫu ca (giờ bắt đầu, độ dài). Nhân viên có giờ tối đa riêng (≤ luật, cứng), giờ tối thiểu riêng (mềm, D25), ngày không làm được, ngày mong muốn nghỉ. Lượt giải có thể đặt ngân sách tuần (cứng, D26) và dung sai chi phí (D21). | `test_validation.py`, `test_roster_cpsat.py`, `test_budget_min_hours.py`, `test_fairness_tolerance.py` |
| FR-4 | Optimize tạo một lượt giải bất biến, trả `job_id` ngay, poll theo `job_id`. Lưu đủ tái lập (nguyên tắc 10). | `test_schedules_flow.py` (MySQL) |
| FR-5 | Mọi nghiệm qua validator. Vi phạm cứng > 0 thì lượt đánh dấu `failed`, không hiện như thành công. | `test_validation.py`, smoke flow |
| FR-6 | Sửa tay tạo lượt mới, chạy lại validator, lịch gốc không đổi. | `test_schedules_flow.py` (MySQL), smoke flow |
| FR-7 | KPI: coverage, giờ thiếu/thừa, hiệu suất, chi phí, phụ cấp đêm, độ lệch ca đêm và cuối tuần, chênh giờ làm, giờ thiếu so với hợp đồng. Xuất CSV. | `test_kpi_and_staffing.py`, `test_schedule_views.py` |
| FR-8 | Độ nhạy: quét λ ∈ [0,8; 1,3], chi phí biên 168 giờ bằng giải lại, dual LP có nhãn xấp xỉ, quét giả định quy đổi, so với baseline greedy, quét dung sai chi phí. | `test_sensitivity.py`, `test_worker.py`, `test_baseline.py` |
| FR-9 | Xếp lại lịch (D20): lịch gốc bất biến; ngày khóa và ca ghim giữ nguyên; người vắng không được xếp vào ngày vắng; gợi ý người thay chỉ qua validator; báo nghỉ đột xuất là lối tắt của xếp lại. | `test_repair.py`, `test_replacement.py`, `test_repair_snapshot.py`, smoke flow |
| FR-10 | Cảnh báo trước khi giải: nhân viên không còn ngày làm, sức chứa dưới nhu cầu, không ca nào phủ giờ đêm, giờ tối thiểu không đạt được, ngân sách dưới chi phí phủ rẻ nhất. Chỉ là điều kiện cần, không chặn nút Optimize. | `test_diagnostics.py`, `test_budget_min_hours.py` |
| FR-11 | Giải thích từng giờ thiếu: luật nào chặn việc thêm một ca, ai còn xếp được. Không gọi solver. | `test_shortfall.py`, `test_schedule_views.py` |
| FR-12 | Nhãn "đầu vào đã đổi" khi hồ sơ nhu cầu, mẫu ca hoặc nhân viên của một lượt bị sửa hoặc xóa (D27). | `test_input_hash.py`, `test_schedules_flow.py` (MySQL) |

## 3. Quyết định đã chốt

Người chốt: Claude theo ủy quyền của người dùng, 2026-11-08 (D1–D24); người dùng chọn D25–D28 ngày 2026-11-09. Lý do ghi cạnh mỗi dòng.

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
| D11 | Trọng số `M_u`, `λ_F` | Không dùng trọng số; giải lexicographic theo tầng: thiếu người, giờ tối thiểu (khi có, D25), thay đổi (repair), chi phí, chênh ca đêm, chênh giờ làm (khi dung sai > 0, D21), sở thích | Tránh chọn `M` tùy tiện (CLAUDE.md 5.2) |
| D12 | So sánh CP-SAT với HiGHS | Trên mô hình tổng hợp có nghỉ ngầm, và trên mô hình theo nhân viên (HiGHS qua `roster_mip.py`, chỉ để đối chiếu; lõi sản phẩm vẫn là CP-SAT) | Đối chiếu có bảng kết quả ở `benchmarks.md` mục 2b; phạm vi 10–30 nhân viên, 3 seed, 60 giây |
| D13 | Kịch bản cơ sở | Store 18, D7–D9, 3 ca 0/8/16 h, 30 nhân viên, 48 giờ | Dữ liệu thật, không sinh ngẫu nhiên |
| D14 | Dataset tổng đài công khai | Bỏ, thay bằng D18 | — |
| D15 | Giết tiến trình con khi quá hạn | Không làm; ghi là giới hạn đã biết | CP-SAT tự dừng theo time limit |
| D16 | Hợp đồng nhân viên | Giờ tối đa riêng (cứng) và giờ tối thiểu riêng (mềm, xem D25); không thêm loại hợp đồng | Đủ cho bán thời gian; MVP mục 8.1. Sửa 2026-11-09 để thêm giờ tối thiểu |
| D17 | Báo cáo nghiên cứu nền | Không có trong repo; đặc tả thay vai trò nguồn | File không tồn tại |
| D18 | Chế độ tổng đài (Erlang A/C) | Bỏ khỏi sản phẩm (người dùng quyết định 2026-11-07) | Nhóm không hỗ trợ tổng đài; giữ một chế độ bán lẻ |
| D19 | Nguồn nhu cầu | Ingest file doanh số tổng quát, không gắn FreshRetailNet. Người dùng ingest file (CSV hoặc parquet) và chọn cột trên form; hệ thống gợi ý cột theo tên. FreshRetailNet là dữ liệu mẫu cho demo | Yêu cầu của người dùng: chỉ là ingest doanh số rồi suy ra nhu cầu; dữ liệu khác FreshRetailNet cũng phải chạy. Hồ sơ lưu tuần tải để quét giả định không cần file gốc |
| D20 | Xếp lại lịch (repair) | Lịch gốc là bất biến. Repair tạo lượt mới: ngày trước `from_day` và ca ghim là cố định, người vắng không được xếp; tầng "thay đổi so với gốc" đặt sau thiếu người và trước chi phí. Gợi ý người thay chỉ dùng validator, không gọi solver. Báo nghỉ đột xuất (`/reroster`) là lối tắt của repair cho một người và các ngày vắng: `from_day` mặc định là ngày vắng đầu tiên, cùng validator và tầng mục tiêu | Giữ ổn định lịch đã công bố (nghiệp vụ người báo ốm); kiểm tra khả thi bằng tính đơn điệu của ràng buộc cứng, không để solver báo INFEASIBLE |
| D21 | Đánh đổi chi phí và công bằng (plan F) | Cho phép. Thêm tham số `cost_tolerance_percent` (0 đến 10, mặc định 0; đã triển khai, xem `model.md` mục 7). Tolerance 0 giữ nguyên thứ tự hiện nay (chi phí đứng trước công bằng); tolerance lớn hơn 0 cho tầng công bằng tăng chi phí tối đa theo tỷ lệ đó. Thêm độ lệch giờ làm `H_max - H_min` cạnh chênh ca đêm | Mặc định không đổi hành vi nên không phá nghiệm thu cũ. Đúng mục 3 của đề tài về công bằng; chi phí tăng được đo và hiện trên UI |
| D22 | Tuần không quấn vòng (plan H) | Cho phép làm ở mức P2. Thêm chế độ `linear` kèm trạng thái kỳ trước của từng nhân viên; mặc định vẫn `cyclic`. Chế độ `cyclic` phải cho kết quả y như cũ | Quấn vòng là xấp xỉ, giới hạn đã nêu ở mục 7. Chỉ làm khi A–F, J xong; chưa làm thì giữ nguyên ghi chú giới hạn |
| D23 | Dự báo nhu cầu (plan I) | Cho phép làm ở mức P2, chỉ baseline mùa vụ (cùng giờ tuần trước, trung bình cùng giờ k tuần) là hàm thuần, không huấn luyện mô hình, không thêm thư viện. Đo bằng WAPE và bias, không dùng MAPE. Trước khi dùng split eval phải xác nhận khoảng ngày bằng `dt.min()/max()` | CLAUDE.md mục 10 cấm thêm thư viện dự báo; baseline không cần. Chỉ làm khi còn thời gian |
| D25 | Giờ tối thiểu theo hợp đồng (plan G3) | `Employee.min_weekly_hours`, mềm: tổng giờ dưới mức tối thiểu là tầng riêng ngay sau thiếu người, trước chi phí. Không là vi phạm cứng, nên repair và gợi ý người thay vẫn đơn điệu. Giá trị lớn hơn giờ tối đa bị từ chối khi nhập | Người dùng chọn mềm 2026-11-09: mô hình không bao giờ INFEASIBLE vì hợp đồng không đạt được; UI báo số giờ thiếu |
| D26 | Ngân sách lương tuần (plan G3) | `weekly_budget` tùy chọn trên mỗi lượt giải, lưu trong snapshot, là trần cứng cho chi phí lao động. Độ phủ vẫn mềm nên ngân sách chặt làm tăng giờ thiếu. Validator có vi phạm `OVER_BUDGET` cho cả lịch | Người dùng chọn trần cứng theo lượt 2026-11-09. Validator kiểm tra nên lịch sửa tay vượt ngân sách bị từ chối |
| D27 | Kết quả cũ (plan G4) | Mỗi lượt giải lưu `source_inputs` (id hồ sơ nhu cầu, mẫu ca, nhân viên và tham số luật đã dùng) và `input_hash` (SHA-256 của snapshot không có phần repair, khóa sắp xếp). `GET /schedules/{id}/staleness` dựng lại snapshot từ dữ liệu hiện tại và so hash: `current`, `stale` (đổi hoặc bị xóa) hoặc `unknown` (lượt cũ chưa có hash, hoặc lượt xếp lại đổi hồ sơ nhu cầu). Lượt sửa tay và xếp lại kế thừa hash của lượt cha. Chỉ là nhãn: lượt vẫn bất biến | Người dùng chọn so snapshot 2026-11-09. Nhân viên thêm sau khi giải làm lượt "mọi nhân viên" thành `stale`, đúng nghĩa vì lịch không có người đó. Đổi tên nhân viên không làm lượt cũ vì tên không nằm trong snapshot |
| D28 | Dữ liệu theo tài khoản | Hồ sơ nhu cầu, nhân viên, mẫu ca, lượt giải và lượt phân tích có `owner_id`; mọi truy vấn lọc theo người đăng nhập, dữ liệu của người khác trả 404. Mã nhân viên, tên mẫu ca, tên hồ sơ là duy nhất trong một tài khoản. Tài khoản mới nhận sẵn 30 nhân viên và 3 mẫu ca. Dữ liệu có trước gán cho tài khoản `SHIFTOPT_DEMO_EMAIL`. Không có vai trò hay chia sẻ dữ liệu | Người dùng chọn 2026-11-09: mỗi tài khoản có dữ liệu làm việc riêng |
| D24 | Playwright cho kiểm thử end-to-end | Không thêm. Dùng `backend/scripts/smoke_flow.py` và duyệt tay theo checklist trong `plan.md` | Tránh dependency mới khi smoke flow đã chạy hai lần liên tiếp đều pass |

## Phiếu duyệt

Người duyệt: Vinh, ủy quyền cho Claude quyết định · Ngày duyệt: 2026-11-08 · Chữ ký: không (duyệt qua hội thoại)

Cột kết quả là "Đồng ý" hoặc "Sửa" kèm nội dung sửa. Mọi "Sửa" phải đổi `LaborRules` hoặc config, rồi chạy lại benchmark (mục 3).

| Mã | Quyết định | Đồng ý / Sửa | Ghi chú |
|---|---|---|---|
| D1 | Ca đêm tính theo luật hay hợp đồng | Đồng ý | Luật là sàn. |
| D2 | "Ngày" bắt đầu lúc mấy giờ | Đồng ý | Khớp `time_grid.py`. |
| D3 | `K` ngày làm liên tiếp tối đa | Đồng ý | Mỗi cửa sổ 7 ngày có một ngày nghỉ. |
| D4 | 48 hay 40 giờ/tuần | Đồng ý | Kịch bản 40 giờ nằm ở What-if. |
| D5 | Đ.110 áp cho cặp ca nào | Đồng ý | Công thức tổng quát, không hard-code `sigma - sigma' > 4`. |
| D6 | Nghỉ giữa giờ (Đ.109) | Đồng ý | Chặt hơn luật, có chủ đích. |
| D7 | `alpha` | Đồng ý | Gộp vào `p`. |
| D8 | `p` (đơn vị doanh số chuẩn hóa mỗi người mỗi giờ) | Đồng ý | Truyền tường minh. Không đổi `DEFAULT_PRODUCTIVITY` (1,0) để khỏi đổi hành vi test. |
| D9 | Sàn `min_staff`, `night_min_staff` | Đồng ý | Theo nguyên tắc 7 của CLAUDE.md. |
| D10 | Doanh thu cho tỷ lệ chi phí lao động | Đồng ý | Không có dữ liệu thật. |
| D11 | Trọng số `M_u`, `λ_F` | Đồng ý | Lexicographic, đã đo so với trọng số ở `benchmarks.md` mục 8. |
| D12 | So sánh CP-SAT với HiGHS | Đồng ý | Phạm vi 10 đến 30 nhân viên, 3 seed, 60 giây; CP-SAT không chứng minh được trọn lượt ở 10 nhân viên (`benchmarks.md` 2b). |
| D13 | Kịch bản cơ sở | Đồng ý | Xác nhận store 18, 30 nhân viên. |
| D14 | Dataset tổng đài công khai | Đồng ý | Thay bằng D18. |
| D15 | Giết tiến trình con khi quá hạn | Đồng ý | Giới hạn đã biết. |
| D16 | Hợp đồng nhân viên | Sửa | Thêm giờ tối thiểu mềm (D25), duyệt 2026-11-09. |
| D17 | Báo cáo nghiên cứu nền | Đồng ý | Đặc tả thay vai trò. |
| D18 | Chế độ tổng đài (Erlang A/C) | Đồng ý | Quyết định của người dùng 2026-11-07. |
| D19 | Nguồn nhu cầu | Đồng ý | Ingest tổng quát. |
| D20 | Xếp lại lịch (repair) | Đồng ý | Tầng thay đổi đứng trước chi phí. |
| D21 | Đánh đổi chi phí và công bằng (plan F) | Đồng ý | Mặc định 0 nên không đổi hành vi hiện nay. |
| D22 | Tuần không quấn vòng (plan H) | Đồng ý | P2, mặc định vẫn cyclic. |
| D23 | Dự báo nhu cầu (plan I) | Đồng ý | P2, chỉ baseline, không thêm thư viện. |
| D24 | Playwright cho kiểm thử end-to-end | Đồng ý | Không thêm. |
| D25 | Giờ tối thiểu theo hợp đồng (plan G3) | Đồng ý | Mềm, tầng sau thiếu người. |
| D26 | Ngân sách lương tuần (plan G3) | Đồng ý | Trần cứng theo lượt. |
| D27 | Đánh dấu kết quả cũ (plan G4) | Đồng ý | So hash snapshot. |
| D28 | Dữ liệu theo tài khoản | Đồng ý | Tách theo `owner_id`, dữ liệu mẫu khi đăng ký. |

**Điểm code chặt hơn luật (đã xác nhận có chủ đích, 2026-11-08):**

- Đ.105 khoản 2: code chỉ cho 8 giờ mỗi ngày, luật cho tới 10 giờ khi quy định theo tuần.
- Đ.109 khoản 1: code mất một giờ phủ cho mọi ca cần nghỉ, luật chỉ yêu cầu 30 hoặc 45 phút.
- Đ.111 khoản 1: code không có ngoại lệ bình quân 04 ngày nghỉ mỗi tháng.

**Các việc nhóm cần quyết trước đây, kết quả 2026-11-08:**

- Kịch bản cơ sở D13: giữ store 18, 30 nhân viên.
- Sai lệch CLAUDE mục 13 dòng 4 (so sánh solver): chấp nhận phạm vi đã đo ở D12; kết luận về solver không vượt phạm vi này.
- Playwright: không thêm (D24).
- F, H, I: cho phép có điều kiện (D21 đến D23). Khi làm xong từng mục, cập nhật CLAUDE.md mục 5.2, 14 cho khớp.

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

Đ.98 khoản 1 (hệ số 150%, 200%, 300% làm thêm) và Đ.107 chưa dùng trong mô hình bản đầu (CLAUDE.md mục 5.4 và 6, mức mở rộng).

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
- Thứ tự tối ưu là lexicographic: thiếu người, giờ tối thiểu (khi có), thay đổi (repair), chi phí, chênh ca đêm, chênh giờ làm (khi có dung sai), sở thích. Không dùng trọng số phạt.
- Công bằng: model tối thiểu hóa max − min (tuyến tính); KPI báo độ lệch chuẩn (mô tả). Hai đại lượng khác nhau.
- Phá đối xứng và phân rã hai pha đều tắt mặc định. Repo không có số đo cho hai tùy chọn này, nên không kết luận chúng nhanh hay chậm hơn.

## 7. Giới hạn đã biết

- Kịch bản cơ sở (store 18, 30 nhân viên) dư sức chứa: 468 giờ-người nhu cầu trên 1440 sức chứa. Đạt 98% không chứng minh được khi thiếu người.
- Kịch bản căng (8 nhân viên, sức chứa 384 < 468) không đạt tối ưu trong 60 giây: coverage 70,3%, gap 100%. Kết quả là `FEASIBLE`, không được gọi là tối ưu.
- Kịch bản cơ sở chỉ đo store 18 (3 seed, 1 worker); so sánh với greedy đo 3 store (18, 84, 578, `benchmarks.md` mục 5). Không suy ra cho store khác.
- Nghị định 145/2020 chưa đối chiếu văn bản gốc. Các điều luật còn lại ở mục 4 đã đối chiếu.
- Lịch tuần quấn vòng: ca Chủ nhật nối với thứ Hai cùng tuần, không nối với tuần trước (D22).
- Chưa có chấm công; không đo adherence.
- Giờ tối thiểu theo hợp đồng là mềm (D25): lịch có thể để một người dưới mức tối thiểu và chỉ báo số giờ thiếu.
- Quét dung sai chi phí (D21) mới đo trên dữ liệu sinh, mọi điểm `FEASIBLE` trong 60 giây (`benchmarks.md` mục 6).
