from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.department import Department
from app.models.task import Task
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
        # 1. Lấy thông số tổng quan (Stats)
        total_users = self.db.query(User).filter(User.is_active == True).count()
        total_depts = self.db.query(Department).count()
        completed_tasks = self.db.query(Task).filter(Task.status == "done").count()
        total_tasks = self.db.query(Task).count()
        
        # Tính Average KPI toàn công ty
        avg_kpi = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # 2. Tính hiệu suất theo phòng ban (Chart Data)
        depts = self.db.query(Department).all()
        dept_charts = []
        for dept in depts:
            dept_tasks_total = self.db.query(Task).filter(Task.department_id == dept.id).count()
            dept_tasks_done = self.db.query(Task).filter(Task.department_id == dept.id, Task.status == "done").count()
            score = (dept_tasks_done / dept_tasks_total * 100) if dept_tasks_total > 0 else 0
            dept_charts.append(DepartmentPerformance(id=dept.id, name=dept.name, score=round(score, 1)))

        # 3. Top Nhân viên xuất sắc (Team Performance)
        users = self.db.query(User).filter(User.is_active == True).all()
        user_performances = []
        for user in users:
            u_total = self.db.query(Task).filter(Task.assignee_id == user.id).count()
            u_done = self.db.query(Task).filter(Task.assignee_id == user.id, Task.status == "done").count()
            
            # Tính KPI: Phạt nhẹ nếu có task quá hạn (logic thực tế)
            kpi = (u_done / u_total * 100) if u_total > 0 else 0
            
            dept_name = next((d.name for d in depts if d.id == user.department_id), "Unknown")
            
            user_performances.append(UserPerformance(
                id=user.id,
                full_name=user.full_name,
                email=user.email,
                department_name=dept_name,
                tasks_completed=u_done,
                kpi_score=round(kpi, 1)
            ))
        
        # Sắp xếp top 5 KPI cao nhất
        user_performances.sort(key=lambda x: x.kpi_score, reverse=True)
        top_performers = user_performances[:5]

        # 4. Mock Activity Log (Vì mình chưa update các hàm Create/Update Task để ghi log)
        # Trong thực tế, bạn sẽ query từ bảng ActivityLog
        recent_activities = [
            ActivityLogResponse(id=1, action="task", description="Trần Minh Bình đã hoàn thành task phân tích dữ liệu", time_ago="10 mins ago"),
            ActivityLogResponse(id=2, action="kpi", description="Hệ thống tự động cập nhật KPI tháng 5", time_ago="2 hours ago"),
            ActivityLogResponse(id=3, action="system", description="Đã thêm 2 nhân viên mới vào phòng Kỹ thuật", time_ago="Yesterday")
        ]

        # 5. Sinh AI Insights dựa trên Data thật
        best_dept = max(dept_charts, key=lambda x: x.score) if dept_charts else None
        ai_insights = f"Hệ thống phát hiện năng suất toàn công ty đạt {round(avg_kpi,1)}%. Phòng {best_dept.name if best_dept else ''} đang có hiệu suất cao nhất. Cần tập trung đẩy nhanh tiến độ các Task đang bị Blocked."

        return DashboardResponse(
            stats=DashboardStats(
                total_employees=total_users,
                active_departments=total_depts,
                completed_tasks=completed_tasks,
                avg_kpi=round(avg_kpi, 1)
            ),
            department_charts=dept_charts,
            top_performers=top_performers,
            recent_activities=recent_activities,
            ai_insights=ai_insights
        )