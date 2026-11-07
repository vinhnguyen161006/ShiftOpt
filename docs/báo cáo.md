# Xếp ca nhân viên cho dịch vụ có nhu cầu biến động: báo cáo cuối

Cập nhật: 2026-11-05. Trạng thái: bản để nhóm duyệt. Mọi số liệu truy được tới lệnh và bảng nguồn ghi trong ngoặc. Kết luận hiệu năng chỉ áp cho các instance đã đo.

## 1. Bài toán

Xếp ca cho nhân viên sao cho số người có mặt đáp ứng nhu cầu theo giờ, trong ràng buộc pháp lý về giờ làm, nghỉ giữa ca, nghỉ hằng tuần và số ngày làm liên tiếp. Phạm vi bản đầu: một địa điểm, lịch tuần 7×24, một loại kỹ năng ([đặc tả.md](đặc%20tả.md) mục 1).

Đầu ra: lịch xếp ca, KPI, danh sách vi phạm, và phân tích độ nhạy khi nhu cầu hoặc giả định quy đổi thay đổi.

## 2. Mô hình

Hai tầng:

- **Tổng hợp (Dantzig, phủ tập).** Số người theo kiểu ca, `min sum c_s x_s`, `sum a_ts x_s >= r_t`, `x` nguyên không âm. Giải bằng PuLP + HiGHS. Dùng để benchmark, lấy dual LP xấp xỉ, và đối chiếu với chi phí biên. Nghỉ giữa ca được mô hình hóa như mất một giờ phủ (Bechtold–Jacobs đơn giản).
- **Theo nhân viên (CP-SAT).** Biến `x[e,d,s]` Boolean, nghỉ giữa giờ `b[e,d,s,k]`, thiếu người `u_h`, cửa sổ nghỉ 24 giờ `v[e,t]`. Hàm mục tiêu lexicographic bốn tầng: thiếu người, chi phí lương có phụ cấp đêm, chênh lệch ca đêm, vi phạm sở thích. Mỗi tầng một lần giải, tầng sau bị khóa bởi tối ưu tầng trước. `OPTIMAL` chỉ khi mọi tầng `OPTIMAL` ([model.md](model.md) mục 2).

Chọn lexicographic thay vì trọng số phạt `M` tùy ý (quyết định D11). Coverage là mềm, có biến thiếu người, nên mô hình luôn khả thi và UI chỉ rõ giờ thiếu.

Validator độc lập (`validation.py`) kiểm lại mọi nghiệm trên trục giờ quấn vòng, không import `models/` hay `solvers/`. Mọi lượt giải đi qua validator trước khi lưu; vi phạm cứng > 0 thì lượt đánh dấu `failed`.

## 3. Ràng buộc pháp lý

Các hằng nằm trong `LaborRules`: giờ/ngày 8, giờ/tuần 48, nghỉ 12 giờ giữa ca, nghỉ 24 giờ hằng tuần, khung đêm 22h–06h, phụ cấp đêm 30%, nghỉ giữa giờ 30 phút (45 phút ban đêm), `K = 6` ngày liên tiếp.

**Chưa đối chiếu nguyên văn.** Trang văn bản chính thức trả HTTP 403; các nguồn tra được là tóm tắt thứ cấp. Ngưỡng ca từ 6 giờ cho nghỉ giữa giờ, và nội dung đầy đủ của Đ.98, 105, 106, 109, 110, 111 cần đối chiếu với 45/2019/QH14 và NĐ 145/2020 trước khi nộp. Xem [đặc tả.md](đặc%20tả.md) mục 4.

Hai ca pháp lý của nghiệm thu được kiểm bằng test: ca 14h–22h rồi 06h–14h bị cấm; ca qua đêm rồi nghỉ đủ 24 giờ không bị báo vi phạm (`test_afternoon_then_morning_breaks_rest_rule`, `test_overnight_shift_then_full_24_hour_rest_is_allowed`) ([acceptance.md](acceptance.md) dòng 6).

## 4. Dữ liệu và giả định

- **Nguồn nhu cầu.** FreshRetailNet-50K (`Dingdong-Inc/FreshRetailNet-50K`, CC BY 4.0, arXiv:2505.16319). Đây là doanh số chuẩn hóa của kho tiền phương thương mại điện tử, **không phải dữ liệu nhân sự và không phải cửa hàng vật lý 24/7**. Số SKU ghi là ~863–865 (dataset card ghi 865, arXiv ghi 863; mâu thuẫn chưa giải quyết).
- **Split.** Đã xác nhận bằng `dt.min()/max()` trong task 6.1: train 2024-03-28 đến 2024-06-25 (90 ngày), eval 2024-06-26 đến 2024-07-02 (7 ngày). Nhu cầu lấy từ train; eval giữ lại làm tập đánh giá. Chưa tính WAPE/MAPE vì chưa có mô hình dự báo.
- **Nhu cầu ẩn.** Ô hết hàng (`hours_stock_status = 1`) được thay bằng trung bình doanh số cùng sản phẩm, cùng thứ, cùng giờ trên các ngày không hết hàng. Store 18: 90159 ô được thay; 1008 ô không có ngày không hết hàng để học nên giữ giá trị quan sát ([task 6.1](../WORKLOG.md)).
- **Quy đổi.** `r = max(sàn, ceil(alpha·D/p))`. Giả định của nhóm: `alpha = 1,0`, `p = 4,0` (giờ đỉnh cần 8 người với store 18), sàn 1 và 1. Giờ đêm được đặt bằng sàn đêm trước khi quy đổi ([đặc tả.md](đặc%20tả.md) mục 3).
- **Phạm vi.** Chỉ hỗ trợ bán lẻ / kho; chế độ tổng đài (Erlang A/C) đã bỏ (D18).

