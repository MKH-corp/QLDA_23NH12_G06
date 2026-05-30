"""
ProjectProgressEngine — tính tiến độ thực tế, không hardcode.

Công thức:
  progress = (task_score × 0.7) + (milestone_score × 0.3)

  task_score = (Σ base_weight của done tasks) / (Σ tổng base_weight)
             - overdue_penalty (5% mỗi task quá hạn, tối đa 20%)
             - blocked_penalty (2% mỗi blocked task)
             - reopen_penalty  (1% mỗi lần reopen)

  milestone_score = done_milestone_weight / total_milestone_weight
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectMilestone
from app.models.task import Task, TaskStatus
from app.utils.task_ultis import business_today


class ProjectProgressEngine:
    # Trọng số trong công thức tổng hợp
    TASK_WEIGHT      = 0.70
    MILESTONE_WEIGHT = 0.30

    # Penalty rates
    OVERDUE_PENALTY_PER_TASK  = 0.05   # 5% mỗi task quá hạn
    MAX_OVERDUE_PENALTY       = 0.20   # không phạt quá 20%
    BLOCKED_PENALTY_PER_TASK  = 0.02
    REOPEN_PENALTY_PER_COUNT  = 0.01

    def __init__(self, db: Session) -> None:
        self.db = db

    def calculate(self, project: Project) -> float:
        """
        Tính progress_percentage [0..100] cho project.
        Ghi kết quả vào project.progress_percentage và commit.
        """
        task_score      = self._task_score(project)
        milestone_score = self._milestone_score(project)

        raw = (task_score * self.TASK_WEIGHT) + (milestone_score * self.MILESTONE_WEIGHT)
        progress = round(max(0.0, min(100.0, raw * 100)), 2)

        project.progress_percentage = progress
        self.db.add(project)
        self.db.commit()
        return progress

    def get_breakdown(self, project: Project) -> dict:
        """Trả về dict giải thích chi tiết cách tính — dùng cho analytics."""
        tasks = self.db.query(Task).filter(Task.project_id == project.id).all()
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id
        ).all()

        today = business_today()
        total_weight    = sum(t.base_weight or 1 for t in tasks)
        done_weight     = sum(t.base_weight or 1 for t in tasks if t.status == TaskStatus.DONE)
        overdue_count   = sum(
            1 for t in tasks
            if t.status != TaskStatus.DONE and t.deadline and t.deadline < today
        )
        blocked_count   = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
        reopen_total    = sum(t.reopen_count or 0 for t in tasks)

        raw_task = (done_weight / total_weight) if total_weight else 0
        overdue_penalty  = min(overdue_count  * self.OVERDUE_PENALTY_PER_TASK, self.MAX_OVERDUE_PENALTY)
        blocked_penalty  = blocked_count * self.BLOCKED_PENALTY_PER_TASK
        reopen_penalty   = reopen_total  * self.REOPEN_PENALTY_PER_COUNT
        task_score = max(0.0, raw_task - overdue_penalty - blocked_penalty - reopen_penalty)

        total_ms_weight = sum(m.weight for m in milestones) or 1
        done_ms_weight  = sum(m.weight for m in milestones if m.is_completed)
        milestone_score = done_ms_weight / total_ms_weight

        return {
            "task_score":        round(task_score, 4),
            "milestone_score":   round(milestone_score, 4),
            "total_tasks":       len(tasks),
            "done_tasks":        sum(1 for t in tasks if t.status == TaskStatus.DONE),
            "overdue_tasks":     overdue_count,
            "blocked_tasks":     blocked_count,
            "reopen_total":      reopen_total,
            "overdue_penalty":   round(overdue_penalty, 4),
            "blocked_penalty":   round(blocked_penalty, 4),
            "reopen_penalty":    round(reopen_penalty,  4),
            "total_milestones":  len(milestones),
            "done_milestones":   sum(1 for m in milestones if m.is_completed),
            "final_progress":    round((task_score * self.TASK_WEIGHT + milestone_score * self.MILESTONE_WEIGHT) * 100, 2),
        }

    # ── private helpers ─────────────────────────────────────────────────

    def _task_score(self, project: Project) -> float:
        tasks = self.db.query(Task).filter(Task.project_id == project.id).all()
        if not tasks:
            return 0.0

        today        = business_today()
        total_weight = sum(t.base_weight or 1 for t in tasks)
        done_weight  = sum(t.base_weight or 1 for t in tasks if t.status == TaskStatus.DONE)

        overdue_count = sum(
            1 for t in tasks
            if t.status != TaskStatus.DONE and t.deadline and t.deadline < today
        )
        blocked_count = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
        reopen_total  = sum(t.reopen_count or 0 for t in tasks)

        raw = done_weight / total_weight if total_weight else 0
        penalty = (
            min(overdue_count * self.OVERDUE_PENALTY_PER_TASK, self.MAX_OVERDUE_PENALTY)
            + blocked_count * self.BLOCKED_PENALTY_PER_TASK
            + reopen_total  * self.REOPEN_PENALTY_PER_COUNT
        )
        return max(0.0, raw - penalty)

    def _milestone_score(self, project: Project) -> float:
        milestones = self.db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id
        ).all()
        if not milestones:
            return 0.0
        total = sum(m.weight for m in milestones) or 1
        done  = sum(m.weight for m in milestones if m.is_completed)
        return done / total
