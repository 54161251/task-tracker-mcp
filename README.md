# Local Task Tracker MCP

A Python/SQLite MCP server that lets an assistant save and retrieve tasks locally. Built by Kaiwen Ji as coursework with OpenAI Codex assistance.

**Engineering focus:** persistent storage, MCP tool/prompt design, parameterized SQL, input validation, and shared rate limiting.

## What it does

| Interface | Purpose |
|---|---|
| `add_task` | Store a title, priority, and optional due date |
| `list_tasks` | Search and retrieve tasks in priority/due-date order |
| `plan_day` | Give the host model a planning prompt with a snapshot of saved tasks |

The server does not call an LLM itself. Claude Desktop launches it over stdio; SQLite keeps tasks between sessions. No hosted service or API key is required by the server.

## Quick start — Windows

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/), then clone this repository.

```powershell
uv venv --python 3.13
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
python configure.py
python -m unittest discover -s tests -v
python demo_checks.py
```

The demo starts a real MCP server with a disposable database and checks tool/prompt behavior, invalid input, SQL-injection handling, and rate limiting. Expected final line: `ALL MCP DEMO CHECKS PASSED (temporary database cleaned up)`. This is an expected result, not a claim of a new test run for this documentation update.

## Connect Claude Desktop

1. Run `python configure.py` in the virtual environment to generate paths for your machine.
2. Merge the generated `task-tracker` entry from `claude_desktop_config.json` into your Claude Desktop `mcpServers` configuration. Preserve other entries.
3. Fully restart Claude Desktop. Ask it to add a task, then list tasks.
4. Use the `plan_day` prompt when supported by the client.

Running `python server.py` alone waits silently for MCP protocol input. This is normal. See the [official local-server setup guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).

## Code map

| Path | Responsibility |
|---|---|
| `server.py` | Startup |
| `tasktracker/server.py` | MCP endpoints and prompt |
| `tasktracker/storage.py` | SQLite and parameterized queries |
| `tasktracker/security.py` | Input validation and sliding-window rate limiter |
| `tasktracker/config.py` | Project-local configuration |
| `configure.py` | Machine-specific client configuration |
| `demo_checks.py` | End-to-end MCP protocol demo |
| `tests/test_core.py` | Core validation, storage, and throttling checks |

## Design decisions

- Bound SQL parameters keep SQL-looking titles as data rather than executable statements.
- One sliding window is shared by tool execution and prompt generation. Restarting the process resets it; separate processes have separate quotas.
- Settings come from project-local `.env` using `dotenv_values` with interpolation disabled. `.env`, databases, and virtual environments are ignored by Git.
- `requirements-lock.txt` records the tested dependency environment; `requirements.txt` lists top-level versions.

## Scope and limitations

Single-user local prototype: no completion/edit/delete tools, cloud synchronization, accounts, pagination, or encrypted database. Access relies on the OS user and MCP host, not application-level authentication. SQLite built-in case folding is limited for non-ASCII text. Prompt instructions do not establish resistance to prompt injection. The rate limiter is application-operation throttling, not protection against raw protocol floods.

## Related projects

[Agent Workflow Toolkit](https://github.com/54161251/agent-workflow-toolkit) contains separate projects for GitHub issue integration, content-bound draft approval, and offline agent evaluation. This task tracker remains an independent coursework project.

## Attribution

Domain logic and security checks were generated with OpenAI Codex assistance. Adapted SDK/client patterns and dependencies are cited in code and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). References: [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x), [SQLite parameter binding](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders), and [python-dotenv](https://bbc2.github.io/python-dotenv/). No production deployment is claimed.
