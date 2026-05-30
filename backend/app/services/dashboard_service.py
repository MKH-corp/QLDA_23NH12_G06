from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.department import Department
from app.models.task import Task
from app.models.kpi_snapshot import KpiSnapshot
# from app.models.activity import ActivityLog
from app.schemas.dashboard import (
    DashboardStats, DepartmentPerformance,
    UserPerformance, ActivityLogResponse, DashboardResponse
)
from datetime import datetime

class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_data(self) -> DashboardResponse:
        period_key = f"{datetime.now().year}-{datetime.now().month:02d}"

        # 1. Lấy thông số tổng quan (Stats)
        total_users = self.db.query(User).filter(User.is_active == True).count()
        total_depts = self.db.query(Department).count()
        completed_tasks = self.db.query(Task).filter(Task.status == "done").count()
        total_tasks = self.db.query(Task).count()

        # Tính Average KPI từ KpiSnapshot chính thức (không dùng công thức cũ)
        snapshots = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.period_key == period_key
        ).all()

        if snapshots:
            avg_kpi = sum(s.total_score for s in snapshots) / len(snapshots)
            avg_kpi = round(avg_kpi, 1)
        else:
            avg_kpi = 0

        # 2. Tính hiệu suất theo phòng ban dựa trên KPI của nhân viên
        depts = self.db.query(Department).all()
        dept_charts = []
        for dept in depts:
            dept_users = self.db.query(User).filter(
                User.department_id == dept.id,
                User.is_active == True
            ).all()

            dept_kpis = []
            for user in dept_users:
                snapshot = self.db.query(KpiSnapshot).filter(
                    KpiSnapshot.user_id == user.id,
                    KpiSnapshot.period_key == period_key
                ).first()
                if snapshot:
                    dept_kpis.append(snapshot.total_score)

            # Lấy trung bình KPI phòng ban từ nhân viên của phòng
            dept_score = sum(dept_kpis) / len(dept_kpis) if dept_kpis else 0
            dept_charts.append(DepartmentPerformance(
                id=dept.id,
                name=dept.name,
                score=round(dept_score, 1)
            ))

        # 3. Top Nhân viên xuất sắc (Top Performers từ KpiSnapshot)
        all_snapshots = self.db.query(KpiSnapshot, User).join(
            User, KpiSnapshot.user_id == User.id
        ).filter(
            KpiSnapshot.period_key == period_key,
            User.is_active == True
        ).order_by(KpiSnapshot.total_score.desc()).all()

        user_performances = []
        for snapshot, user in all_snapshots:
            dept_name = next(
                (d.name for d in depts if d.id == user.department_id),
                "Unknown"
            )
            user_performances.append(UserPerformance(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                department_name=dept_name,
                tasks_completed=snapshot.tasks_completed,
                kpi_score=round(snapshot.total_score, 1)
            ))

        top_performers = user_performances[:5]

        # 4. Recent Activity (Mock vì chưa có logging đầy đủ)
        recent_activities = [
            ActivityLogResponse(id=1, action="task", description="Trần Minh Bình đã hoàn thành task phân tích dữ liệu", time_ago="10 mins ago"),
            ActivityLogResponse(id=2, action="kpi", description="Hệ thống tự động cập nhật KPI tháng 5", time_ago="2 hours ago"),
            ActivityLogResponse(id=3, action="system", description="Đã thêm 2 nhân viên mới vào phòng Kỹ thuật", time_ago="Yesterday")
        ]

        # 5. AI Insights dựa trên data thật
        best_dept = max(dept_charts, key=lambda x: x.score) if dept_charts else None
        ai_insights = f"Hệ thống phát hiện năng suất toàn công ty đạt {avg_kpi}%. Phòng {best_dept.name if best_dept else ''} đang có hiệu suất cao nhất. Cần tập trung đẩy nhanh tiến độ các Task đang bị Blocked."

        return DashboardResponse(
            stats=DashboardStats(
                total_employees=total_users,
                active_departments=total_depts,
                completed_tasks=completed_tasks,
                avg_kpi=avg_kpi
            ),
            department_charts=dept_charts,
            top_performers=top_performers,
            recent_activities=recent_activities,
            ai_insights=ai_insights
        )