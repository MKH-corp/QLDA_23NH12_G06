# Work & KPI Frontend - Sprint 1

React + Vite frontend for Work & KPI Management.

## Features
- Login page with JWT token handling
- Auth state with current user, token persistence, logout
- Route guard with role-based redirects for admin / manager / staff
- Staff task page: view my tasks, filter by status, update status, view detail
- Manager task page: view team tasks, create task, assign task, filter by status / assignee / overdue
- Admin page: basic user and department management overview
- Call real FastAPI backend APIs

## Local run
1. Copy `.env.example` to `.env`
2. Install dependencies with `npm install`
3. Start dev server with `npm run dev`
4. Ensure backend is running at `VITE_API_BASE_URL`

## Sprint 2 frontend notes
- Token is stored in `localStorage`
- Auth state is managed in `src/context/AuthContext.tsx`
- Route guard is implemented in `src/components/ProtectedRoute.tsx`
- Role redirects:
  - `admin` -> `/admin`
  - `manager` -> `/manager/tasks`
  - `staff` -> `/staff/tasks`
