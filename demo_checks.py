"""End-to-end demo and exploit checks over real MCP stdio, using disposable data."""
import asyncio
import json
import sys
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@asynccontextmanager
async def connect(root: Path):
    # Client lifecycle adapted from official SDK (MIT):
    # https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/examples/snippets/clients/stdio_client.py
    params = StdioServerParameters(command=sys.executable, args=[
        str(Path(__file__).resolve().parent / "server.py"), "--config-dir", str(root)
    ])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


def data(result):
    assert not result.isError, result
    return result.structuredContent or json.loads(result.content[0].text)


async def run():
    with tempfile.TemporaryDirectory(prefix="mcp-task-demo-") as folder:
        root = Path(folder)
        (root / ".env").write_text("RATE_LIMIT_CALLS=30\nRATE_LIMIT_SECONDS=60\n", encoding="utf-8")
        async with connect(root) as session:
            assert {t.name for t in (await session.list_tools()).tools} == {"add_task", "list_tasks"}
            assert [p.name for p in (await session.list_prompts()).prompts] == ["plan_day"]
            print("PASS: MCP startup, handshake, two tools, and prompt discovery")
            task = data(await session.call_tool("add_task", {"title": "Prepare MCP demo", "priority": "high"}))
            assert task["title"] == "Prepare MCP demo"
            payload = "x'); DROP TABLE tasks; --"
            data(await session.call_tool("add_task", {"title": payload}))
            attack = data(await session.call_tool("list_tasks", {"query": "' OR 1=1 --"}))
            assert attack["tasks"] == []
            tasks = data(await session.call_tool("list_tasks", {}))["tasks"]
            assert len(tasks) == 2 and any(t["title"] == payload for t in tasks)
            print("PASS: DROP TABLE payload stored as text; OR 1=1 did not bypass filtering")
            for arguments in [{"title": "a" * 201}, {"title": "bad\u0000text"},
                              {"title": "bad date", "due_date": "2026-02-30"},
                              {"title": "bad priority", "priority": "urgent"}]:
                assert (await session.call_tool("add_task", arguments)).isError
            for arguments in [{"limit": 0}, {"limit": 101}]:
                assert (await session.call_tool("list_tasks", arguments)).isError
            assert len(data(await session.call_tool("list_tasks", {}))["tasks"]) == 2
            print("PASS: invalid inputs rejected without adding records")
            prompt = await session.get_prompt("plan_day", {"focus": "Coursework"})
            assert "Prepare MCP demo" in prompt.messages[0].content.text
            print("PASS: planning prompt includes saved tasks")
        async with connect(root) as session:
            assert len(data(await session.call_tool("list_tasks", {}))["tasks"]) == 2
            print("PASS: data persists across server restarts")
        (root / ".env").write_text("RATE_LIMIT_CALLS=3\nRATE_LIMIT_SECONDS=60\n", encoding="utf-8")
        async with connect(root) as session:
            for _ in range(3):
                data(await session.call_tool("list_tasks", {}))
            blocked = await session.call_tool("add_task", {"title": "Blocked write"})
            assert blocked.isError and "Rate limit exceeded" in blocked.content[0].text
            try:
                await session.get_prompt("plan_day", {})
            except Exception as error:
                assert "Rate limit exceeded" in str(error)
            else:
                raise AssertionError("Prompt bypassed shared limit")
            print("PASS: fourth call blocked; switching tools or using prompt cannot bypass limit")
        async with connect(root) as session:
            assert len(data(await session.call_tool("list_tasks", {}))["tasks"]) == 2
            print("PASS: rate-limited write made no database change")
    print("ALL MCP DEMO CHECKS PASSED (temporary database cleaned up)")


if __name__ == "__main__":
    asyncio.run(asyncio.wait_for(run(), timeout=60))
