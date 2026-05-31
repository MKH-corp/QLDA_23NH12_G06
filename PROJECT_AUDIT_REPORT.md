# Bao cao nghiem thu source code du an Work & KPI Management

Ngay lap bao cao: 2026-05-31  
Pham vi doc source: toan bo file tracked cua repo `QLDA_23NH12_G06`, bao gom `README.md`, `docker-compose.yml`, backend FastAPI, Alembic migrations, seed, tests, frontend React/Vite, config mau. Khong dua `node_modules`, `.venv`, `.git`, `__pycache__`, `dist` vao phan danh gia nghiep vu vi do la dependency/artifact sinh ra.

## 1. Tong quan du an

Ten du an: `QLDA_23NH12_G06 - Work & KPI Management`.

Muc tieu: he thong quan ly cong viec, du an, KPI ca nhan/doi nhom, dashboard hieu suat, thong bao tu dong va tro ly AI noi bo. README chinh mo ta stack FastAPI + SQLAlchemy + Alembic, React + Vite, PostgreSQL (`README.md`, `backend/README.md`, `frontend/README.md`).

Doi tuong su dung:
- `admin`: quan tri tong the, nhan su, project, bao cao, KPI.
- `manager`: quan ly task trong phong ban, xem dashboard/team KPI theo backend.
- `staff`: xem va cap nhat task duoc giao, xem KPI/AI insight ca nhan.

Bai toan doanh nghiep:
- Phan cong va theo doi cong viec theo phong ban.
- Tinh KPI tu task hoan thanh dung han, qua han, reopen.
- Theo doi du an voi thanh vien, milestone, audit/status history.
- Tao canh bao task qua han, sap den han, blocked, KPI thap/cao.
- Hoi dap KPI bang AI co kiem soat context theo phan quyen.

Quy mo hien tai: ung dung monorepo nho/trung binh, phu hop demo/sprint productization. Chua dat muc enterprise production do thieu nhieu quy trinh HR/KPI thuc te, audit bao quat, bao cao nang cao, hardening bao mat va deployment hoan chinh.

Cong nghe:
- Backend: FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic Settings, JWT `python-jose`, Argon2id qua `pwdlib`.
- Frontend: React 18, Vite, TypeScript, React Router, dnd-kit.
- DB/devops: PostgreSQL Docker Compose, Adminer.
- AI: OpenAI Responses API qua `urllib.request`, fallback rule-based local.

## 2. Cau truc thu muc

```
QLDA_23NH12_G06/
  README.md
  docker-compose.yml
  backend/
    app/
      api/deps.py
      api/v1/*.py
      core/config.py, security.py
      db/base.py, session.py, models.py
      models/*.py
      repositories/*.py
      schemas/*.py
      services/*.py
      utils/*.py
      main.py
    alembic/
      env.py
      versions/*.py
    tests/*.py
    seed.py
    requirements.txt
  frontend/
    src/
      api/*.ts
      components/**/*.tsx
      context/AuthContext.tsx
      hooks/useApi.ts
      lib/storage.ts
      pages/*.tsx
      types/*.ts
      utils/task.ts
      App.tsx
      main.tsx
      styles.css
    package.json
    vite.config.ts
```

Ghi chu chat luong tai lieu: noi dung tieng Viet trong README/source comment bi mojibake o nhieu file, vi du `README.md`, `backend/app/models/project.py`, `frontend/src/pages/*.tsx`. Day la loi encoding/tai lieu, anh huong nghiem thu UI va maintainability.

## 3. Phan tich kien truc

Frontend Architecture:
```
React Router
  -> ProtectedRoute
  -> AppShell
       -> RoleInsightsPanel
       -> NotificationBell
       -> ChatbotPanel
       -> role pages
API layer src/api/*
  -> apiRequest()
  -> localStorage token
  -> FastAPI endpoints
```

Backend Architecture:
```
FastAPI app.main
  -> CORS middleware
  -> api_router
  -> route handlers
  -> service layer
  -> repository layer
  -> SQLAlchemy models
  -> PostgreSQL
Background:
  FastAPI lifespan -> NotificationScheduler -> NotificationEngine
```

