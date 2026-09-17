import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from tasktracker.config import Settings
from tasktracker.security import RateLimiter, RateLimitError, clean_text
from tasktracker.storage import TaskStore


class CoreTests(unittest.TestCase):
    def test_sql_injection_is_literal_data(self):
        with tempfile.TemporaryDirectory() as folder:
            store = TaskStore(Path(folder) / "tasks.db")
            payload = "x'); DROP TABLE tasks; --"
            store.add(payload, "high", None)
            store.add("Legitimate task", "low", None)
            self.assertEqual(store.list(payload, 10)[0]["title"], payload)
            self.assertEqual(store.list("' OR 1=1 --", 10), [])
            self.assertEqual(len(store.list("", 10)), 2)
            self.assertEqual(len(TaskStore(store.path).list("", 10)), 2)

    def test_validation(self):
        for text in [" ", "a" * 201, "bad\x00text", "bad\ntext"]:
            with self.assertRaises(ValueError):
                clean_text(text, "title", 200)
        self.assertEqual(clean_text(" O'Brien ", "title", 200), "O'Brien")

    def test_rate_limit_expiry(self):
        now = [100.0]
        limiter = RateLimiter(2, 60, lambda: now[0])
        limiter.check()
        limiter.check()
        with self.assertRaises(RateLimitError):
            limiter.check()
        now[0] = 160.0
        limiter.check()

    def test_concurrent_limit(self):
        limiter = RateLimiter(5, 60)
        def attempt(_):
            try:
                limiter.check()
                return 1
            except RateLimitError:
                return 0
        with ThreadPoolExecutor(max_workers=8) as pool:
            self.assertEqual(sum(pool.map(attempt, range(40))), 5)

    def test_config_rejects_path_escape(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / ".env").write_text("DATABASE_FILE=../outside.db\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                Settings.load(root)


if __name__ == "__main__":
    unittest.main()
