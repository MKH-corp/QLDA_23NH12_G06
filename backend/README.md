# Work & KPI Management Backend - Sprint 1

## Features
- FastAPI backend
- PostgreSQL via environment variable
- SQLAlchemy ORM
- Alembic migrations
- Core models: Department, User, Task
- Task CRUD APIs with filters: status, overdue
- Reference APIs for departments and users
- Auto set `done_at` when task status becomes `done`
- Seed data for departments, users, and tasks

## Quick start
1. Copy `.env.example` to `.env`
2. Install dependencies
3. Run `alembic upgrade head`
4. Run `python seed.py`
5. Start app with `uvicorn app.main:app --reload`
