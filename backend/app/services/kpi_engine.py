from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, UTC
from app.models.task import Task, TaskStatus
from app.models.kpi_snapshot import KpiSnapshot
from app.models.kpi_rule import KpiRule
from app.utils.task_ultis import (
    business_month_utc_range,
    business_period_key,
    completion_business_date,
)

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
        if not date_ref:
            date_ref = datetime.now(UTC)
        period_key = business_period_key(date_ref)
        period_start, period_end = business_month_utc_range(date_ref)

        # 1. Quét toàn bộ Task đã Done trong tháng của User
        done_tasks = self.db.query(Task).options(joinedload(Task.project)).filter(
            Task.assignee_id == user_id,
            Task.status == TaskStatus.DONE,
            Task.done_at >= period_start,
            Task.done_at < period_end,
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
            weight = float(task.estimated_hours or task.base_weight or 1.0)
            project_weight = float(task.project.project_weight or 1.0) if task.project else 1.0
            
            # Tính điểm gốc = hệ số * điểm chuẩn
            task_score = weight * self.rules['BASE_COMPLETION']
            breakdown["base_score"] += task_score

            # Check Deadline Manipulation / Overdue
            if task.deadline and task.done_at:
                if completion_business_date(task.done_at) <= task.deadline:
                    bonus = task_score * (self.rules['ON_TIME_BONUS'] - 1)
                    task_score += bonus
                    breakdown["on_time_bonus"] += bonus
                    breakdown["on_time_count"] += 1
                else:
                    days_late = max((completion_business_date(task.done_at) - task.deadline).days, 1)
                    penalty = task_score * min(days_late * 0.05, 0.5)
                    task_score -= penalty
                    breakdown["overdue_penalty_amount"] -= penalty
                    breakdown["overdue_count"] += 1

            # Check Reopen Abuse
            if task.reopen_count and task.reopen_count > 2:
                reopen_penalty = task_score * 0.1
                task_score -= reopen_penalty
                breakdown["reopen_penalty_amount"] -= reopen_penalty

            total_score += max(task_score * project_weight, 0) # Không để task âm điểm quá nặng kéo sập hệ thống

        for key in (
            "base_score",
            "on_time_bonus",
            "overdue_penalty_amount",
            "reopen_penalty_amount",
        ):
            breakdown[key] = round(breakdown[key], 2)

        snapshot = self._get_or_create_snapshot(user_id, period_key)

        snapshot.total_score = round(total_score, 2)
        snapshot.tasks_completed = breakdown["tasks_analyzed"]
        snapshot.tasks_overdue = breakdown["overdue_count"]
        snapshot.breakdown = breakdown

        self.db.commit()
        return snapshot

    def _get_or_create_snapshot(self, user_id: int, period_key: str) -> KpiSnapshot:
        snapshot = self.db.query(KpiSnapshot).filter(
            KpiSnapshot.user_id == user_id,
            KpiSnapshot.period_type == "MONTHLY",
            KpiSnapshot.period_key == period_key,
        ).first()
        if snapshot:
            return snapshot

        snapshot = KpiSnapshot(user_id=user_id, period_type="MONTHLY", period_key=period_key)
        self.db.add(snapshot)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            snapshot = self.db.query(KpiSnapshot).filter(
                KpiSnapshot.user_id == user_id,
                KpiSnapshot.period_type == "MONTHLY",
                KpiSnapshot.period_key == period_key,
            ).first()
            if snapshot is None:
                raise
        return snapshot
