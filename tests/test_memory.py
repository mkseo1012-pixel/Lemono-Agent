import os
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path

from lemono.config import Settings
from lemono.evolution import PreferenceLearner
from lemono.memory import MemoryStore


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = MemoryStore(Path(self.temp.name) / "memory.db")

    def tearDown(self):
        self.temp.cleanup()

    def test_memory_search_is_tenant_isolated(self):
        self.store.add("alice", "fact", "Project codename is Citrus", "test")
        self.store.add("bob", "fact", "Project codename is Rocket", "test")
        self.assertEqual(
            [item.content for item in self.store.search("alice", "codename")],
            ["Project codename is Citrus"],
        )

    def test_explicit_preference_learning(self):
        learned = PreferenceLearner(self.store).learn("alice", "답변은 간결하게 해줘")
        self.assertEqual(learned, ["간결"])
        self.assertEqual(self.store.preferences("alice")[0].source, "explicit-user-statement")

    def test_forget_deletes_only_requested_user(self):
        self.store.add("alice", "fact", "one", "test")
        self.store.add("bob", "fact", "two", "test")
        self.assertEqual(self.store.delete_user("alice"), 1)
        self.assertEqual(self.store.recent("alice"), [])
        self.assertEqual(len(self.store.recent("bob")), 1)

    def test_settings_load_dotenv(self):
        env_file = Path(self.temp.name) / ".env"
        env_file.write_text("LEMONO_DEFAULT_PROVIDER=gemini\n", encoding="utf-8")
        previous = os.environ.pop("LEMONO_DEFAULT_PROVIDER", None)
        try:
            with chdir(self.temp.name):
                settings = Settings()
            self.assertEqual(settings.default_provider, "gemini")
        finally:
            os.environ.pop("LEMONO_DEFAULT_PROVIDER", None)
            if previous is not None:
                os.environ["LEMONO_DEFAULT_PROVIDER"] = previous