## 5. Kết quả benchmark

Mọi số ở đây chạy lại được; máy và phiên bản ở [benchmarks.md](benchmarks.md) đầu file.

**Curtois & Qu (2014), Instance1–5 (CP-SAT).** Với 8 worker và 120 giây: Instance1–3 đạt tối ưu công bố và được chứng minh; Instance4 đạt công bố nhưng chưa chứng minh; Instance5 còn cách công bố 5 đơn vị ([benchmarks.md](benchmarks.md) mục 1b). Với 1 worker chỉ Instance1 được chứng minh. Kết quả phụ thuộc số worker.

**Lịch theo nhân viên, 20/30/40 nhân viên, 3 seed.** 18/18 lần `OPTIMAL`, gap 0, coverage 1,0, 0 vi phạm, thời gian tối đa 31,5 s (1 worker) và 25,9 s (8 worker) ([benchmarks.md](benchmarks.md) mục 3). Nhu cầu sinh theo seed, không phải dữ liệu thật.

**Kịch bản cơ sở, store 18, 30 nhân viên, 3 seed.** 3/3 `OPTIMAL`, coverage 1,0, 0 vi phạm, 12–20 giây ([benchmarks.md](benchmarks.md) mục 4). Nhu cầu 468 giờ-người mỗi tuần trên sức chứa 1440: kịch bản dư sức chứa.

**Kịch bản căng, store 18, 8 nhân viên, 3 seed.** Không đạt tối ưu trong 60 giây: `FEASIBLE`, gap 1,0, coverage 0,703, 139 giờ thiếu, 0 vi phạm cứng. Lịch vẫn hợp lệ; chất lượng chưa được chứng minh ([benchmarks.md](benchmarks.md) mục 4). Đây là giới hạn đã đo, không hạ ràng buộc.

## 6. So sánh solver

Trên mô hình tổng hợp có nghỉ ngầm, 3 instance (đều, đỉnh, đỉnh có ca cách đều): HiGHS và CP-SAT cùng `OPTIMAL` và cùng objective ở 10 và 60 giây, đều dưới 0,1 giây ([benchmarks.md](benchmarks.md) mục 2). Instance quá nhỏ để phân biệt hiệu năng. Không suy ra cho mô hình theo nhân viên, vì mô hình đó chỉ có CP-SAT (D12). Không trích số Mittelmann.

## 7. Độ nhạy

- **Chi phí biên rời rạc** `z(r + e_t) − z(r)` cho 168 giờ, bằng giải lại. Đây là chi phí biên của mô hình nguyên, không phải shadow price. Kiểm bằng ví dụ tay (3 ca, nhu cầu 1, giờ 3 = 100 × 980) ([task 5.1](../WORKLOG.md)).
- **Dual LP** từ bản relax của cùng mô hình, luôn gắn nhãn xấp xỉ, integrality gap có thể lớn. Dual không bao giờ lấy từ CP-SAT hoặc MIP.
- **Quét λ** trong {0,8; …; 1,3}: `z(λ)` không giảm. Điểm không `OPTIMAL` được đánh dấu `proven = False`.
- **Quét giả định quy đổi** (`alpha`, `p`, sàn): chạy lại được qua API `staffing-sweep` và trên UI (what-if).
- Hệ số khuyến mãi 1,43 là gợi ý từ bài báo (v5), không phải ước lượng của nhóm; ngày lễ và mưa không có hệ số mặc định.

## 8. Nghiệm thu

[acceptance.md](acceptance.md) đối chiếu từng dòng của CLAUDE.md mục 13. Tóm tắt:

- **Đạt:** ràng buộc cứng; hiệu năng 20–40 nhân viên; pháp lý (kiểm bằng test); tái lập; coverage engine 98,21%.
- **Đạt có điều kiện:** coverage 98% ở kịch bản cơ sở (kịch bản dư sức chứa).
- **Sai lệch:** so sánh solver trên mô hình tổng hợp, không trên mô hình theo nhân viên.
- **Chờ:** độ nhạy và UI cần người duyệt trên trình duyệt. Smoke flow trên Compose chạy đạt; ảnh các màn ở [acceptance/](acceptance/).

Backend chạy 102 test trên MySQL 8.4.10 thật, không skip. Migration `3a7c9e1f2b40` khớp model (`alembic check` sạch).

## 9. Hạn chế

- Chỉ một store, 3 seed, 1 và 8 worker. Không suy ra cho store khác.
- Coverage khi thiếu người chỉ đo ở một kịch bản; solver không chứng minh tối ưu trong 60 giây khi thiếu nhân viên.
- Nghỉ giữa giờ xấp xỉ bằng một giờ phủ, bảo thủ.
- Ngưỡng 6 giờ (Đ.109) và nội dung điều luật chưa đối chiếu nguyên văn.
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

cd ../backend
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 30 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 8 --productivity 4 --time-limit 60 --workers 1 --seeds 0 1 2
```
