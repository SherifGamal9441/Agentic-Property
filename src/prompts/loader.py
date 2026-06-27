from pathlib import Path
import yaml

_PROMPTS_DIR = Path(__file__).parent

def load_prompt(filename: str) -> dict:
    with open(_PROMPTS_DIR / filename) as f:
        return yaml.safe_load(f)
