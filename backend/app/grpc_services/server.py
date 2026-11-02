"""gRPC server for agent services."""

from __future__ import annotations

import logging
from concurrent import futures

import grpc

logger = logging.getLogger(__name__)


def serve(port: int = 50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    # Add generated servicers here
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logger.info("gRPC server started on port %s", port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
