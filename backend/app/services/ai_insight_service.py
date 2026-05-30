from app.schemas.ai import AIInsightSchema, AIEvidenceSchema


class AIInsightService:
    """Service to generate insights from context data"""

    @staticmethod
    def generate_insights(context: dict) -> list[AIInsightSchema]:
        """Generate rule-based insights from context"""
        insights = []
        role = context.get("role")

        if role == "staff":
            insights.extend(AIInsightService._generate_staff_insights(context))
        elif role == "manager":
            insights.extend(AIInsightService._generate_manager_insights(context))
        elif role == "admin":
            insights.extend(AIInsightService._generate_admin_insights(context))

        return insights

    @staticmethod
    def _generate_staff_insights(context: dict) -> list[AIInsightSchema]:
        """Generate insights for staff"""
        insights = []

        # Overdue tasks warning
        if context.get("own_overdue_tasks", 0) > 0:
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Ban co {context['own_overdue_tasks']} cong viec qua han",
                message=f"Ban hien dang co {context['own_overdue_tasks']} task da qua deadline. Hay uu tien hoan thanh nhung task nay ngay lap tuc de tranh anh huong den KPI.",
                severity="danger",
                recommendations=[
                    "Uu tien hoan thanh cac task qua han",
                    "Lien he quan ly neu co van de can phong ngua",
                    "Tao ke hoach chi tiet de hoan thanh trong 24 gio"
                ],
                evidence=AIEvidenceSchema(
                    task_ids=context.get("own_overdue_task_ids", []),
                    overdue_count=context.get("own_overdue_tasks", 0),
                )
            ))

        # Near deadline tasks warning
        if context.get("own_near_deadline_tasks", 0) > 0:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"Ban co {context['own_near_deadline_tasks']} cong viec sap toi han",
                message=f"Phat hien {context['own_near_deadline_tasks']} task se toi deadline trong 2 ngay toi. Hay sap xep thoi gian de hoan thanh dung han.",
                severity="warning",
                recommendations=[
                    "Sap xep thoi gian hop ly cho cac task nay",
                    "Tap trung vao cac task co deadline som nhat",
                    "Tranh hoan thanh trong phut chot"
                ],
                evidence=AIEvidenceSchema(
                    task_ids=context.get("own_near_deadline_task_ids", []),
                    near_deadline_count=context.get("own_near_deadline_tasks", 0),
                )
            ))

        # Blocked tasks
        if context.get("own_blocked_tasks", 0) > 0:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"Ban co {context['own_blocked_tasks']} cong viec bi chan",
                message=f"Co {context['own_blocked_tasks']} task dang o trang thai blocked. Vui long kiem tra va giai quyet cac van de de tiep tuc cong viec.",
                severity="warning",
                recommendations=[
                    "Xem xet chi tiet ly do cac task bi chan",
                    "Tim cach khac phuc hoac lien he quan ly",
                    "Cap nhat trang thai task khi van de duoc giai quyet"
                ],
                evidence=AIEvidenceSchema(
                    task_ids=context.get("own_blocked_task_ids", []),
                    blocked_count=context.get("own_blocked_tasks", 0),
                )
            ))

        # Low KPI warning
        kpi = context.get("own_kpi_score", 0)
        if kpi < 70 and kpi > 0:
            insights.append(AIInsightSchema(
                type="warning",
                title=f"KPI thang nay thap: {kpi:.1f}",
                message=f"Diem KPI cua ban thang nay la {kpi:.1f}, thap hon nguong 70. Hay tap trung hoan thanh cac task va cai thien hieu suat cong viec.",
                severity="warning",
                recommendations=[
                    "Tap trung hoan thanh cac task con lai",
                    "Tranh de task qua han",
                    "Xin ho tro tu quan ly neu can thiet"
                ],
                evidence=AIEvidenceSchema(
                    kpi_score=kpi,
                    tasks_completed=context.get("own_kpi_snapshot", {}).get("tasks_completed", 0) if context.get("own_kpi_snapshot") else 0
                )
            ))

        # Excellent performance
        if kpi >= 85:
            insights.append(AIInsightSchema(
                type="success",
                title="Ban la nhan vien xuat sac",
                message=f"Chuc mung! Ban da dat KPI {kpi:.1f} va hoan thanh {context.get('own_done_tasks', 0)} task. Hay tiep tuc giu vung thanh tich nay!",
                severity="success",
                recommendations=[
                    "Tiep tuc gia trong hieu suat cong viec",
                    "Chia se kinh nghiem voi dong doi",
                    "Tham gia lam quy trinh hop tac noi bo"
                ],
                evidence=AIEvidenceSchema(
                    kpi_score=kpi,
                    tasks_completed=context.get("own_done_tasks", 0)
                )
            ))

        return insights

    @staticmethod
    def _generate_manager_insights(context: dict) -> list[AIInsightSchema]:
        """Generate insights for manager"""
        insights = []

        # Team KPI summary
        team_kpi = context.get("team_avg_kpi", 0)
        insights.append(AIInsightSchema(
            type="info",
            title=f"Tong quan team KPI: {team_kpi:.1f}",
            message=f"KPI trung binh team ban la {team_kpi:.1f}. Team co {context.get('team_size', 0)} thanh vien, {context.get('team_tasks_done', 0)} task da hoan thanh.",
            severity="info",
            recommendations=[
                "Theo doi kpi tung nhan vien",
                "Xem xet dieu chinh phan cong neu can"
            ],
            evidence=AIEvidenceSchema(
                kpi_score=team_kpi,
                tasks_completed=context.get("team_tasks_done", 0),
                overdue_count=context.get("team_overdue", 0)
            )
        ))

        # Risk users warning
        risk_users = context.get("risk_users", [])
        if risk_users:
            risk_names = ", ".join([u["name"] for u in risk_users[:3]])
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Co {len(risk_users)} nhan vien co nguy co",
                message=f"Phat hien {len(risk_users)} nhan vien co KPI thap (< 70): {risk_names}. Hay cau tao va ho tro theo doi.",
                severity="danger",
                recommendations=[
                    "Lien he cac nhan vien co KPI thap",
                    "Dieu chinh phan cong neu can thiet",
                    "Tham gia tranh luan de tim giai phap"
                ],
                evidence=AIEvidenceSchema()
            ))

        # Top performers
        top_performers = context.get("top_performers", [])
        if top_performers:
            top_names = ", ".join([u["name"] for u in top_performers[:3]])
            insights.append(AIInsightSchema(
                type="success",
                title=f"Nhan vien xuat sac: {top_names}",
                message=f"Chuc mung {len(top_performers)} nhan vien co hieu suat cao (KPI >= 85). Hay ghi nhan va khuyen khich ho.",
                severity="success",
                recommendations=[
                    "Ghi nhan va khuyen khich hieu suat",
                    "Cau tao phuong phap lam viec cua ho",
                    "De xuat thang tien hoac phuot thuong"
                ],
                evidence=AIEvidenceSchema()
            ))

        return insights

    @staticmethod
    def _generate_admin_insights(context: dict) -> list[AIInsightSchema]:
        """Generate insights for admin"""
        insights = []

        # System KPI overview
        system_kpi = context.get("system_avg_kpi", 0)
        insights.append(AIInsightSchema(
            type="info",
            title=f"Tong quan KPI he thong: {system_kpi:.1f}",
            message=f"KPI trung binh cong ty la {system_kpi:.1f}. He thong co {context.get('total_users', 0)} nhan vien, {context.get('total_departments', 0)} phong ban.",
            severity="info",
            recommendations=[
                "Theo doi KPI toan he thong",
                "Phan tich xu huong hieu suat"
            ],
            evidence=AIEvidenceSchema(
                kpi_score=system_kpi,
                tasks_completed=context.get("system_tasks_done", 0),
                overdue_count=context.get("system_overdue", 0)
            )
        ))

        # Risk departments/users
        risk_users = context.get("risk_users", [])
        if risk_users:
            risk_count = len(risk_users)
            insights.append(AIInsightSchema(
                type="danger",
                title=f"Co {risk_count} nhan vien co KPI thap",
                message=f"Phat hien {risk_count} nhan vien co KPI < 70. Dieu nay co the anh huong toi hieu suat chung cua cong ty.",
                severity="danger",
                recommendations=[
                    "Phan tich chi tiet tai sao KPI thap",
                    "Ho tro cac nhan vien co nguy co",
                    "Xem xet dieu chinh chien luoc kinh doanh"
                ],
                evidence=AIEvidenceSchema()
            ))

        return insights
