# Local Task Tracker MCP

A Python personal-productivity server with exactly two tools and one prompt. Claude Desktop launches it as a local child process and exchanges MCP messages over standard input/output. SQLite retains tasks between sessions. No hosted services, API subscription, Node.js, or network listener is required by this server.

## Setup (Windows / VS Code)

Install Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/). Open this folder in VS Code, open its PowerShell terminal, and run:

```powershell
uv venv --python 3.13
.\.venv\Scripts\Activate.ps1
uv pip install -r requirements.txt
python configure.py
python -m unittest discover -s tests -v
python demo_checks.py
```

If activation is restricted, use a VS Code Command Prompt terminal and `.venv\Scripts\activate.bat`. Select `.venv\Scripts\python.exe` using **Python: Select Interpreter**. Demonstrate the activated environment in your editor for the assignment. The supplied local folder already has a uv environment; recreate it if moving the project.

`requirements.txt` contains the tested top-level versions. `requirements-lock.txt` records the full tested environment; install that file instead for the same dependency versions. The project uses the maintained MCP 1.x API explicitly rather than mixing incompatible SDK versions.

## Claude Desktop

1. Run `python configure.py` with the virtual environment active. It creates `.env` if absent and regenerates `claude_desktop_config.json` with absolute paths for this installation.
2. In Claude Desktop, open **Settings → Developer → Edit Config**. On Windows the file is normally `%APPDATA%\Claude\claude_desktop_config.json`.
3. Merge the generated `task-tracker` entry into the existing `mcpServers` object. Preserve other servers. For an empty configuration, copy the generated JSON in full.
4. Fully quit and reopen Claude Desktop. Confirm that `task-tracker` starts and its two tools appear.
5. Ask: “Use task-tracker to add a high-priority task titled Prepare MCP demo.” Then ask: “List my tasks using task-tracker.” Approve tool use when Claude asks.
6. Select the `plan_day` MCP prompt from the client's prompt/attachment menu if available. The automated demo also verifies `prompts/get` directly, independently of client UI support.

Official setup reference: https://modelcontextprotocol.io/docs/develop/connect-local-servers

Running `python server.py` directly appears to wait silently: stdio servers wait for protocol input. Use `python demo_checks.py` to launch and exercise a real server automatically. Do not put debug prints on the server's stdout.

## Interface

| Endpoint | Arguments | Result |
|---|---|---|
| `add_task` tool | `title` (1–200 chars), `priority` (low/medium/high; default medium), optional `due_date` (YYYY-MM-DD) | Persisted record, including ID and creation time |
| `list_tasks` tool | optional literal `query` (up to 200 chars), `limit` (1–100; default 20) | Tasks ordered by priority then due date, returned count and limit |
| `plan_day` prompt | optional `focus` (1–200 chars) | Planning instructions with a snapshot of up to 20 tasks |

Adding and reading are separate tools because one changes state while the other only retrieves it. The prompt asks the host model to plan; the server itself does not call an LLM. No resources are registered because this assignment follows the two-tools-and-a-prompt option.

## Configuration and authentication

Configuration is read using `pathlib.Path` and `dotenv_values` from project-local `.env`, with variable interpolation disabled. Application settings do not come from system environment variables. `.env`, the database and `.venv` are ignored by Git. `.env.example` contains safe defaults only.

There are **no external credentials** in this local-only implementation. Access is controlled by the OS user account and the client that launches the stdio process; this is not application-level authentication. Anyone able to run code as that OS user can access the database. No API key is invented or passed as a tool argument. If a future external service requires a secret, load it from the ignored `.env`, never commit it or put it in Claude's JSON. The rubric separately awards secret-management points: this project demonstrates `.env` handling but cannot demonstrate management of a real external credential without adding an authenticated integration. Confirm the local-only interpretation with the instructor.

`RATE_LIMIT_CALLS=20` and `RATE_LIMIT_SECONDS=60` set one shared sliding window for tool execution and prompt generation. `DATABASE_FILE=data/tasks.sqlite3` must remain within the project. Changes take effect after restarting the server.

## Security demonstrations

Run `python demo_checks.py`. All attacks use a disposable database; your saved tasks are untouched.

**1. Input validation and SQL injection prevention.** Empty, oversized, control-character and invalid date inputs fail. SQL uses bound parameters, not string interpolation. The demo submits `x'); DROP TABLE tasks; --` as a title: it remains harmless text and the table survives. Searching for `' OR 1=1 --` returns no unrelated records. Accepting punctuation as data is intentional; the blocked outcome is SQL execution, not storage of the literal string.

**2. Rate limiting.** The demo starts a server with a three-call window, completes three reads, and attempts a fourth call that writes a task. It receives a rate-limit error and no row is inserted. Prompt generation shares the same limiter. Unit tests verify recovery when the window expires and concurrent enforcement. Invalid arguments rejected by the SDK before dispatch, discovery, and protocol initialization are not counted. This is application-operation throttling, not protection against raw protocol floods. Restarting the process resets the window; multiple processes have separate quotas.

Expected final line: `ALL MCP DEMO CHECKS PASSED (temporary database cleaned up)`.

For a live Claude rate-limit demo, temporarily set `RATE_LIMIT_CALLS=3`, restart Claude, and request four sequential task-tool calls. Restore 20 afterwards. For the SQL demo, ask Claude to save the literal payload, then list tasks and verify the earlier tasks remain. The automated client supplies exact inputs if Claude declines to repeat an attack string.

## Project guide and limitations

`server.py` handles startup; `tasktracker/server.py` registers endpoints; `storage.py` owns SQL; `security.py` owns validation and throttling; `config.py` loads file settings. `demo_checks.py` is a real MCP client, and `tests/test_core.py` tests security boundaries directly.

This is a single-user prototype: it has no completion/edit/delete tools, pagination, encrypted database, cloud synchronization, or user accounts. Unicode text is supported but SQLite's built-in `lower()` only folds ASCII reliably. Titles in prompts remain untrusted content; the prompt instruction reduces confusion but does not prove resistance to LLM prompt injection. Back up the database when the server is stopped. Future work could add task lifecycle tools, pagination and authenticated remote services.

## GitHub and submission

Create a **private** repository and push only this `task-tracker` directory. Do not upload its parent directory: the sibling `canvas-submission` folder is deliberately excluded from the repository deliverable. Run `git status --ignored` to confirm `.env`, `.venv`, and `data` stay ignored. Invite the instructor and TA through repository access settings after confirming their GitHub identities. Never assume an email address identifies a GitHub username. Add the resulting URL to the separate Canvas table.

```powershell
git init -b main
git add .
git commit -m "Implement local task tracker MCP server"
git remote add origin https://github.com/YOUR-ACCOUNT/YOUR-PRIVATE-REPO.git
git push -u origin HEAD:main
```

The Canvas table, architecture diagram, and reflection draft live outside this repository. Edit the reflection to reflect your own experience; rehearse explaining parameter binding, the sliding window, stdio, and tool/prompt differences.

## Citations and AI assistance

Code comments identify adapted registration/client patterns from the [official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x), the [SQLite parameter-binding documentation](https://docs.python.org/3/library/sqlite3.html#sqlite3-placeholders), and [python-dotenv](https://bbc2.github.io/python-dotenv/). Domain logic and security checks were generated for this project with OpenAI Codex assistance. Review and understand all code before submitting. See `THIRD_PARTY_NOTICES.md` for the SDK license notice.
