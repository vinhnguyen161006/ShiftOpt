# Mô tả dữ liệu

Cập nhật: 2026-11-07. Các con số lấy từ `backend/` chạy trên file đã tải về; cách tái chạy ở mục 6.

## 1. Nguồn

**FreshRetailNet-50K** (`Dingdong-Inc/FreshRetailNet-50K` trên Hugging Face, giấy phép CC BY 4.0, arXiv:2505.16319). Đây là doanh số sản phẩm theo giờ của kho tiền phương thương mại điện tử, đã chuẩn hóa.

**Dữ liệu này không phải nhu cầu nhân sự và không phải dữ liệu của cửa hàng vật lý 24/7.** Số người cần được suy ra từ giả định của nhóm (mục 5).

Số liệu quy mô: 898 store (thực chất là kho tiền phương) ở 18 thành phố, khoảng 863–865 SKU. Số SKU ghi 865 trong dataset card và 863 trong arXiv; khi trích dẫn, ghi "~863–865".

## 2. Hai file dùng trong dự án

Đặt trong `data/raw/freshretailnet50k/data/` (đã gitignore). SHA-256 được ghim trong `backend/scripts/download_freshretailnet.py`.

| File | Số dòng | Khoảng ngày (đã kiểm bằng `dt.min()/max()`) | Vai trò |
|---|---|---|---|
| `train.parquet` | 4.500.000 | 2024-03-28 → 2024-06-25 (90 ngày) | Nguồn nhu cầu (tải lượng) của ShiftOpt |
| `eval.parquet` | 350.000 | 2024-06-26 → 2024-07-02 (7 ngày) | Tập đánh giá, chưa dùng |

Mỗi dòng là một (store, sản phẩm, ngày). 4.500.000 dòng tương đương 50.000 chuỗi × 90 ngày.

## 3. Cột

| Cột | Kiểu | Ý nghĩa | Dùng trong ShiftOpt |
|---|---|---|---|
| `store_id` | int | Mã store (kho) | Có: chọn store |
| `city_id` | int | Thành phố | Không |
| `management_group_id`, `first/second/third_category_id`, `product_id` | int | Nhóm và mã sản phẩm | Không |
| `dt` | string | Ngày, `YYYY-MM-DD` | Có |
| `sale_amount` | float | Tổng doanh số trong ngày (chuẩn hóa) | Không (dùng `hours_sale`) |
| `hours_sale` | list[24 float] | Doanh số từng giờ 0..23 | **Có: tải lượng theo giờ** |
| `hours_stock_status` | list[24 int] | 1 nếu giờ đó hết hàng | **Có: thay giờ hết hàng** |
| `stock_hour6_22_cnt` | int | Số giờ hết hàng trong khung 6h–22h | Không |
| `holiday_flag` | int | Ngày lễ (≈ 34% dòng) | Chưa dùng; dự kiến cho kịch bản |
| `activity_flag` | int | Có hoạt động khuyến mãi (≈ 38% dòng) | Chưa dùng; dự kiến cho kịch bản |
| `discount` | float | Mức giảm giá, 0 đến 1,088 (trung bình 0,91) | Chưa dùng |
| `precpt` | float | Lượng mưa (trung bình 3,7; tối đa 42,5) | Chưa dùng; không dùng cho dự báo vì lúc dự báo chưa biết |
| `avg_temperature`, `avg_humidity`, `avg_wind_level` | float | Thời tiết | Không |

## 4. Dữ liệu store 18 đã xử lý

Tuần tải của store 18 tạo bằng ingest (`POST /api/demand-profiles/ingest`, hàm `derive_demand` trong `backend/src/demand/sales_ingest.py`) từ `train.parquet`, ô **Cửa hàng** = 18. Tuần tải lưu ở cột `demand_profiles.sales_load`, không ghi ra file.

- **168 giá trị** = 7 thứ × 24 giờ, thứ Hai 00h đầu tiên.
- Store 18 có 164 sản phẩm và 14.760 dòng gốc trong train.
- **Thay giờ hết hàng:** 90.159 ô được thay bằng trung bình doanh số của cùng sản phẩm, cùng thứ, cùng giờ trên các ngày không hết hàng. 1.008 ô không có ngày nào đủ điều kiện nên giữ giá trị quan sát.
- Metadata của hồ sơ ghi SHA-256 của file, mapping cột, phương pháp, số ô đã thay và nhãn "không phải nhu cầu nhân sự". `train.parquet` tải theo revision Hugging Face `c374e85975c82816c495acfa904cc55ab14a47d3`.

