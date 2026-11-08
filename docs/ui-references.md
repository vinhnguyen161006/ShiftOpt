# Nguồn tham chiếu UI/UX

Theo CLAUDE.md mục 8.3: mỗi pattern UI lấy từ một nguồn có thật, đã mở xem trực tiếp. Ở mọi màn hình, phần nhìn (màu, font, khung blueprint, nút) theo trang chủ (`frontend/src/features/home/`); bảng dưới chỉ ghi phần bố cục và hành vi lấy từ đâu.

Không chép mã từ nguồn nào dưới đây. Mọi thứ được viết lại bằng token và class của trang chủ.

## Nguồn

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
| R14 | Timefold docs, Employee Shift Scheduling, "Real-time planning" (đọc trang qua công cụ tải trang, 2026-11-07; trang được chuyển hướng từ `/employee-scheduling/latest/`) | https://docs.timefold.ai/employee-shift-scheduling/latest/real-time-planning | 2026-11-07 | Không xác minh được trong phần đọc (không ghi giấy phép); không lấy mã | Tái lập lịch khi phát sinh nghỉ đột xuất: đánh dấu nhân viên không làm được, giữ nguyên các ca đã phân công của người khác ("the same shifts they were originally assigned"). Dùng làm căn cứ cho mục "Báo nghỉ đột xuất". Phần quy tắc xáo trộn trong hợp đồng chỉ đọc qua tóm tắt của công cụ, không trích nguyên văn |
| R13 | MDN, thuộc tính CSS `color-scheme` | https://developer.mozilla.org/en-US/docs/Web/CSS/color-scheme | 2026-11-07, trang ghi sửa lần cuối 2026-07-21 | Creative Commons (chân trang không nêu rõ loại nào); không lấy mã | `color-scheme: dark` đổi màu nền canvas, thanh cuộn và mặc định của ô nhập; kiểm tra tín hiệu hệ thống bằng `prefers-color-scheme` |

## Bố cục lấy từ chính trang chủ

Màn hình Schedule (kết quả một run) và What-if (đường cong z(lambda)) dựng lại hai panel minh họa của trang chủ, dùng chung token và hằng số khoảng cách: `WorkspacePreview` (header có chấm accent, dải KPI bốn ô, khối "Weekly roster" với ô ca một chữ cái, khối "Staffing coverage" với tab ngày, cột nhân sự và dòng meta solver) và `ScenarioPanel` ("Demand vs. staffing": cột theo giờ, thanh lambda, đường cong chi phí kèm hai số và ghi chú). Nguồn là mã của dự án (`frontend/src/features/home/components/WorkspacePreview.tsx`, `ScenarioPanel.tsx`, `home.css`), không phải bên thứ ba. Khác trang chủ: lịch hiển thị mọi nhân viên (cuộn dọc), dòng phụ dưới tên là số ca thay vì loại hợp đồng, vì dữ liệu hợp đồng chưa có; mỗi điểm sweep không tối ưu vẫn được đánh dấu theo nguyên tắc 5.

## Màn hình → nguồn

| Màn hình ShiftOpt | Nguồn |
|---|---|
| Khung app (header, nav) | Trang chủ; R1 (thanh điều hướng trên, vùng làm việc bên dưới) |
| Nút chuyển giao diện sáng/tối (header của trang chủ và khung app) | R12, R13 (hành vi: theo hệ thống, người dùng ghi đè, lưu lại). Nhãn `aria-label` và biểu tượng mặt trời/trăng do nhóm tự đặt, các nguồn trên không bàn về nhãn của nút |
| Demand (lưới 7 × 24, CSV, FreshRetailNet, tổng đài) | R3, R2, R5, R8 |
| Employees, Shift templates | R7, R5, R2, R8, R1 (ngày không làm được / không muốn làm) |
| Schedule (Optimize, trạng thái, lịch, coverage, chi phí) | R1, R10, R9, R6 |
| Compliance (danh sách vi phạm, sửa tay) | R1 (score analysis), R2, R9 |
| What-if (lambda, đường cong, heatmap chi phí biên, so sánh kịch bản) | R4, R11, R9 |
