# QLDA_23NH12_G06 - Work & KPI Management

Ứng dụng quản lý công việc và KPI theo mô hình monorepo:
- **Backend:** FastAPI + SQLAlchemy + Alembic
- **Frontend:** React + Vite
- **Database:** PostgreSQL

Repo này được chuẩn hoá để người khác có thể chạy trên **Windows** và **Ubuntu**. Cách dễ nhất là dùng **Docker cho PostgreSQL**, sau đó chạy backend và frontend local.

---

## 1. Cấu trúc thư mục

```text
QLDA_23NH12_G06/
  backend/          # FastAPI backend
  frontend/         # React + Vite frontend
  docker-compose.yml# PostgreSQL bằng Docker
  README.md
```

---

## 2. Yêu cầu cài đặt

### Dùng cho cả Windows và Ubuntu
Cần có:
- **Git**
- **Docker Desktop** (Windows) hoặc **Docker Engine + Docker Compose** (Ubuntu)
- **Python 3.11+ hoặc 3.12**
- **Node.js 18+**
- **npm**

### Kiểm tra nhanh

```bash
git --version
docker --version
docker compose version
python3 --version
node --version
npm --version
```

Trên **Windows**, nếu lệnh `python3` không có, có thể dùng `python`.

---

## 3. Clone project

```bash
git clone https://github.com/hurzpoet261/BTN-QLDA-Gr06.git
cd BTN-QLDA-Gr06
```

Nếu thư mục local của bạn đang tên khác như `QLDA_23NH12_G06` thì cứ dùng bình thường, không bắt buộc phải trùng tên.

---

## 4. Chạy database bằng Docker

Project đã có sẵn `docker-compose.yml` để chạy PostgreSQL.

### Khởi động database

```bash
docker compose up -d db
```

### Kiểm tra container

```bash
docker compose ps
```

### Thông tin database mặc định
- **Host:** `127.0.0.1`
- **Port host:** `5433`
- **Port trong container:** `5432`
- **Database:** `work_kpi_db`
- **Username:** `postgres`
- **Password:** `postgres`

> Dùng port **5433** để tránh xung đột với PostgreSQL local đang chạy sẵn trên máy.

### Dừng database

```bash
docker compose down
```

### Xóa luôn dữ liệu database

```bash
docker compose down -v
```

---

## 5. Chạy backend

Backend dùng FastAPI, kết nối PostgreSQL qua biến môi trường trong file `.env`.

### 5.1. Ubuntu

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### 5.2. Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### 5.3. Windows CMD

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Backend URL
Khi chạy thành công, backend mặc định ở:
- `http://127.0.0.1:8000`

### Test nhanh backend
Mở trình duyệt hoặc dùng curl:

```bash
curl http://127.0.0.1:8000/health
```

Kết quả mong đợi:

```json
{"status":"ok"}
```

---

## 6. Chạy frontend

Frontend dùng React + Vite.

### 6.1. Ubuntu

Mở terminal mới:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### 6.2. Windows PowerShell / CMD

Mở terminal mới:

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

### Frontend URL
Vite thường chạy ở:
- `http://localhost:5173`

Nếu port `5173` đang bận, Vite sẽ tự chuyển sang port khác như `5174`.

---

## 7. Cấu hình môi trường

### Backend - `backend/.env`
File mẫu:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/work_kpi_db
APP_NAME=Work & KPI Management API
```

### Frontend - `frontend/.env`
File mẫu:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 8. Cách chạy đầy đủ

### Bước 1 - chạy DB
```bash
docker compose up -d db
```

### Bước 2 - chạy backend
```bash
cd backend
# kích hoạt venv rồi chạy
alembic upgrade head
python seed.py
uvicorn app.main:app --reload
```

### Bước 3 - chạy frontend ở terminal khác
```bash
cd frontend
npm install
npm run dev
```

---

## 9. Các lỗi thường gặp

### 9.1. `Port is already in use`
- Với PostgreSQL: project này đã dùng port host `5433`, nên thường sẽ không đụng PostgreSQL local ở `5432`.
- Với frontend: nếu `5173` bận, Vite sẽ nhảy sang `5174` hoặc port khác.

### 9.2. `OPTIONS /tasks 400 Bad Request`
Đây thường là lỗi **CORS** khi frontend chạy ở port khác với port backend đã cho phép.

Ví dụ:
- backend cho phép `5173`
- nhưng frontend thực tế chạy ở `5174`

Khi đó cần cập nhật cấu hình CORS trong backend.

### 9.3. `Ctrl+Z` không tắt Vite
- `Ctrl+C` = dừng hẳn server
- `Ctrl+Z` = tạm treo process, vẫn có thể giữ port

Nếu lỡ bấm `Ctrl+Z`, port có thể vẫn bị chiếm.

### 9.4. Docker DB đã chạy nhưng migrate lỗi
Hãy thử reset volume DB:

```bash
docker compose down -v
docker compose up -d db
```

sau đó chạy lại:

```bash
alembic upgrade head
python seed.py
```

---

## 10. Dành cho người khác dùng project này

Nếu bạn chia sẻ project cho người khác, nên bảo họ làm theo đúng thứ tự:

1. Cài Docker, Python, Node.js
2. Chạy PostgreSQL bằng Docker
3. Chạy backend
4. Chạy frontend

Cách này hoạt động được trên cả:
- **Windows**
- **Ubuntu**

---

## 11. Cập nhật Sprint 1

- Đồng bộ trạng thái task giữa backend và frontend: `todo`, `doing`, `blocked`, `done`
- Form task không còn nhập tay ID thô cho phòng ban/người dùng; thay bằng dropdown lấy dữ liệu thật từ API
- Bổ sung reference APIs:
  - `GET /references/departments`
  - `GET /references/users`

## 12. Cập nhật Sprint 2 - Phần 1 (Backend Auth)

- Mở rộng bảng `users` với: `password_hash`, `role`, `is_active`, `created_at`
- Thêm role hệ thống: `admin`, `manager`, `staff`
- Bổ sung JWT authentication bằng email/password
- Bổ sung auth APIs:
  - `POST /auth/login`
  - `GET /auth/me`
- Bổ sung reusable dependencies:
  - `get_current_user`
  - `require_authenticated_user`
  - `require_admin`
  - `require_manager_or_admin`

## 13. Cập nhật Sprint 2 - Phần 2 (Backend User/Department Authorization)

- Bổ sung CRUD đầy đủ cho `departments`
- Bổ sung CRUD đầy đủ cho `users`
- Áp dụng phân quyền theo role:
  - `admin`: full access với user và department
  - `manager`: chỉ xem users trong department của mình, xem department của mình
  - `staff`: chỉ xem user của chính mình và department của mình
- Password của user tạo mới/cập nhật được hash ở backend
- API response user không trả `password_hash`
- Không cần migration mới vì schema database không đổi

## 14. Gợi ý cải tiến tiếp theo

Nếu muốn project dễ dùng hơn nữa, có thể làm tiếp:
- Docker cho cả **backend + frontend + db**
- CORS đọc từ biến môi trường
- script tự động setup một lệnh
- deploy online để người dùng chỉ cần mở trình duyệt

---

## 15. Tài liệu con
- `backend/README.md`
- `frontend/README.md`

---

## 16. License
Thêm license nếu nhóm muốn public repo chính thức.