Database Architecture:
```
departments
  -> users
  -> tasks
  -> projects
projects
  -> project_members
  -> project_milestones
  -> project_status_history
  -> project_audit_logs
users
  -> kpi_snapshots, kpi_records, notifications, activity_logs
```

AI Architecture:
```
AI endpoints
  -> AIContextService: lay context theo role
  -> AIInsightService: insight rule-based
  -> OpenAIChatService: goi /responses neu co API key
  -> fallback local neu OpenAI loi/chua cau hinh
```

Authentication Flow:
```
POST /auth/login
  -> AuthService.authenticate_user()
  -> verify Argon2id password
  -> create JWT: sub, email, role, exp
  -> frontend luu token vao localStorage
GET /auth/me
  -> HTTPBearer
  -> decode JWT
  -> query user
```

Authorization Flow:
```
require_authenticated_user
  -> inactive user bi chan
require_admin
require_manager_or_admin
Service-level checks:
  UserService: admin/manager/staff scope
  TaskService: admin all, manager department, staff assignee
  ProjectService: admin, manager department, project manager/member read/write
  KPI/AI/Notification: role-aware filtering
```

Notification Flow:
```
Startup lifespan
  -> NotificationScheduler.start()
  -> run_once moi interval
  -> NotificationEngine.check_all()
  -> tao Notification neu overdue/near-deadline/blocked/low KPI/excellent
Frontend NotificationBell
  -> GET /notifications
  -> PUT /notifications/{id}/read
```

KPI Calculation Flow:
```
TaskService create/update/delete
  -> KpiEngine.recalculate_monthly_kpi(user_id)
  -> lay done tasks trong business month
  -> base_score * weight
  -> on_time_bonus / overdue_penalty / reopen_penalty
  -> upsert KpiSnapshot
KPI APIs
  -> /kpi/me, /kpi/team, /kpi/{user_id}, recalculate endpoints
```

Uu diem:
- Tach layer route/service/repository kha ro cho `users`, `tasks`, `projects`.
- Test backend co 31 testcase bao gom auth, authorization, KPI, scheduler, OpenAI fallback, project lifecycle.
- KPI co explainability qua `breakdown`.
- Project module co audit log va status history rieng.
- AI chat khong gui email raw trong safe context, dung `store: False`.

Nhuoc diem/rui ro:
- Frontend routing chi mo project/KPI/report cho admin, trong khi backend co logic manager/staff cho mot so API (`frontend/src/App.tsx:27-36`, `backend/app/services/project_service.py:60-67`).
- Token luu localStorage, de bi lay neu co XSS (`frontend/src/lib/storage.ts:4-12`).
- `jwt_secret_key` co default yeu trong code (`backend/app/core/config.py:9`).
- CORS hardcode origin dev (`backend/app/main.py:26-33`).
- KPI snapshot thieu unique constraint `(user_id, period_key)`, engine upsert bang query first nen co nguy co duplicate khi concurrent (`backend/app/models/kpi_snapshot.py:8-10`, `backend/app/services/kpi_engine.py:83-93`).
- Xoa user/department la hard delete co the gay loi FK/mat du lieu (`backend/app/repositories/user_repository.py:79-81`, `backend/app/repositories/department_repository.py:34-36`).
- Mot so bang/model chua duoc dung trong UI/API, vi du `kpi_records`.

## 4. Phan tich co so du lieu

Bang va chuc nang:
- `departments`: danh muc phong ban. Unique `name`.
- `users`: nhan su/tai khoan, email unique, role, department, active state.
- `tasks`: cong viec, status `todo/doing/blocked/done`, deadline, done_at, base_weight, creator, assignee, department, project, reopen_count.
- `projects`: du an, code, status, priority, progress, dates, hours/budget, manager, creator/updater, archived_at.
- `project_members`: thanh vien du an, role trong project, unique `(project_id, user_id)`.
- `project_milestones`: milestone du an, due date, completed state, weight.
- `project_status_history`: lich su doi status project.
- `project_audit_logs`: audit thay doi field project.
- `kpi_rules`: rule multiplier cho KPI.
- `kpi_snapshots`: diem KPI theo period.
- `kpi_records`: diem KPI thang dang "legacy/final record", chua thay API dung.
- `notifications`: thong bao nguoi dung.
- `activity_logs`: log hoat dong global.

