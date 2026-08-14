import os
import stat
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lemono.config import Settings, read_dotenv
from lemono.setup import run_setup


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / ".env"

    def tearDown(self):
        self.temp.cleanup()

    def test_setup_saves_private_config_and_settings_load_it(self):
        answers = iter(["2", "grok-test", "claude,gemini"])
        run_setup(
            config_path=self.path,
            input_fn=lambda _prompt: next(answers),
            secret_fn=lambda _prompt: "secret-value",
            output_fn=lambda _message: None,
        )
        values = read_dotenv(self.path)
        self.assertEqual(values["LEMONO_DEFAULT_PROVIDER"], "grok")
        self.assertEqual(values["XAI_API_KEY"], "secret-value")
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o600)
        with mock.patch.dict(os.environ, {}, clear=True):
            settings = Settings(data_dir=self.path.parent)
        self.assertEqual(settings.default_model, "grok-test")

    def test_setup_preserves_saved_key_when_input_is_blank(self):
        self.path.write_text("OPENAI_API_KEY=existing\n", encoding="utf-8")
        answers = iter(["openai", "", ""])
        run_setup(
            config_path=self.path,
            input_fn=lambda _prompt: next(answers),
            secret_fn=lambda _prompt: "",
            output_fn=lambda _message: None,
        )
        self.assertEqual(read_dotenv(self.path)["OPENAI_API_KEY"], "existing")

    def test_setup_rejects_unknown_fallback(self):
        answers = iter(["1", "gpt-5", "unknown"])
        with self.assertRaises(ValueError):
            run_setup(
                config_path=self.path,
                input_fn=lambda _prompt: next(answers),
                secret_fn=lambda _prompt: "secret",
                output_fn=lambda _message: None,
            )
