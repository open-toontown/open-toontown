"""
Standalone test client for the TTBTN MCP server.

Connects over stdio (exactly like Claude Code / Cursor would) and calls a
selection of tools, printing the results. Used to validate the server.

Usage:
    mcp/.venv/Scripts/python mcp/test_client.py [tool [tool ...]]
    (no args -> runs the default validation set)
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))


async def call(session, name, args=None):
    print('\n### tool: %s%s' % (name, (' %s' % (args or {}))))
    try:
        result = await session.call_tool(name, args or {})
        for content in result.content:
            if getattr(content, 'type', '') == 'text':
                print(content.text)
            else:
                print(content)
    except Exception as e:
        print('ERROR: %s' % e)


async def main():
    tools = sys.argv[1:] or ['get_project_info', 'game_status', 'scan_crash_logs',
                             'latest_logs']
    params = StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(HERE, 'mcp_server.py')],
        cwd=HERE,
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            available = await session.list_tools()
            names = [t.name for t in available.tools]
            print('available tools: %s' % ', '.join(names))
            for t in tools:
                if t not in names:
                    print('\n### tool not found: %s' % t)
                    continue
                if t == 'get_project_info':
                    await call(session, t)
                elif t == 'game_status':
                    await call(session, t)
                elif t == 'scan_crash_logs':
                    await call(session, t, {'since_hours': 24, 'max_results': 10})
                elif t == 'latest_logs':
                    await call(session, t, {'n': 25, 'grep': 'error'})
                elif t == 'start_servers':
                    await call(session, t, {'timeout_s': 60})
                elif t == 'stop_servers':
                    await call(session, t)
                elif t == 'run_smoke_test':
                    await call(session, t, {'timeout_s': 300, 'avatar_choice': 0,
                                             'login_token': 'dev', 'stop_client': True})
                else:
                    await call(session, t)


if __name__ == '__main__':
    asyncio.run(main())
