"""Create local .env and generate a complete Claude configuration fragment."""
import json
import shutil
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
if not (root / ".env").exists():
    shutil.copyfile(root / ".env.example", root / ".env")
configuration = {"mcpServers": {"task-tracker": {
    "command": sys.executable, "args": [str(root / "server.py")]
}}}
(root / "claude_desktop_config.json").write_text(json.dumps(configuration, indent=2) + "\n", encoding="utf-8")
print("Created claude_desktop_config.json; merge its mcpServers entry into Claude Desktop's config.")
