import os
import subprocess
import sys


def test_settings_load_without_a_groq_key():
    env = os.environ.copy()
    env.pop("GROQ_API_KEY", None)

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
    )

    assert result.returncode == 0, result.stderr
