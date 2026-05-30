import json
import unittest
from unittest.mock import MagicMock, patch

from app.api.v1.ai import chat_with_ai
from app.models.user import UserRole
from app.schemas.ai import AIChatMessageSchema, AIChatRequestSchema
from app.services.openai_chat_service import OpenAIChatResult, OpenAIChatService
from tests.helpers import close_session, create_department, create_user, make_session


class OpenAIChatServiceTests(unittest.TestCase):
    def test_generate_reply_calls_responses_api_with_sanitized_context(self) -> None:
        response = MagicMock()
        response.__enter__.return_value = response
        response.headers = {"x-request-id": "req_test"}
        response.read.return_value = json.dumps({
            "model": "gpt-test",
            "output": [{
                "type": "message",
                "content": [{"type": "output_text", "text": "Phản hồi từ OpenAI"}],
            }],
        }).encode("utf-8")
        service = OpenAIChatService(
            api_key="test-key",
            model="gpt-test",
            base_url="https://api.openai.test/v1",
            timeout_seconds=3,
        )

        with patch("app.services.openai_chat_service.urlopen", return_value=response) as urlopen_mock:
            result = service.generate_reply(
                "KPI nhóm thế nào?",
                {
                    "role": "manager",
                    "team_avg_kpi": 82,
                    "team_users": [{"id": 1, "name": "An", "email": "secret@example.com"}],
                    "risk_users": [{"user_id": 1, "name": "An", "kpi": 60, "email": "secret@example.com"}],
                },
                [AIChatMessageSchema(role="assistant", content="Bạn muốn xem gì?")],
            )

        request = urlopen_mock.call_args.args[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(result.reply, "Phản hồi từ OpenAI")
        self.assertEqual(result.request_id, "req_test")
        self.assertEqual(payload["model"], "gpt-test")
        self.assertFalse(payload["store"])
        self.assertNotIn("secret@example.com", json.dumps(payload))
        self.assertEqual(payload["input"][-1], {"role": "user", "content": "KPI nhóm thế nào?"})


class AIChatEndpointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = make_session()
        department = create_department(self.db, "Engineering")
        self.staff = create_user(self.db, department, "staff@example.com", UserRole.STAFF)

    def tearDown(self) -> None:
        close_session(self.db)

    def test_chat_uses_local_fallback_when_openai_is_not_configured(self) -> None:
        with patch("app.api.v1.ai.OpenAIChatService") as service_class:
            service_class.return_value.is_configured = False
            response = chat_with_ai(AIChatRequestSchema(message="KPI của tôi"), self.db, self.staff)

        self.assertTrue(response.used_fallback)
        self.assertEqual(response.evidence["reason"], "openai_not_configured")

    def test_chat_returns_openai_reply_when_configured(self) -> None:
        with patch("app.api.v1.ai.OpenAIChatService") as service_class:
            service_class.return_value.is_configured = True
            service_class.return_value.generate_reply.return_value = OpenAIChatResult(
                reply="KPI của bạn đang ổn định.",
                model="gpt-test",
                request_id="req_test",
            )
            response = chat_with_ai(AIChatRequestSchema(message="KPI của tôi"), self.db, self.staff)

        self.assertFalse(response.used_fallback)
        self.assertEqual(response.reply, "KPI của bạn đang ổn định.")
        self.assertEqual(response.evidence["source"], "openai")


if __name__ == "__main__":
    unittest.main()
