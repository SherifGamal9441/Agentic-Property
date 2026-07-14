import os
import subprocess
import sys
from pathlib import Path


def test_settings_load_without_a_groq_key(tmp_path):
    env = os.environ.copy()
    env.pop("GROQ_API_KEY", None)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[2])

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from config.pydantic.settings import settings; "
            "assert settings.groq_api_key is None",
        ],
        env=env,
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )

    assert result.returncode == 0, result.stderr
