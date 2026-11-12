"""Use the repository's local .env as the source of configuration."""
from pathlib import Path

from dotenv import load_dotenv


def load_environment(path: Path) -> bool:
    return load_dotenv(dotenv_path=path, override=True)