Quan he chinh:
- `users.department_id -> departments.id`.
- `tasks.creator_id/assignee_id -> users.id`, `tasks.department_id -> departments.id`, `tasks.project_id -> projects.id`.
- `projects.department_id -> departments.id`, `projects.manager_id/created_by/updated_by -> users.id`.
- `project_members.project_id -> projects.id`, `project_members.user_id -> users.id`.
- `project_milestones/project_status_history/project_audit_logs.project_id -> projects.id`.
- `kpi_snapshots/kpi_records/notifications/activity_logs.user_id -> users.id`.

Kiem tra constraint/index:
- Co unique: `departments.name`, `users.email`, `kpi_rules.code`, `project_members(project_id,user_id)`.
- Co index: task status/deadline, KPI user/period, project child FK, activity action/entity.
- Thieu unique quan trong: `kpi_snapshots(user_id, period_key, period_type)`; `kpi_records(user_id, month, year)`; `projects.code` neu code la ma du an; notification duplicate chi kiem bang query JSON, khong co constraint.
- Thieu index nen bo sung: `tasks.assignee_id`, `tasks.department_id`, `tasks.project_id`, `notifications.user_id/is_read/created_at`, `projects.status/department_id/manager_id`, `users.department_id/role/is_active`.
- FK thieu `ondelete` ro rang o core table: `tasks`/`users.department_id`/`notifications`/`kpi_snapshots`; xoa user/department co nguy co fail hoac mat du lieu.
- `ActivityLog.user_id` model khong co `ondelete=SET NULL`, trong migration ban dau co sau do migration `a0e...` tao lai FK khong ondelete (`backend/alembic/versions/a0e272b985c3_update_activity_logs_schema.py:20-21`).

Doi chieu migration:
- Alembic co single head `20260531_001`.
- Co migration rong `9b3ab314b7c5` va `d7b098d8d51c` de giu chuoi; chap nhan duoc nhung nen ghi ro ly do.
- File migration `20260510 000001 enterprise project management.py` co khoang trang, gay bat tien CLI/scripting.

Toi uu DB de xuat:
- Them unique composite cho KPI snapshot/record.
- Dung soft delete cho users/departments/tasks/projects hoac set `is_active/archived_at`.
- Them index theo truy van thuc te.
- Them check constraint cho `base_weight >= 1`, `project progress 0..100`, `start_date <= end_date`.
- Chuan hoa status project bang enum/check constraint thay vi string thuong.

## 5. API da tim thay

Auth:
- `POST /auth/login`
- `GET /auth/me`

Users:
- `POST /users`
- `GET /users`
- `GET /users/{user_id}`
- `PUT /users/{user_id}`
- `DELETE /users/{user_id}`

Departments:
- `POST /departments`
- `GET /departments`
- `GET /departments/{department_id}`
- `PUT /departments/{department_id}`
- `DELETE /departments/{department_id}`

Tasks:
- `POST /tasks`
- `GET /tasks`
- `GET /tasks/{task_id}`
- `PUT /tasks/{task_id}`
- `DELETE /tasks/{task_id}`

Projects:
- `GET /projects/`
- `POST /projects/`
- `GET /projects/dashboard`
- `GET /projects/{project_id}`
- `PUT /projects/{project_id}`
- `DELETE /projects/{project_id}`
- `POST /projects/{project_id}/members`
- `PUT /projects/{project_id}/members/{user_id}`
- `DELETE /projects/{project_id}/members/{user_id}`
- `POST /projects/{project_id}/milestones`
- `PATCH /projects/{project_id}/milestones/{milestone_id}/complete`
- `GET /projects/{project_id}/analytics`
- `GET /projects/{project_id}/kpi`

