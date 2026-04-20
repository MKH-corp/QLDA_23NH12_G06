# Work & KPI Management Backend - Sprint 1

## Features
- FastAPI backend
- PostgreSQL via environment variable
- SQLAlchemy ORM
- Alembic migrations
- Core models: Department, User, Task
- JWT authentication with email/password login
- Password hashing bằng Argon2id (`pwdlib`)
- Auth APIs: `POST /auth/login`, `GET /auth/me`
- Department CRUD APIs with role-based authorization
- User CRUD APIs with role-based authorization
- Task CRUD APIs with filters: status, overdue
- Reference APIs for departments and users
- Auto set `done_at` when task status becomes `done`
- Seed data for departments, users, and tasks

## Default seed login
- Email: `an@company.local`
- Password: `Password@123`

## Quick start
1. Copy `.env.example` to `.env`
2. Install dependencies
3. Run `alembic upgrade head`
4. Run `python seed.py`
5. Start app with `uvicorn app.main:app --reload`

## Notes
- Backend auth hiện dùng `pwdlib` với thuật toán Argon2id để tránh lỗi tương thích `passlib + bcrypt` trên một số môi trường Python mới.
- Seed dev hiện dùng email nội bộ dạng `@company.local`, nên schema auth/response chấp nhận chuỗi email nội bộ thay vì validate nghiêm ngặt theo public DNS.
