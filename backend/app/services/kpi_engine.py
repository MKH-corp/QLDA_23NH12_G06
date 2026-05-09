from sqlalchemy.orm import Session
from sqlalchemy import extract, and_
from datetime import datetime, UTC
from app.models.task import Task, TaskStatus
from app.models.kpi_snapshot import KpiSnapshot
from app.models.kpi_rule import KpiRule

class KpiEngine:
    def __init__(self, db: Session):
        self.db = db
        # Cache rules in memory for this transaction to avoid N+1 DB calls
        self.rules = {r.code: r.multiplier for r in self.db.query(KpiRule).filter(KpiRule.is_active == True).all()}
        
        # Default fallbacks if DB is empty
        self.rules.setdefault('BASE_COMPLETION', 1.0)
        self.rules.setdefault('ON_TIME_BONUS', 1.2)
        self.rules.setdefault('OVERDUE_PENALTY', 0.5)
        self.rules.setdefault('REOPEN_PENALTY', -5.0)

    def recalculate_monthly_kpi(self, user_id: int, date_ref: datetime = None):
        """Hàm này được trigger EVENT-DRIVEN từ TaskService"""
        if not date_ref: date_ref = datetime.now(UTC)
        current_month = date_ref.month
        current_year = date_ref.year
        period_key = f"{current_year}-{current_month:02d}"

        # 1. Quét toàn bộ Task đã Done trong tháng của User
        done_tasks = self.db.query(Task).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.DONE,
            extract('year', Task.done_at) == current_year,
            extract('month', Task.done_at) == current_month
        ).all()

        # 2. Khởi tạo Tracking Variables (Explainability)
        breakdown = {
            "base_score": 0.0,
            "on_time_bonus": 0.0,
            "overdue_penalty_amount": 0.0,
            "reopen_penalty_amount": 0.0,
            "tasks_analyzed": len(done_tasks),
            "overdue_count": 0,
            "on_time_count": 0
        }
        
        total_score = 0.0

        # 3. ANTI-CHEATING & SCORING LOGIC
        for task in done_tasks:
            # Lấy thẳng base_weight làm hệ số ưu tiên (mặc định 1.0 nếu rỗng)
            weight = float(task.base_weight) if task.base_weight else 1.0
            
            # Tính điểm gốc = hệ số * điểm chuẩn
            task_score = weight * self.rules['BASE_COMPLETION']
            breakdown["base_score"] += task_score

            # Check Deadline Manipulation / Overdue
            if task.deadline and task.done_at:
                if task.done_at.date() <= task.deadline:
                    bonus = task_score * (self.rules['ON_TIME_BONUS'] - 1)
                    task_score += bonus
                    breakdown["on_time_bonus"] += bonus
                    breakdown["on_time_count"] += 1
                else:
                    penalty = task_score * (1 - self.rules['OVERDUE_PENALTY'])
                    task_score -= penalty
                    breakdown["overdue_penalty_amount"] -= penalty
                    breakdown["overdue_count"] += 1

            # Check Reopen Abuse
            if task.reopen_count and task.reopen_count > 0:
                reopen_penalty = task.reopen_count * self.rules['REOPEN_PENALTY']
                task_score += reopen_penalty # Penalty is negative
                breakdown["reopen_penalty_amount"] += reopen_penalty

            total_score += max(task_score, 0) # Không để task âm điểm quá nặng kéo sập hệ thống

        # 4. UPSERT SNAPSHOT TABLE (Tối ưu truy vấn)
        snapshot = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.user_id == user_id,
            KpiSnapshot.period_key == period_key
        ).first()

        if not snapshot:
            snapshot = KpiSnapshot(user_id=user_id, period_type="MONTHLY", period_key=period_key)
            self.db.add(snapshot)

        snapshot.total_score = round(total_score, 2)
        snapshot.tasks_completed = breakdown["tasks_analyzed"]
        snapshot.tasks_overdue = breakdown["overdue_count"]
        snapshot.breakdown = breakdown

        self.db.commit()
        return snapshot