KPI:
- `GET /kpi/me`
- `GET /kpi/team`
- `GET /kpi/{user_id}`
- `POST /kpi/recalculate/me`
- `POST /kpi/recalculate/team`
- `POST /kpi/recalculate/all`

AI:
- `GET /ai/insights/me`
- `GET /ai/insights/team`
- `POST /ai/insights/run`
- `GET /ai/summary/dashboard`
- `POST /ai/chat`

Notification, report, activity:
- `GET /notifications/`
- `PUT /notifications/{notification_id}/read`
- `POST /notifications/run-check`
- `GET /reports/productivity`
- `GET /activities/recent`
- `GET /references/departments`
- `GET /references/users`

## 6. Phan tich chuc nang nghiep vu

Trang thai theo source:
- Dang nhap JWT: Hoan thanh.
- Lay profile hien tai: Hoan thanh.
- Dang ky user tu public: Chua co.
- Quan ly nhan su CRUD: Hoan thanh mot phan. Co CRUD admin, nhung delete hard, password policy yeu, frontend gui password trong form.
- Quan ly phong ban CRUD: Hoan thanh mot phan. Co backend CRUD, frontend chua co man hinh department rieng.
- Phan quyen role admin/manager/staff: Hoan thanh mot phan. Backend kha tot, frontend route bi han che manager.
- Quan ly task CRUD: Hoan thanh mot phan. Co board, filter, pagination, DnD status. Staff van goi delete/update API; backend cho staff xoa task cua minh, thuc te doanh nghiep thuong khong nen.
- Giao viec: Hoan thanh mot phan. Manager giao viec trong department; chua co workflow accept/approve.
- Deadline/overdue: Hoan thanh mot phan. Co query va canh bao, chua co SLA/escalation.
- KPI ca nhan: Hoan thanh mot phan. Co snapshot va breakdown.
- KPI team: Hoan thanh mot phan. Co API/UI admin, manager backend co nhung frontend chua co trang KPI rieng.
- KPI phong ban/toan cong ty: Hoan thanh mot phan. Dashboard/reports co du lieu co ban, chua co trend/period history.
- Project management: Hoan thanh mot phan. Co project CRUD, member, milestone, status history, audit field-level; frontend detail chua thao tac member/milestone/status history day du.
- Bao cao productivity: Hoan thanh mot phan. Chi co bao cao don gian theo phong ban.
- Notification: Hoan thanh mot phan. Co rule-based notification va bell, chua realtime push/email/in-app preference.
- Activity log: Hoan thanh mot phan. Co log global, nhung user service log `user_id=None` nen khong ro actor.
- AI Insight: Hoan thanh mot phan. Rule-based, khong phai LLM insight.
- AI Chatbot: Hoan thanh mot phan. Co OpenAI neu config, fallback local.
- Scheduler: Hoan thanh mot phan. Chay in-process theo lifespan, chua co distributed lock.
- Audit Log enterprise: Hoan thanh mot phan. Chi manh o project, yeu o user/task/department.
- File dinh kem/comment/feedback/workflow phe duyet/cham cong/nghi phep: Chua co.

## 7. Danh gia theo nghiep vu thuc te

Neu xem day la he thong KPI cho doanh nghiep that:
- Dap ung nghiep vu cot loi hien tai: khoang 45-55%.
- San sang demo noi bo/sprint review: co.
- San sang production doanh nghiep: chua.

Da dap ung:
- Tai khoan noi bo, role co ban.
- Phong ban, nhan su, task, project.
- KPI theo task trong thang hien tai.
- Dashboard, report co ban.
- Notification rule-based.
- AI assistant co context theo role.

