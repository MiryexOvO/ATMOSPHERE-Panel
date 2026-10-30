from __future__ import annotations

from aiomcrcon import Client


async def execute_rcon_command(host: str, port: int, password: str, command: str) -> str:
    async with Client(host, port, password) as client:
        response = await client.send_cmd(command)
        return response