Tải lượng theo giờ (một số thứ và giờ, đơn vị doanh số chuẩn hóa):

```
hour     0    3    6    8    9    12   15   18   21   23
Mon    2.5  0.9  9.3 19.2 19.1 13.6 15.3  9.5  4.4  2.2
Tue    3.2  1.2 11.2 21.0 20.1 13.5 14.7 10.0  5.3  2.5
Sat    3.1  0.5 10.5 23.3 26.5 11.5 13.4  7.6  3.6  2.2
Sun    2.7  0.5  9.1 24.2 28.3 12.8 15.8  8.6  4.6  1.6
```

Tổng tải một tuần: 1.552,7. Giờ đỉnh: 28,3, rơi vào 9h Chủ nhật. Mẫu hình: đỉnh buổi sáng 8h–10h, thấp nhất vào 2h–4h, cuối tuần cao hơn các ngày trong tuần.

## 5. Quy đổi thành số nhân viên

`r[d,h] = max(sàn, ceil(alpha · D[d,h] / p))`, trong đó:

- `alpha = 1,0` và `p = 4,0` là **giả định của nhóm** (đặc tả D7–D8), không phải hằng số lấy từ dữ liệu. Với `p = 1` giờ đỉnh cần 29 người, quá lớn so với quy mô demo.
- Sàn ban ngày `min_staff = 1`; sàn ban đêm `night_min_staff = 1`.
- Giờ 22h–06h đặt `D = 0` trước khi quy đổi (`zero_night_load`), nên `r` giờ đêm bằng sàn đêm. Lý do: doanh số ban đêm gần bằng 0 vì kho không bổ sung hàng ngoài khung 6h–22h.

Kết quả với store 18, `alpha = 1`, `p = 4`: tổng 468 giờ-người mỗi tuần, đỉnh 8 người.

## 6. Hạn chế

1. **Không phải nhu cầu nhân sự.** Mọi con số người đều phụ thuộc `alpha`, `p` và các sàn; UI và báo cáo phải ghi rõ.
2. **Chỉ dùng ba store** trong thực nghiệm: 18, 84, 578 (xem mục 8). Kết quả không suy ra cho các store còn lại.
3. **Khuyến mãi không được điều chỉnh.** Bài báo gợi ý hệ số uplift trung bình 1,43; dự án chưa đưa hệ số này vào dữ liệu, chỉ dùng như một kịch bản để thảo luận.
4. **Split `eval` 7 ngày** được xác nhận bằng `dt.min()/max()`, chưa dùng để đánh giá mô hình nào.
5. **Giờ hết hàng** được thay bằng ước lượng, nên tải lượng store 18 là một giả định có phương pháp, không phải doanh số thực đã quan sát.

## 7. Tái tạo

Chạy trong `backend/`:

```
uv run --locked python -m scripts.download_freshretailnet
uv run --locked python -u -m scripts.baseline_store18 --store 18 --employees 30 --productivity 4
```

Lệnh đầu tải hai file (bỏ qua nếu đã đúng SHA-256) và kiểm hash. Lệnh sau ingest store 18 bằng cùng hàm `derive_demand` rồi giải kịch bản cơ sở (số đo ở `benchmarks.md` mục 4). Trên web, tạo hồ sơ bằng ingest như `demo.md` bước 2. Store khác: đổi `--store`.

## 8. Chọn store cho thực nghiệm

Tiêu chí, theo `backend/scripts/rank_stores.py`:

- Xếp hạng store theo tổng doanh số, rồi lấy các store ở phân vị 10, 25, 50, 75, 90, cộng store 18.
- Với mỗi ứng viên, `derive_demand` với α = 1, p = 4, sàn 1 người ban ngày và đêm.
- Chọn nếu đỉnh nhu cầu nằm trong [4, 15] người, và tỷ lệ ô không thay được dưới 5%.

Kết quả (`docs/experiments/store_ranking.csv`): 18, 84 và 578 đạt tiêu chí. Store 27, 278 và 838 không đạt do đỉnh quá thấp (1–3 người) hoặc tỷ lệ ô không thay được cao. Kế hoạch ban đầu yêu cầu 4–6 store; tiêu chí hiện chỉ cho 3.

