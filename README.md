<div align="center">

<img src="./assets/logo.svg" alt="ShiftOpt" width="360" />

**Xếp ca nhân viên tối ưu cho dịch vụ có nhu cầu biến động theo giờ**


---

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![OR-Tools 9.15](https://img.shields.io/badge/OR--Tools-CP--SAT_9.15-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/optimization)
[![PuLP + HiGHS](https://img.shields.io/badge/PuLP_3.3-HiGHS-5C6BC0?style=for-the-badge)](https://highs.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.156-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![MySQL 8.4](https://img.shields.io/badge/MySQL-8.4_LTS-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)

</div>

---

## Tổng quan

### Bài toán

Một cửa hàng hoặc kho mở 24/7 có lượng việc thay đổi theo từng giờ. Người quản lý phải trả lời ba câu hỏi:

- **Mỗi giờ cần bao nhiêu người?** Doanh số và lượng khách khác nhau giữa sáng, trưa, tối và giữa các ngày trong tuần.
- **Xếp ai làm ca nào?** Phải đủ người ở mọi giờ, chi phí lương thấp nhất, chia ca đêm công bằng.
- **Có đúng luật không?** Bộ luật Lao động 2019 giới hạn giờ làm, bắt buộc nghỉ giữa hai ca, nghỉ hằng tuần và nghỉ giữa ca. Xếp lịch bằng tay rất dễ vi phạm.

### Giải pháp

ShiftOpt nhận **nhu cầu theo giờ, danh sách nhân viên, mẫu ca và tham số luật**, rồi:

1. **Xếp lịch tối ưu** bằng mô hình quy hoạch nguyên theo từng nhân viên (OR-Tools CP-SAT). Giải theo bốn tầng ưu tiên: ít thiếu người nhất, rồi chi phí thấp nhất, rồi công bằng ca đêm, rồi tôn trọng ngày muốn nghỉ.
2. **Kiểm tra lại toàn bộ luật** bằng một validator viết riêng, độc lập với solver. Hệ thống không tin trạng thái của solver.
3. **Phân tích độ nhạy bằng giải lại thật**: chi phí thay đổi ra sao khi nhu cầu tăng giảm, khi giả định quy đổi thay đổi, và khi một giờ cần thêm một người.

Nhu cầu có thể nhập tay, nhập CSV, hoặc **ingest file doanh số** FreshRetailNet-50K để hệ thống tự suy ra số người cần mỗi giờ. Mọi giả định quy đổi đều hiện trên giao diện.

---

## Kiến trúc

```mermaid
flowchart TB
  UI["Giao diện React<br/>Nhu cầu · Nhân viên · Mẫu ca · Xếp lịch · Độ nhạy"] -->|"HTTP /api"| API["API FastAPI<br/>kiểm tra đầu vào · tạo job · xuất CSV"]
  API --> DB[("MySQL 8.4<br/>hồ sơ · lượt giải · phân tích")]
  API -->|"việc nặng"| Jobs["Xử lý nền<br/>pool tiến trình · hạn chót · giới hạn số job"]

  subgraph Engine["Engine shiftopt (Python thuần, tất định)"]
    Demand["5a. Nhu cầu<br/>nhu cầu ẩn giờ hết hàng · quy đổi ra số người"]
    Opt["5b. Tối ưu<br/>CP-SAT theo nhân viên · Dantzig + HiGHS"]
    Val["5c. Validator<br/>kiểm lại luật trên trục giờ"]
    Kpi["5d. KPI<br/>phủ · thiếu / thừa · chi phí · công bằng"]
    Sens["5e. Độ nhạy<br/>quét λ · quét giả định · chi phí biên · dual LP"]
  end

  API -->|"ingest file doanh số"| Demand
  Jobs --> Opt
  Jobs --> Sens
  Opt -->|"lịch đề xuất"| Val
  Val -->|"0 vi phạm: succeeded<br/>có vi phạm: failed"| DB
  API --> Kpi
```

Mô tả chi tiết từng tầng và thuật toán: [docs/kiến trúc.md](docs/kiến%20trúc.md). Công thức mô hình: [docs/model.md](docs/model.md).

---

## Tính năng chính

### 1. Xếp lịch theo nhân viên, có đủ ràng buộc pháp lý

| Ràng buộc | Căn cứ | Loại |
|---|---|---|
| Tối đa 8 giờ/ngày, 48 giờ/tuần, hoặc thấp hơn theo từng nhân viên | Đ.105 | Cứng |
| Nghỉ ít nhất 12 giờ giữa hai ca, tính bằng công thức tổng quát | Đ.110 | Cứng |
| Nghỉ ít nhất 24 giờ liên tục mỗi tuần, tính trên trục giờ | Đ.111 | Cứng |
| Tối đa 6 ngày làm liên tiếp | Đề bài | Cứng |
| Nghỉ giữa ca 30 phút (ca đêm 45 phút), trừ khỏi số người có mặt | Đ.109 | Cứng |
| Phụ cấp làm đêm 30%, giờ đêm 22h–06h | Đ.98, Đ.106 | Chi phí |
| Phủ nhu cầu từng giờ | Đề bài | Mềm: luôn có lời giải, giờ thiếu hiện trên biểu đồ |

- **Giải theo tầng (lexicographic)** thay vì dùng trọng số phạt tùy ý: tầng sau không được làm xấu kết quả tầng trước.
- **Trung thực về chất lượng lời giải.** Chỉ gọi là tối ưu khi solver trả `OPTIMAL`. Kết quả `FEASIBLE` luôn kèm gap và cận.
- **Tái lập được.** Mỗi lượt giải lưu ảnh chụp đầu vào, tham số, seed, phiên bản solver và log. Với 1 worker và cùng seed, lượt giải đạt `OPTIMAL` luôn cho cùng lịch.

### 2. Validator độc lập: solver đề xuất, validator phán xét

- Kiểm lại mọi ràng buộc cứng trên lịch kết quả, bằng mã không dùng chung với mô hình tối ưu.
- Chạy sau mỗi lượt giải và sau mỗi lần sửa lịch bằng tay. Sửa tay luôn tạo lượt mới; lịch gốc không bị đổi.
- Vi phạm được nhóm theo điều luật. Ví dụ: ca Tối 16h–24h rồi ca Ngày 8h hôm sau bị báo vi phạm Đ.110 vì chỉ nghỉ 8 giờ.

### 3. Ingest doanh số và quy đổi ra nhu cầu nhân sự

- Tải file `train.parquet` của FreshRetailNet-50K (tối đa 200 MB) ngay trên web, chọn store, hệ thống tự xử lý.
- **Nhu cầu ẩn:** giờ hết hàng được thay bằng trung bình doanh số cùng sản phẩm, cùng thứ, cùng giờ ở các ngày còn hàng.
- **Quy đổi:** `số người = max(sàn, ceil(alpha × tải / p))`. Giờ đêm dùng sàn đêm cố định.
- Lưu SHA-256 của file vào metadata để biết chính xác dữ liệu đầu vào là file nào.

### 4. Phân tích độ nhạy bằng giải lại, không dùng giá bóng giả

| Phân tích | Mô hình | Cho biết |
|---|---|---|
| Quét hệ số nhu cầu λ từ 0,8 đến 1,3 | Theo nhân viên (CP-SAT) | Đường chi phí z(λ) của đội thật |
| Quét giả định `alpha` / `p` / sàn | Theo nhân viên (CP-SAT) | Kết luận thay đổi bao nhiêu khi giả định thay đổi |
| Chi phí biên theo giờ (169 lần giải) | Tổng hợp (HiGHS) | Bản đồ nhiệt giờ nào đắt nhất nếu cần thêm người |
| Dual của LP nới lỏng | Tổng hợp (HiGHS) | Ước lượng, luôn gắn nhãn **"xấp xỉ"** |
| So sánh hai lượt giải | — | KPI và chi phí đặt cạnh nhau |

---

## Công nghệ

| Tầng | Công nghệ | Vai trò |
|---|---|---|
| **Engine** | Python 3.11 · OR-Tools CP-SAT 9.15 · PuLP 3.3 + HiGHS 1.13 | Mô hình, solver, validator, KPI, độ nhạy |
| **Backend** | FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · pyarrow | REST API bất đồng bộ, job nền, ingest Parquet |
| **Cơ sở dữ liệu** | MySQL 8.4 LTS (InnoDB, `utf8mb4`) | Hồ sơ nhu cầu, nhân viên, mẫu ca, lượt giải, phân tích |
| **Frontend** | React 19 · Vite 8 · TypeScript 5.9 · TanStack Query 5 · CSS thuần | Giao diện tiếng Việt, biểu đồ tự vẽ bằng SVG |
| **Chất lượng** | pytest · Ruff · mypy strict · Biome · openapi-typescript | Kiểm thử, lint, kiểu tĩnh, kiểu TypeScript sinh từ OpenAPI |
| **Triển khai** | Docker Compose · nginx 1.30 · uv 0.10 | 5 dịch vụ, mọi phiên bản được ghim |

---

## Dịch vụ và cổng

| Dịch vụ | Cổng máy | Vai trò |
|---|---|---|
| `frontend` | `3000` | Giao diện (nginx), chuyển `/api` sang backend |
| `backend` | `8000` | REST API; tài liệu OpenAPI ở `/docs`; healthcheck `/health` |
| `db` | không mở ra ngoài | MySQL 8.4 |
| `migrate` | — | Chạy `alembic upgrade head` một lần rồi thoát |
| `seed` | — | Nạp 30 nhân viên và 3 mẫu ca demo khi bảng còn trống, rồi thoát |

---

## Bắt đầu nhanh

### Yêu cầu

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), hoặc Docker Engine có Compose.
- Chỉ khi chạy ngoài Docker: Python 3.11 cùng [uv](https://docs.astral.sh/uv/) 0.10.10, và Node.js 22.23.3.

### 1. Tải mã nguồn và cấu hình

```bash
git clone https://github.com/vinhnguyen161006/ShiftOpt.git
cd ShiftOpt
cp .env.example .env
```

### 2. Tải dữ liệu demo (một lần)

```bash
cd backend
uv run --locked python -m scripts.download_freshretailnet
cd ..
```

Script tải `train.parquet` vào `data/demo/` và `eval.parquet` vào `data/raw/`, có kiểm SHA-256. File mẫu `data/demo/nhu_cau_cua_hang_24h.csv` đã có sẵn trong repo.

### 3. Chạy toàn bộ hệ thống

```bash
docker compose up -d --build
```

- Giao diện: `http://localhost:3000`
- Tài liệu API: `http://localhost:8000/docs`

Thứ tự khởi động: `db` → `migrate` → `backend` → `seed`, `frontend`.

Dừng hệ thống: `docker compose down`. Dữ liệu vẫn được giữ trong volume `mysql_data`.

### 4. Chạy thử luồng chính

1. **Nhu cầu** → **Tạo hồ sơ nhu cầu** → **FreshRetailNet** → chọn `data/demo/train.parquet`, store `18`, `p = 4` → **Tạo từ dữ liệu**.
2. **Xếp lịch** → chọn hồ sơ vừa tạo → đặt **Số worker của solver** = 1 → **Tối ưu**.
3. Xem lịch, biểu đồ phủ, chi phí và khung **Tuân thủ**. Sau đó vào **Độ nhạy** để chạy quét λ.

Kịch bản demo đầy đủ từng bước: [docs/demo.md](docs/demo.md).

### Chạy ngoài Docker để phát triển

```bash
make install
```

Lệnh này chạy `uv sync --locked` trong `engine/` và `backend/`, và `npm ci` trong `frontend/`.

Backend cần một MySQL có sẵn. Đặt `SHIFTOPT_DATABASE_URL`, ví dụ `mysql+asyncmy://shiftopt:test@127.0.0.1:3307/shiftopt_test?charset=utf8mb4`, rồi chạy trong `backend/`:

```bash
uv run --locked alembic upgrade head
uv run --locked uvicorn --factory src.main:create_app --reload
```

Frontend, trong `frontend/`: `npm run dev`. Lệnh này chuyển `/api` sang `localhost:8000`.

---

## Cấu trúc thư mục

```text
ShiftOpt/
├── engine/                    # Thư viện Python thuần `shiftopt`, không phụ thuộc web hay DB
│   ├── src/shiftopt/
│   │   ├── domain.py          # Instance, Employee, ShiftType, Solution (dataclass bất biến)
│   │   ├── time_grid.py       # Trục 168 giờ có quấn vòng, khung giờ đêm
│   │   ├── staffing/          # Nhu cầu ẩn giờ hết hàng, quy đổi tuyến tính
│   │   ├── constraints/       # LaborRules (hằng số luật), cặp ca cấm, cửa sổ ngày liên tiếp
│   │   ├── models/            # roster_cpsat (theo nhân viên), set_covering_pulp, implicit_breaks
│   │   ├── solvers/           # SolveParams / SolveResult chung cho CP-SAT và HiGHS
│   │   ├── sensitivity/       # Quét λ, chi phí biên, dual LP, quét giả định
│   │   ├── validation.py      # Kiểm tra luật độc lập, không import models/ hay solvers/
│   │   └── kpi.py             # Phủ, thiếu / thừa, chi phí, công bằng
│   ├── tests/                 # Test engine, coverage 98%
│   └── benchmarks/            # Curtois & Qu, so sánh solver, quy mô 20–40 nhân viên
├── backend/
│   ├── src/                   # demand, employees, shifts, schedules, analysis, rules; jobs.py
│   ├── migrations/            # Alembic
│   ├── scripts/               # Tải dữ liệu, seed demo, xuất OpenAPI, smoke test
│   └── tests/                 # unit/ và integration/ (cần MySQL)
├── frontend/src/
│   ├── features/              # Mỗi màn hình một thư mục, không import chéo
│   ├── components/ui/         # Component dùng chung theo phong cách trang chủ
│   ├── locales/vi.ts          # Toàn bộ chữ tiếng Việt của giao diện
│   └── types/api.ts           # Sinh từ OpenAPI, không sửa tay
├── data/demo/                 # File dùng khi demo: train.parquet (không commit), CSV mẫu
├── docs/                      # Đặc tả, kiến trúc, mô hình, benchmark, nghiệm thu, demo, ADR
├── scripts/check_conventions.py   # Cưỡng chế "không comment" và "code chỉ ASCII"
├── docker-compose.yml
└── Makefile
```

---

## Kiểm thử và chất lượng

```bash
make conventions    # không comment, code chỉ ASCII
make lint           # ruff format + ruff check, biome
make typecheck      # mypy strict, tsc
make test           # pytest engine (chặn dưới 80% coverage) và backend
```

- Engine: 147 test, coverage 98%.
- Backend: 110 test. Test tích hợp chạy trên MySQL 8.4 thật và tự bỏ qua khi thiếu biến `SHIFTOPT_TEST_DATABASE_URL`.
- Các test **tiêm vi phạm** để chứng minh validator bắt được lỗi thật: nghỉ 8 giờ giữa hai ca, 7 ngày làm liên tiếp, 49 giờ/tuần, nghỉ tuần 18 giờ.

CI (GitHub Actions) chạy: kiểm tra quy ước, lint, mypy, pytest, `alembic check`, đối chiếu OpenAPI với kiểu TypeScript, build image Docker, gitleaks, `pip-audit`, `npm audit`.

### Benchmark

Chạy trong `engine/`. Số đo và điều kiện chạy: [docs/benchmarks.md](docs/benchmarks.md).

```bash
uv run --locked python benchmarks/download_curtois_qu.py
uv run --locked python benchmarks/run_curtois_qu.py --time-limit 120 --workers 8 --seed 0
uv run --locked python benchmarks/compare_solvers.py
uv run --locked python benchmarks/run_roster_scale.py --sizes 20 30 40 --seeds 0 1 2 --time-limit 60 --workers 1
```

Mọi kết luận về hiệu năng chỉ áp dụng cho các instance và time limit đã đo.

---

## Dữ liệu

- **FreshRetailNet-50K** (Hugging Face `Dingdong-Inc/FreshRetailNet-50K`, CC BY 4.0, arXiv:2505.16319). Đây là doanh số đã chuẩn hóa của kho tiền phương thương mại điện tử, **không phải dữ liệu nhân sự** và không phải cửa hàng 24/7. `alpha`, `p` và các mức sàn là **giả định của nhóm**, luôn hiện trên giao diện.
- **Curtois & Qu (2014)**, benchmark xếp ca. Tải về `data/benchmarks/curtois_qu/` bằng script có kiểm SHA-256. Không commit, vì trang nguồn không ghi giấy phép.

---

## Giới hạn đã biết

- Nhu cầu từ FreshRetailNet là tuần trung bình của dữ liệu quá khứ, chưa phải dự báo tuần tới.
- Chi phí biên và dual LP tính trên mô hình tổng hợp: không giới hạn số người, một mức lương chung, không có luật theo từng người. Kết quả không phải chi phí thêm một người cho đội hiện tại.
- Chỉ hỗ trợ một địa điểm, một loại kỹ năng, một tuần. Không hỗ trợ tổng đài (đặc tả D18).
- Job quá hạn không bị dừng thật, và thời gian chờ trong hàng đợi cũng bị tính vào hạn chót ([docs/kiến trúc.md](docs/kiến%20trúc.md) mục 10).
- Không xác thực, không phân quyền. Chỉ triển khai cục bộ hoặc trong mạng tin cậy.
- Nội dung điều luật chưa được đối chiếu với nguyên văn văn bản 45/2019/QH14 ([docs/đặc tả.md](docs/đặc%20tả.md) mục 4).

---

## Tài liệu

| Tài liệu | Nội dung |
|---|---|
| [docs/đặc tả.md](docs/đặc%20tả.md) | Yêu cầu, quyết định D1–D18 (bản nháp, chờ nhóm duyệt) |
| [docs/kiến trúc.md](docs/kiến%20trúc.md) | Các tầng hệ thống và thuật toán, viết bằng ngôn ngữ tự nhiên |
| [docs/model.md](docs/model.md) | Công thức mô hình toán học |
| [docs/benchmarks.md](docs/benchmarks.md) | Kết quả benchmark và điều kiện đo |
| [docs/acceptance.md](docs/acceptance.md) | Đối chiếu tiêu chí nghiệm thu |
| [docs/demo.md](docs/demo.md) | Kịch bản demo từng bước |
| [docs/adr/](docs/adr/) | Quyết định kiến trúc: chọn solver, thư viện biểu đồ |
| [CLAUDE.md](CLAUDE.md) | Nguyên tắc bất biến và quy ước phát triển |
