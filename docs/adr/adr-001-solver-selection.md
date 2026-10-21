# ADR-001: CP-SAT cho mô hình theo nhân viên, PuLP + HiGHS cho Dantzig và dual LP

Ngày: 2026-10-21
Trạng thái: Đã chốt

## Quyết định

Dùng OR-Tools CP-SAT cho bài toán gán nhân viên (roster), PuLP + HiGHS cho mô hình tập phủ Dantzig và lấy dual LP. Gurobi là tùy chọn qua license học thuật, không phải phụ thuộc bắt buộc.

## Lý do

- CP-SAT xử lý tốt ràng buộc Boolean và chuỗi (nghỉ, ngày liên tiếp).
- HiGHS là solver mã nguồn mở hạng nhất cho LP/MIP, hỗ trợ dual natively.
- Timefold Python bị loại (repo archive, chậm hơn Java).

## Hệ quả

- `solvers/cpsat.py` và `solvers/pulp_backend.py` dùng chung `SolveParams` / `SolveResult` (`solvers/base.py`). Protocol `SolverBackend` chỉ thêm khi benchmark hai solver trên cùng instance.
- Dual chỉ lấy từ LP relaxation và phải gắn nhãn "xấp xỉ" ở mọi đầu ra.