Con thieu lon:
- Cham cong, nghi phep, lich lam viec, ngay le.
- KPI target/OKR theo chu ky, approval/chot KPI, lich su KPI bat bien.
- Quy trinh phe duyet task/KPI/project.
- Comment, feedback, file dinh kem, mention.
- Audit log bao quat moi entity.
- Phan quyen chi tiet theo permission/policy, khong chi role.
- Dashboard dieu hanh nhieu chu ky, drill-down, export.
- Tenant/company separation neu dung nhieu doanh nghiep.
- Backup/restore, observability, monitoring, rate limit, security headers.

## 8. Danh gia AI

AI Chatbot:
- Co endpoint `/ai/chat`.
- Neu `OPENAI_CHAT_ENABLED=true` va co `OPENAI_API_KEY`, backend goi OpenAI Responses API (`backend/app/services/openai_chat_service.py:45-81`).
- Neu khong co key hoac loi API, dung fallback local (`backend/app/api/v1/ai.py:112-149`).

AI Insight:
- `AIInsightService` la rule-based, khong goi LLM (`backend/app/services/ai_insight_service.py`).
- Insight dua tren overdue, near deadline, blocked, KPI thap/cao.

AI Notification:
- `NotificationEngine` rule-based, khong co LLM generation (`backend/app/services/notification_engine.py`).
- Truong `is_ai_generated` co trong DB nhung engine hien set `False`.

Context AI lay tu:
- `AIContextService`: tasks, KPI snapshot, notifications, users/departments theo role (`backend/app/services/ai_context_service.py:19-158`).
- OpenAI safe context chi gui cac truong tong hop, id task, risk/top performers da cat bot (`backend/app/services/openai_chat_service.py:102-120`).

Du lieu AI truy cap duoc:
- Staff: task/KPI/thong bao cua minh.
- Manager: team trong department.
- Admin: toan he thong o muc tong hop.

Du lieu AI khong truy cap duoc:
- Noi dung chi tiet task gan day trong prompt OpenAI, audit log, project detail, comment/file vi chua co.
- Du lieu ngoai he thong.

Muc do thong minh: trung binh-thap neu khong co OpenAI key; trung binh neu co OpenAI key, vi context con rat ngan va chu yeu la aggregate.

De xuat AI:
- Them RAG/context builder cho task/project/KPI theo cau hoi.
- Luu prompt/evidence id an toan de audit.
- Tach "AI insight" that su dung LLM co guardrail, con notification rule-based nen goi la rule engine.
- Them prompt-injection tests va redaction PII.

## 9. Bao mat

Danh gia tong the: Trung binh cho demo noi bo, Thap-Trung binh cho production.

JWT:
- Co exp, HS256, bearer token.
- Rui ro: secret default trong code (`backend/app/core/config.py:9`), khong co refresh/revocation/session blacklist.

Password hashing:
- Tot: dung `PasswordHash.recommended()` Argon2id (`backend/app/core/security.py:9-17`).
- Thieu: password policy/min length/history/lockout/rate limit.

RBAC:
- Co dependency va service checks.
- Rui ro: frontend route khong phai security boundary; backend la chinh. Project member role co nhung chua dong bo UI day du.

SQL Injection:
- Thap do dung SQLAlchemy ORM. Co raw SQL trong migration, khong nhan input user.

XSS:
- React escape default.
- Rui ro token localStorage bi lay neu XSS (`frontend/src/lib/storage.ts:4-12`).

CSRF:
- Dung Bearer token khong cookie nen CSRF thap.
- Neu chuyen sang cookie can CSRF protection.

File upload:
- Khong co file upload. Khong du du lieu de danh gia upload security.

API exposure:
- Hầu hết endpoint yêu cầu auth, `/health` public.
- CORS hardcode dev origins (`backend/app/main.py:26-39`).

Secrets:
- `.env.example` ok, `.env` bi gitignore. Bao cao khong doc/noi dung `.env` thuc de tranh lo bi mat; khong du du lieu de ket luan secret production.

## 10. Chat luong code

Clean Code:
- Backend co layer kha ro, nhung comment mojibake va comment qua nhieu lam giam maintainability.
- Frontend dung nhieu inline style, kho bao tri va khong theo design system ro rang.

