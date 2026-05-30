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
    """Chat with AI assistant (fallback only - no OpenAI integration yet)"""
    context_service = AIContextService(db)
    context = context_service.get_context_for_user(current_user)

    # Fallback response using context
    reply = _generate_fallback_reply(request.message, context, current_user)

    return AIChatResponseSchema(
        reply=reply,
        insights=[],
        used_fallback=True,
        evidence={"source": "fallback", "has_context": len(context) > 0}
    )


def _generate_fallback_reply(message: str, context: dict, user: User) -> str:
    """Generate fallback reply for chatbot"""
    msg_lower = message.lower()

    # KPI question
    if "kpi" in msg_lower or "diem" in msg_lower or "hieu suat" in msg_lower:
        if user.role == UserRole.STAFF:
            kpi = context.get("own_kpi_score", 0)
            return f"KPI thang nay cua ban la {kpi:.1f}. Ban da hoan thanh {context.get('own_done_tasks', 0)} task va co {context.get('own_overdue_tasks', 0)} task qua han."
        elif user.role == UserRole.MANAGER:
            kpi = context.get("team_avg_kpi", 0)
            return f"KPI trung binh cua team ban la {kpi:.1f}. Team co {context.get('team_size', 0)} thanh vien va {context.get('team_tasks_done', 0)} task da hoan thanh."
        else:
            kpi = context.get("system_avg_kpi", 0)
            return f"KPI trung binh he thong la {kpi:.1f}. Toan cong ty co {context.get('total_users', 0)} nhan vien va {context.get('system_tasks_done', 0)} task da hoan thanh."

    # Overdue task question
    if "qua han" in msg_lower or "task chiem" in msg_lower or "delay" in msg_lower:
        if user.role == UserRole.STAFF:
            return f"Ban hien co {context.get('own_overdue_tasks', 0)} task da qua han. Hay uu tien hoan thanh nhung task nay."
        else:
            return f"Hien co {context.get('team_overdue', 0) if user.role == UserRole.MANAGER else context.get('system_overdue', 0)} task qua han. Vui long theo doi."

    # Performance question
    if "hieu suat" in msg_lower or "nhan vien" in msg_lower or "team" in msg_lower:
        risk = context.get("risk_users", [])
        top = context.get("top_performers", [])

        reply = ""
        if risk:
            reply += f"Co {len(risk)} nhan vien co KPI thap. "
        if top:
            reply += f"Co {len(top)} nhan vien co hieu suat cao. "
        if not reply:
            reply = "Hieu suat team dang on dinh."

        return reply

    # Default
    return "Toi la tro ly AI cho he thong quan ly cong viec va KPI. Ban co the hoi toi ve: KPI, cong viec qua han, hieu suat team, hoac de xuat hanh dong."
