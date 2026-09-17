"""File-based configuration. No credentials or system environment required."""
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    database: Path
    calls: int = 20
    seconds: int = 60

    @classmethod
    def load(cls, root: Path) -> "Settings":
        # dotenv_values usage reference: https://bbc2.github.io/python-dotenv/
        # Disable expansion so configuration never reads system variables.
        values = dotenv_values(root / ".env", interpolate=False)
        relative = Path(values.get("DATABASE_FILE") or "data/tasks.sqlite3")
        database = (root / relative).resolve()
        if relative.is_absolute() or not database.is_relative_to(root.resolve()):
            raise ValueError("DATABASE_FILE must stay inside the project directory.")
        calls = int(values.get("RATE_LIMIT_CALLS") or "20")
        seconds = int(values.get("RATE_LIMIT_SECONDS") or "60")
        if not 1 <= calls <= 1000 or not 1 <= seconds <= 3600:
            raise ValueError("Invalid rate limit configuration.")
        return cls(database, calls, seconds)