SOLID/Separation:
- Backend service/repository dap ung muc kha.
- ProjectService qua lon, gom CRUD/member/milestone/analytics/KPI/audit, nen tach module.
- Frontend API layer co trung lap: `frontend/src/api/projects.ts` va `frontend/src/api/services.ts` cung co project APIs; `getKpiAnalytics` goi endpoint khong ton tai.

DRY/KISS:
- Co duplicate DTO/type mapping o frontend.
- UI co nhieu component inline style thay vi reusable.

Dependency Injection:
- FastAPI Depends dung tot cho DB/auth.
- Scheduler tao session rieng tot.

Dead/unused code/file cu the:
- `frontend/src/api/services.ts:16` goi `/kpi/analytics` nhung backend khong co endpoint nay.
- `frontend/src/components/project/ProjectFormModal.tsx:18-21` co `getDefaultDepartmentId` khong dung.
- `frontend/src/pages/StaffTasksPage.tsx:4` import `createTask` nhung staff page khong tao task.
- `backend/app/models/kpi_record.py` va bang `kpi_records` chua thay API/UI/service dung trong source.
- `backend/alembic/versions/9b3ab314b7c5_add_projects_kpis_notifications.py` la migration rong.
- `backend/alembic/versions/d7b098d8d51c_create_activity_logs_table.py` co block code cu comment-out dai.
- `backend/app/schemas/reference.py` duplicate mot phan voi `department.py`/`user.py`.

## 11. Loi va rui ro tiem an

1. KPI snapshot co nguy co duplicate khi concurrent  
Muc do: Cao.  
Vi tri: `backend/app/models/kpi_snapshot.py:8-10`, `backend/app/services/kpi_engine.py:83-93`.  
Cach tai hien: hai request update task/recalculate KPI cho cung user/period chay dong thoi, ca hai deu khong thay snapshot va cung insert.  
Cach sua: them unique constraint `(user_id, period_type, period_key)`, dung PostgreSQL upsert `ON CONFLICT DO UPDATE`.

2. Hard delete user co the fail FK hoac mat lich su  
Muc do: Cao.  
Vi tri: `backend/app/services/user_service.py:105-118`, `backend/app/repositories/user_repository.py:79-81`.  
Cach tai hien: tao user co task/KPI/notification/activity, goi `DELETE /users/{id}`. DB se fail FK hoac mat user neu cascade duoc them sau nay.  
Cach sua: soft delete `is_active=false`, chan xoa user co data, hoac set ondelete policy ro rang.

3. Staff duoc xoa task cua minh  
Muc do: Cao theo nghiep vu doanh nghiep.  
Vi tri: `backend/app/services/task_service.py:155-166`, `frontend/src/pages/StaffTasksPage.tsx:86`.  
Cach tai hien: staff login, xoa task assigned.  
Cach sua: staff chi duoc cap nhat status/comment; delete chi manager/admin.

4. Frontend khong expose day du quyen manager/project/KPI  
Muc do: Trung binh-Cao.  
Vi tri: `frontend/src/App.tsx:27-36`, `frontend/src/components/AppShell.tsx:21-29`.  
Cach tai hien: manager login chi thay `/manager/tasks`, khong co project/dashboard/KPI/report du backend cho phep.  
Cach sua: them route/menu manager cho dashboard/project/team KPI/report voi scope backend.

5. JWT secret default yeu  
Muc do: Cao neu deploy sai.  
Vi tri: `backend/app/core/config.py:9`.  
Cach tai hien: deploy khong set `JWT_SECRET_KEY`, token co the forge neu biet default.  
Cach sua: fail-fast neu production va secret default; validate env bat buoc.

6. Token localStorage de bi lay neu XSS  
Muc do: Trung binh.  
Vi tri: `frontend/src/lib/storage.ts:4-12`.  
Cach tai hien: chen script XSS bat ky co the doc localStorage.  
Cach sua: can nhac HttpOnly Secure SameSite cookie, CSP, sanitize input/output.

