"""gRPC client for internal agent communication."""

from __future__ import annotations

import grpc
from app.config import get_settings

settings = get_settings()


async def get_agent_channel():
    # Placeholder – generated stubs would be used here
    return grpc.aio.insecure_channel(f"{settings.mcp_host}:{settings.mcp_port}")
