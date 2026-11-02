"""MCP server entrypoint."""

from __future__ import annotations

import logging
from app.mcp_server.tools import register_tools

logger = logging.getLogger(__name__)


def main():
    logger.info("Starting ScopePilot MCP server")
    register_tools()
    # MCP server loop would go here


if __name__ == "__main__":
    main()