7. Endpoint frontend ton tai nhung backend khong co  
Muc do: Trung binh.  
Vi tri: `frontend/src/api/services.ts:16`.  
Cach tai hien: goi `getKpiAnalytics()` se 404.  
Cach sua: xoa code hoac tao endpoint `/kpi/analytics`.

8. Project code khong unique  
Muc do: Trung binh.  
Vi tri: `backend/app/models/project.py:68`, migration `20260510...:49`.  
Cach tai hien: tao hai project cung code.  
Cach sua: unique index cho `projects.code` neu code la ma nghiep vu.

9. Notification duplicate prevention dua vao JSON query khong co constraint  
Muc do: Trung binh.  
Vi tri: `backend/app/services/notification_engine.py:175-188`.  
Cach tai hien: hai scheduler instance hoac hai request `run-check` dong thoi co the tao trung.  
Cach sua: unique key theo `(user_id, notification_type, business_date/period_key)` bang cot rieng hoac generated column.

10. Scheduler in-process khong an toan khi scale multi-instance  
Muc do: Trung binh.  
Vi tri: `backend/app/main.py:9-21`, `backend/app/services/notification_scheduler.py`.  
Cach tai hien: chay 2 backend replicas, ca hai deu check notification.  
Cach sua: dung job queue/Celery/APScheduler voi distributed lock/advisory lock.

11. User activity log mat actor voi create/update/delete user  
Muc do: Trung binh.  
Vi tri: `backend/app/services/user_service.py:32-38`, `backend/app/services/user_service.py:96-102`, `backend/app/services/user_service.py:112-117`.  
Cach tai hien: admin tao/sua/xoa user, log hien System do `user_id=None`.  
Cach sua: truyen `current_user` xuong service va log actor id.

12. CORS hardcode origin dev  
Muc do: Trung binh.  
Vi tri: `backend/app/main.py:26-39`.  
Cach tai hien: frontend deploy domain moi bi CORS fail hoac can sua code.  
Cach sua: doc allow origins tu env, tach dev/prod.

13. README/source bi mojibake  
Muc do: Trung binh cho nghiem thu.  
Vi tri: README va nhieu file co tieng Viet.  
Cach tai hien: mo file trong terminal/editor hien ky tu sai.  
Cach sua: chuan hoa UTF-8, chay script kiem tra encoding, sua noi dung hien thi.

14. KPI khong co quy trinh chot/duyet/chong sua lich su  
Muc do: Cao theo nghiep vu KPI.  
Vi tri: `backend/app/services/kpi_engine.py`, `backend/app/models/kpi_snapshot.py`.  
Cach tai hien: task cu doi status/deadline/reopen se tinh lai snapshot thang hien tai, khong co approval/chot ky.  
Cach sua: them period closing, KPI record immutable, audit change sau khi close.

15. Project budget utilization tinh sai don vi  
Muc do: Trung binh.  
Vi tri: `backend/app/services/project_service.py:500-502`.  
Cach tai hien: `budget_utilization = actual_hours / estimated_budget * 100`, lay gio chia tien.  
Cach sua: them `actual_budget/cost_spent` hoac doi ten thanh hour utilization = actual_hours / estimated_hours.

16. Project create khong validate manager/department hop le  
Muc do: Trung binh.  
Vi tri: `backend/app/services/project_service.py:69-91`.  
Cach tai hien: tao project voi `manager_id` user khong ton tai/khac department/role staff; DB co the fail FK hoac business sai.  
Cach sua: validate manager ton tai, active, role manager/admin hoac member policy.

17. Update user password co the hash chuoi rong  
Muc do: Trung binh.  
Vi tri: `backend/app/services/user_service.py:89-90`, `frontend/src/components/EmployeeForm.tsx:20-27`.  
Cach tai hien: edit user, frontend gui `password: ""`; backend hash password rong neu field co trong payload.  
Cach sua: frontend omit password rong; backend bo qua password rong va validate min length.

