from __future__ import annotations

import asyncio
from aiomcrcon import Client, RCONConnectionError, IncorrectPasswordError, ClientNotConnectedError


async def execute_rcon_command(host: str, port: int, password: str, command: str) -> str:
    # 统一库异常与超时，避免轮询错误冒到 ASGI。
    try:
        async with asyncio.timeout(8):
            async with Client(host, port, password) as client:
                result=await client.send_cmd(command)
                # 库返回 (文本, 请求编号)，对调用方统一为文本。
                return result[0] if isinstance(result,tuple) else str(result)
    except (RCONConnectionError, IncorrectPasswordError, ClientNotConnectedError, TimeoutError) as exc:
        raise RuntimeError(f'RCON 暂不可用: {type(exc).__name__}') from exc
