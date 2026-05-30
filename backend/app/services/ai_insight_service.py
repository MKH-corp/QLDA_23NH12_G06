from app.schemas.ai import AIEvidenceSchema, AIInsightSchema


class AIInsightService:
    """Generate role-aware, rule-based insights from authorized context."""

    @staticmethod
    def generate_insights(context: dict) -> list[AIInsightSchema]:
        generators = {
            "staff": AIInsightService._generate_staff_insights,
            "manager": AIInsightService._generate_manager_insights,
            "admin": AIInsightService._generate_admin_insights,
        }
        generator = generators.get(context.get("role"))
        return generator(context) if generator else []

    @staticmethod
    def _generate_staff_insights(context: dict) -> list[AIInsightSchema]:
        insights = []
        overdue = context.get("own_overdue_tasks", 0)
        near_deadline = context.get("own_near_deadline_tasks", 0)
        blocked = context.get("own_blocked_tasks", 0)
        kpi = context.get("own_kpi_score", 0)

        if overdue:
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Bạn có {overdue} công việc quá hạn",
                message="Hãy ưu tiên xử lý các công việc quá hạn để hạn chế ảnh hưởng tới KPI.",
                severity="danger",
                recommendations=["Ưu tiên công việc quá hạn", "Trao đổi với quản lý nếu cần hỗ trợ"],
                evidence=AIEvidenceSchema(task_ids=context.get("own_overdue_task_ids", []), overdue_count=overdue),
            ))
        if near_deadline:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"Bạn có {near_deadline} công việc sắp tới hạn",
                message="Các công việc này sẽ tới hạn trong 2 ngày tới. Hãy sắp xếp thời gian xử lý.",
                severity="warning",
                recommendations=["Xử lý công việc có thời hạn gần nhất trước"],
                evidence=AIEvidenceSchema(task_ids=context.get("own_near_deadline_task_ids", []), near_deadline_count=near_deadline),
            ))
        if blocked:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"Bạn có {blocked} công việc bị chặn",
                message="Kiểm tra nguyên nhân và cập nhật trạng thái sau khi vấn đề được giải quyết.",
                severity="warning",
                recommendations=["Trao đổi với người phụ trách để tháo gỡ vướng mắc"],
                evidence=AIEvidenceSchema(task_ids=context.get("own_blocked_task_ids", []), blocked_count=blocked),
            ))
        if 0 < kpi < 70:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"KPI tháng này đang thấp: {kpi:.1f}",
                message="KPI hiện thấp hơn ngưỡng 70. Hãy tập trung hoàn thành công việc đúng hạn.",
                severity="warning",
                recommendations=["Hạn chế công việc quá hạn", "Chủ động xin hỗ trợ khi cần"],
                evidence=AIEvidenceSchema(kpi_score=kpi),
            ))
        if kpi >= 85:
            insights.append(AIInsightSchema(
                type="success",
                title="Bạn đang có hiệu suất tốt",
                message=f"KPI hiện tại đạt {kpi:.1f}. Hãy tiếp tục duy trì kết quả này.",
                severity="success",
                recommendations=["Chia sẻ kinh nghiệm với đồng đội"],
                evidence=AIEvidenceSchema(kpi_score=kpi, tasks_completed=context.get("own_done_tasks", 0)),
            ))
        return insights

    @staticmethod
    def _generate_manager_insights(context: dict) -> list[AIInsightSchema]:
        team_kpi = context.get("team_avg_kpi", 0)
        insights = [AIInsightSchema(
            type="info",
            title=f"KPI trung bình của nhóm: {team_kpi:.1f}",
            message=f"Nhóm có {context.get('team_size', 0)} thành viên và đã hoàn thành {context.get('team_tasks_done', 0)} công việc.",
            severity="info",
            recommendations=["Theo dõi KPI từng nhân viên", "Điều chỉnh phân công khi cần"],
            evidence=AIEvidenceSchema(kpi_score=team_kpi, tasks_completed=context.get("team_tasks_done", 0), overdue_count=context.get("team_overdue", 0)),
        )]
        risk_users = context.get("risk_users", [])
        if risk_users:
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Có {len(risk_users)} nhân viên cần hỗ trợ",
                message="Một số nhân viên có KPI dưới 70. Hãy rà soát khối lượng công việc và nguyên nhân.",
                severity="danger",
                recommendations=["Trao đổi trực tiếp với nhân viên", "Điều chỉnh phân công nếu cần"],
                evidence=AIEvidenceSchema(),
            ))
        return insights

    @staticmethod
    def _generate_admin_insights(context: dict) -> list[AIInsightSchema]:
        system_kpi = context.get("system_avg_kpi", 0)
        insights = [AIInsightSchema(
            type="info",
            title=f"KPI trung bình hệ thống: {system_kpi:.1f}",
            message=f"Hệ thống có {context.get('total_users', 0)} nhân viên thuộc {context.get('total_departments', 0)} phòng ban.",
            severity="info",
            recommendations=["Theo dõi xu hướng KPI toàn hệ thống"],
            evidence=AIEvidenceSchema(kpi_score=system_kpi, tasks_completed=context.get("system_tasks_done", 0), overdue_count=context.get("system_overdue", 0)),
        )]
        risk_users = context.get("risk_users", [])
        if risk_users:
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Có {len(risk_users)} nhân viên có KPI thấp",
                message="Cần phân tích nguyên nhân theo phòng ban và theo dõi kế hoạch cải thiện.",
                severity="danger",
                recommendations=["Phân tích KPI theo phòng ban", "Theo dõi kế hoạch cải thiện"],
                evidence=AIEvidenceSchema(),
            ))
        return insights