18. `done_at` trong seed duoc set runtime cho task done, nhung KPI snapshot khong seed  
Muc do: Thap-Trung binh.  
Vi tri: `backend/seed.py:83-122`, `backend/seed.py:148-150`.  
Cach tai hien: sau seed dashboard/KPI co the 0 den khi recalculate.  
Cach sua: seed chay `KpiEngine` cho active users.

## 12. Diem danh gia

- Backend: 7.0/10. Layer kha tot, tests tot, nhung con rui ro production/KPI/soft delete/scheduler.
- Frontend: 6.0/10. Build pass, UI day du cho demo admin/task, nhung role coverage lech backend, inline style nhieu, mojibake.
- Database: 6.0/10. Schema phong phu, migration co single head, nhung thieu unique/index/ondelete/check constraints.
- AI: 5.5/10. Co OpenAI/fallback/context gating, nhung insight/notification chu yeu rule-based, context han che.
- Security: 5.5/10. Auth/hash/RBAC co, nhung secret default, localStorage token, thieu rate limit/audit/session hardening.
- DevOps: 4.5/10. Co DB Docker, chua dockerize backend/frontend, chua CI/CD/observability/prod config.
- Business Logic: 5.5/10. Core task/KPI/project co, nhung thieu quy trinh HR/KPI thuc te.

Tinh tong hop:
- Hoan thanh ky thuat: 65%.
- Hoan thanh nghiep vu: 50%.
- San sang trien khai thuc te: 35%.

## 13. Kiem chung

Da chay:
- Backend: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` trong `backend`: 31 tests pass.
- Alembic: `python -m alembic heads`: single head `20260531_001`.
- Frontend: `npm.cmd run build`: Vite build thanh cong.

Luu y: khong chay migration tren PostgreSQL that va khong chay E2E browser. Khong du du lieu de ket luan 100% ve runtime production DB.

## 14. Roadmap phat trien

Bat buoc sua ngay:
- Bat buoc set JWT secret production, fail-fast neu dung default.
- Them unique constraint cho KPI snapshots/records va upsert an toan.
- Doi user/task delete sang soft delete/permission dung nghiep vu.
- Sua password update rong.
- Sua mojibake UTF-8 tren README/UI/source comments.
- Dong bo frontend routes cho manager/project/KPI/report theo backend hoac thu hep backend neu chua muon release.

Nen sua:
- Them index theo query thuc te.
- Tach ProjectService thanh CRUD, access policy, member, milestone, analytics.
- Xoa/hoan thien dead code `/kpi/analytics`, `kpi_records`, migration rong/comment-out.
- Cau hinh CORS bang env.
- Them validation date/weight/project code/manager role.
- Seed KPI snapshots sau seed task.

Nang cap tuong lai:
- Dockerize backend/frontend, healthcheck day du.
- CI pipeline lint/test/build/migration check.
- Observability: structured logging, request id, metrics.
- Rate limit auth/AI endpoints.
- Realtime notification qua WebSocket/SSE.
- Export report CSV/PDF.

Tinh nang doanh nghiep nen bo sung:
- Cham cong, nghi phep, holiday calendar.
- KPI target/OKR, approval workflow, period close, immutable KPI history.
- Comment, feedback, attachment, mention.
- Audit log bat buoc cho user/task/department/KPI.
- Workflow phe duyet task/project/status change.
- Dashboard trend theo thang/quy/nam, drill-down phong ban/nhan vien.
- Permission model chi tiet hon role co ban.

## 15. Ket luan nghiem thu

Du an da vuot muc prototype don gian: co backend kha day du, migration co kiem tra, test pass, frontend build pass, co KPI/notification/AI module. Tuy nhien, neu nghiem thu nhu san pham doanh nghiep that thi chua dat production readiness. Cac diem can xu ly truoc release la KPI consistency, soft delete/permission, security hardening, encoding, dong bo frontend-role va quy trinh KPI enterprise.

Ket luan: Chap nhan o muc demo/sprint internal; khong nen trien khai production cho doanh nghiep that neu chua hoan tat nhom viec "Bat buoc sua ngay".
