import re
import unittest
from pathlib import Path


class MigrationGraphTests(unittest.TestCase):
    def test_migration_graph_has_single_head(self) -> None:
        versions_dir = Path(__file__).parents[1] / "alembic" / "versions"
        revisions: set[str] = set()
        parents: set[str] = set()

        for path in versions_dir.glob("*.py"):
            content = path.read_text(encoding="utf-8")
            revision = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
            self.assertIsNotNone(revision, f"Missing revision in {path.name}")
            revisions.add(revision.group(1))

            down_revision = re.search(r"^down_revision\s*=\s*(.+)$", content, re.MULTILINE)
            self.assertIsNotNone(down_revision, f"Missing down_revision in {path.name}")
            parents.update(re.findall(r"['\"]([^'\"]+)['\"]", down_revision.group(1)))

        self.assertEqual(revisions - parents, {"20260531_001"})
        self.assertTrue(parents - {"None"} <= revisions)

    def test_merge_revision_joins_notification_and_reopen_branches(self) -> None:
        merge_path = (
            Path(__file__).parents[1]
            / "alembic"
            / "versions"
            / "20260531_001_merge_notification_and_reopen_heads.py"
        )
        content = merge_path.read_text(encoding="utf-8")
        self.assertIn('down_revision = ("20260530_001", "3fadc5024285")', content)


if __name__ == "__main__":
    unittest.main()
