# ShiftOpt

Xếp ca nhân viên cho dịch vụ có nhu cầu biến động. Mô hình quy hoạch nguyên tuyến tính (OR-Tools CP-SAT, PuLP + HiGHS), API FastAPI, giao diện React. Đặc tả và nguyên tắc: [CLAUDE.md](CLAUDE.md), [WORKLOG.md](WORKLOG.md).

## Yêu cầu

| Thành phần | Phiên bản |
|---|---|
| Python | 3.11 (uv 0.10.10 quản lý) |
| Node.js | 22.23.3 |
| Docker | Docker Desktop hoặc Docker Engine có Compose |
| MySQL | 8.4.10 (chỉ cho test tích hợp và chạy stack) |

## Cài đặt

```
make install
```

Lệnh này chạy `uv sync --locked` trong `engine/` và `backend/`, và `npm ci` trong `frontend/`.

## Chạy toàn bộ stack bằng Docker

```
cp .env.example .env
docker compose up -d --build
```

Thứ tự khởi động: `db` (MySQL) → `migrate` (Alembic, chạy một lần) → `backend` (có healthcheck `/health`) → `frontend`. Mở `http://localhost:3000`.

Kiểm tra API từ đầu đến cuối (tạo nhu cầu, Optimize, sửa tay gây vi phạm, sweep, xuất CSV):

```
cd backend
uv run --locked python -m scripts.smoke_flow --base-url http://localhost:3000
```

Dừng stack: `docker compose down` (giữ dữ liệu) hoặc `docker compose down -v` (xóa dữ liệu).

## Chạy phát triển

Cần MySQL có sẵn. Ví dụ chạy MySQL tạm bằng Docker:

```
docker run -d --name shiftopt-testdb -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=shiftopt_test -e MYSQL_USER=shiftopt -e MYSQL_PASSWORD=test -p 3307:3306 mysql:8.4.10
```

Backend (trong `backend/`, đặt `SHIFTOPT_DATABASE_URL` trỏ tới MySQL, ví dụ `mysql+asyncmy://shiftopt:test@127.0.0.1:3307/shiftopt_test?charset=utf8mb4`):

```
uv run --locked alembic upgrade head
uv run --locked uvicorn --factory src.main:create_app --reload
```

Frontend (trong `frontend/`): `npm run dev`, proxy `/api` sang `localhost:8000`.

## Kiểm thử

```
make conventions    # không comment, code chỉ ASCII
make lint           # ruff format + ruff check, biome
make typecheck      # mypy strict, tsc
make test           # pytest engine (ngưỡng coverage 80%) và backend
```

Test tích hợp backend cần `SHIFTOPT_TEST_DATABASE_URL`; thiếu biến này thì các test đó tự bỏ qua. Trên CI, MySQL 8.4.10 được chạy như service.

## Dữ liệu

- **FreshRetailNet-50K** (Hugging Face `Dingdong-Inc/FreshRetailNet-50K`, CC BY 4.0). Doanh số chuẩn hóa của kho tiền phương thương mại điện tử. **Không phải dữ liệu nhân sự** và không phải cửa hàng 24/7. Tải và xử lý:

  ```
  cd backend
  uv run --locked python scripts/download_freshretailnet.py
  uv run --locked python scripts/build_demand_store.py --store-id 18
  ```

  File thô vào `data/raw/` (không commit), file xử lý vào `data/processed/`.

- **Curtois & Qu (2014)**, benchmark xếp ca: tải về `data/benchmarks/curtois_qu/` bằng script có kiểm SHA-256 ghim. Không commit vì trang nguồn không ghi giấy phép:

  ```
  cd engine
  uv run --locked python benchmarks/download_curtois_qu.py
  ```

Các hệ số `alpha`, `p`, `r_min`, và giả định về lưu lượng cuộc gọi là **giả định của nhóm**, hiển thị trên UI.

## Benchmark và đo hiệu năng

Chạy trong `engine/`. Số đo và điều kiện chạy: [docs/benchmarks.md](docs/benchmarks.md).

```
uv run --locked python benchmarks/run_curtois_qu.py --time-limit 120 --workers 8 --seed 0
uv run --locked python benchmarks/compare_solvers.py
uv run --locked python benchmarks/run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60 --workers 1
```

Nghiệm thu bản đầu theo CLAUDE.md mục 13: [docs/acceptance.md](docs/acceptance.md). Kiểm tra bảo mật và phụ thuộc: [docs/security-review.md](docs/security-review.md).

## Giới hạn đã biết

- **Tối ưu chỉ được khẳng định khi solver báo `OPTIMAL`.** Kết quả `FEASIBLE` hiển thị kèm gap và cận dưới. Mọi kết luận hiệu năng chỉ áp dụng cho các instance và time limit đã đo.
- **Dual chỉ có từ LP relaxation** và luôn gắn nhãn "xấp xỉ". Không có shadow price của mô hình nguyên.
- **Chưa có hợp đồng riêng theo nhân viên** (giờ tối đa, loại hợp đồng). Engine chỉ đọc `max_weekly_hours` và `max_consecutive_days` chung.
- **Erlang A chưa có dataset tổng đài công khai.** Dữ liệu tổng đài hiện là mô phỏng có seed; dataset công khai (ngân hàng Đông Bắc Mỹ, SEELab Technion) chưa kiểm giấy phép.
- **Time limit không giết tiến trình con.** Khi quá hạn, API báo lỗi và bỏ chờ; CP-SAT tự dừng theo time limit của chính nó.
- **Giới hạn số job đang chạy** đếm rồi mới thêm, không khóa; trong điều kiện nhiều request đồng thời, số job có thể vượt nhẹ `max_pending_jobs`.
- **Không xác thực, không phân quyền.** Triển khai cục bộ hoặc trong mạng tin cậy.
- **Multi-worker không tái lập tuyệt đối.** Tái lập đầy đủ cần `num_workers = 1` cùng seed.
- **Container frontend (nginx) chạy root** theo mặc định của image; chưa đổi, đang chờ quyết định.
- **Chưa đo trên máy sạch**: dựng theo README mới kiểm trên máy phát triển.
