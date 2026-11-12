"""Load local configuration without replacing process environment variables."""
from pathlib import Path

from dotenv import load_dotenv


def load_environment(path: Path) -> bool:
    return load_dotenv(dotenv_path=path, override=False)
