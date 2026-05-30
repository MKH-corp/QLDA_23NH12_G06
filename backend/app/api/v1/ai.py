from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_authenticated_user
from app.models.user import User, UserRole
from app.schemas.ai import (
    AIInsightSchema, AIDashboardSummarySchema, AIChatRequestSchema, AIChatResponseSchema
)
from app.services.ai_context_service import AIContextService
from app.services.ai_insight_service import AIInsightService
from app.services.notification_engine import NotificationEngine
from app.services.openai_chat_service import OpenAIChatError, OpenAIChatService

router = APIRouter()


@router.get("/insights/me", response_model=list[AIInsightSchema])
def get_my_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """Get AI insights for current user (staff only gets own insights)"""
    context_service = AIContextService(db)
    context = context_service.get_context_for_user(current_user)

    if not context.get("own_kpi_score") and context.get("own_tasks", 0) == 0:
        return []

    insights = AIInsightService.generate_insights(context)
    return insights


@router.get("/insights/team", response_model=list[AIInsightSchema])
def get_team_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """Get AI insights for team (manager/admin only)"""
    if current_user.role == UserRole.STAFF:
        raise HTTPException(status_code=403, detail="Staff cannot view team insights")

    context_service = AIContextService(db)
    context = context_service.get_context_for_user(current_user)

    if not context.get("team_size") and not context.get("total_users"):
        return []

    insights = AIInsightService.generate_insights(context)
    return insights


@router.post("/insights/run", response_model=dict)
def run_ai_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """Run AI insights and notification checks"""
    if current_user.role == UserRole.STAFF:
        raise HTTPException(status_code=403, detail="Staff cannot trigger system insights")

    engine = NotificationEngine(db)

    if current_user.role == UserRole.MANAGER:
        team_users = db.query(User).filter(
            User.department_id == current_user.department_id,
            User.is_active == True
        ).all()
        for user in team_users:
            engine.check_user(user.id)
        return {
            "message": "AI insights and notifications run for your team",
            "users_processed": len(team_users)
        }
    else:
        engine.check_all()
        return {
            "message": "AI insights and notifications run for all users",
            "users_processed": "all"
        }


@router.get("/summary/dashboard", response_model=AIDashboardSummarySchema)
def get_ai_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """Get AI summary for dashboard"""
    context_service = AIContextService(db)
    context = context_service.get_context_for_user(current_user)

    summary = AIDashboardSummarySchema(
        user_id=current_user.id,
        role=context.get("role", "staff"),
        total_kpi_score=context.get("own_kpi_score") if current_user.role == UserRole.STAFF
                        else context.get("team_avg_kpi") if current_user.role == UserRole.MANAGER
                        else context.get("system_avg_kpi"),
        total_tasks_completed=context.get("own_done_tasks", 0) if current_user.role == UserRole.STAFF
                              else context.get("team_tasks_done", 0) if current_user.role == UserRole.MANAGER
                              else context.get("system_tasks_done", 0),
        overdue_tasks=context.get("own_overdue_tasks", 0) if current_user.role == UserRole.STAFF
                      else context.get("team_overdue", 0) if current_user.role == UserRole.MANAGER
                      else context.get("system_overdue", 0),
        near_deadline_tasks=context.get("own_near_deadline_tasks", 0) if current_user.role == UserRole.STAFF else 0,
        blocked_tasks=context.get("own_blocked_tasks", 0) if current_user.role == UserRole.STAFF else 0,
        risk_users=context.get("risk_users", []),
        top_performers=context.get("top_performers", []),
        team_overdue_count=context.get("team_overdue", 0) if current_user.role == UserRole.MANAGER else 0,
    )

    return summary


@router.post("/chat", response_model=AIChatResponseSchema)
def chat_with_ai(
    request: AIChatRequestSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_authenticated_user)
):
    """Chat with the OpenAI-backed assistant, with a local fallback."""
    context_service = AIContextService(db)
    context = context_service.get_context_for_user(current_user)
    chat_service = OpenAIChatService()

    if chat_service.is_configured:
        try:
            result = chat_service.generate_reply(request.message, context, request.history)
            return AIChatResponseSchema(
                reply=result.reply,
                insights=[],
                used_fallback=False,
                evidence={
                    "source": "openai",
                    "model": result.model,
                    "request_id": result.request_id,
                },
            )
        except OpenAIChatError:
            fallback_reason = "openai_unavailable"
    else:
        fallback_reason = "openai_not_configured"

    return AIChatResponseSchema(
        reply=_generate_fallback_reply(request.message, context, current_user),
        insights=[],
        used_fallback=True,
        evidence={
            "source": "fallback",
            "reason": fallback_reason,
            "has_context": len(context) > 0,
        },
    )


def _generate_fallback_reply(message: str, context: dict, user: User) -> str:
    """Generate fallback reply for chatbot"""
    msg_lower = message.lower()

    # KPI question
    if "kpi" in msg_lower or "điểm" in msg_lower or "diem" in msg_lower or "hiệu suất" in msg_lower or "hieu suat" in msg_lower:
        if user.role == UserRole.STAFF:
            kpi = context.get("own_kpi_score", 0)
            return f"KPI tháng này của bạn là {kpi:.1f}. Bạn đã hoàn thành {context.get('own_done_tasks', 0)} công việc và có {context.get('own_overdue_tasks', 0)} công việc quá hạn."
        elif user.role == UserRole.MANAGER:
            kpi = context.get("team_avg_kpi", 0)
            return f"KPI trung bình của nhóm là {kpi:.1f}. Nhóm có {context.get('team_size', 0)} thành viên và {context.get('team_tasks_done', 0)} công việc đã hoàn thành."
        else:
            kpi = context.get("system_avg_kpi", 0)
            return f"KPI trung bình hệ thống là {kpi:.1f}. Toàn công ty có {context.get('total_users', 0)} nhân viên và {context.get('system_tasks_done', 0)} công việc đã hoàn thành."

    # Overdue task question
    if "quá hạn" in msg_lower or "qua han" in msg_lower or "delay" in msg_lower:
        if user.role == UserRole.STAFF:
            return f"Bạn hiện có {context.get('own_overdue_tasks', 0)} công việc đã quá hạn. Hãy ưu tiên hoàn thành các công việc này."
        else:
            return f"Hiện có {context.get('team_overdue', 0) if user.role == UserRole.MANAGER else context.get('system_overdue', 0)} công việc quá hạn. Vui lòng theo dõi."

    # Performance question
    if "hiệu suất" in msg_lower or "hieu suat" in msg_lower or "nhân viên" in msg_lower or "nhan vien" in msg_lower or "team" in msg_lower:
        risk = context.get("risk_users", [])
        top = context.get("top_performers", [])

        reply = ""
        if risk:
            reply += f"Có {len(risk)} nhân viên có KPI thấp. "
        if top:
            reply += f"Có {len(top)} nhân viên có hiệu suất cao. "
        if not reply:
            reply = "Hiệu suất của nhóm đang ổn định."

        return reply

    # Default
    return "Tôi là trợ lý cho hệ thống quản lý công việc và KPI. Bạn có thể hỏi về KPI, công việc quá hạn, hiệu suất nhóm hoặc đề xuất hành động."
