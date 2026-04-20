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
- Task CRUD APIs with role-based authorization and filters: status, overdue
- Reference APIs for departments and users
- Auto set `done_at` when task status becomes `done`
- Seed data for departments, users, and tasks

## Default seed login
- Admin: `an@company.local` / `Password@123`
- Manager (Engineering): `binh@company.local` / `Password@123`
- Manager (Business): `dao@company.local` / `Password@123`
- Staff (Engineering): `cuc@company.local` / `Password@123`
- Staff (Business): `em@company.local` / `Password@123`

## Quick start
1. Copy `.env.example` to `.env`
2. Install dependencies
3. Run `alembic upgrade head`
4. Run `python seed.py`
5. Start app with `python -m uvicorn app.main:app --reload`

## Sprint 2 Task authorization
- `admin`: full access to all tasks
- `manager`: only manage tasks in their own department
- `staff`: only see tasks assigned to themselves; cannot create tasks for others
- `creator_id` is always taken from the authenticated user, never trusted from request body
- `done_at` is auto-set when status changes to `done`

## Notes
- Backend auth hiện dùng `pwdlib` với thuật toán Argon2id để tránh lỗi tương thích `passlib + bcrypt` trên một số môi trường Python mới.
- Seed dev hiện dùng email nội bộ dạng `@company.local`, nên schema auth/response chấp nhận chuỗi email nội bộ thay vì validate nghiêm ngặt theo public DNS.
