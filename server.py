"""Launch through Claude Desktop or `python server.py` (stdio transport)."""
import argparse
import sys
from pathlib import Path

from tasktracker.config import Settings
from tasktracker.server import create_server


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config-dir", type=Path, default=Path(__file__).resolve().parent)
    args = parser.parse_args()
    try:
        server = create_server(Settings.load(args.config_dir.resolve()))
    except Exception:
        print("Task tracker startup failed. Check .env and directory permissions.", file=sys.stderr)
        raise SystemExit(1) from None
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
