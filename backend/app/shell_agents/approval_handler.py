"""Approval routing via Zoho Cliq."""

from __future__ import annotations

import logging
from typing import Any, Optional
from uuid import UUID

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ApprovalHandler:
    """Sends proposal for human approval and processes responses."""

    async def request_approval(
        self,
        project_id: UUID,
        proposal_content: str,
        channel_id: Optional[str] = None,
    ) -> dict[str, Any]:
        channel = channel_id or settings.zoho_cliq_channel_id
        if not channel or not settings.zoho_cliq_bot_token:
            logger.warning("Cliq not configured – skipping live approval request")
            return {
                "status": "skipped",
                "reason": "Zoho Cliq credentials not configured",
                "project_id": str(project_id),
            }

        # Placeholder for actual Cliq API call
        logger.info(
            "Would post approval card for project %s to channel %s",
            project_id,
            channel,
        )
        return {
            "status": "sent",
            "project_id": str(project_id),
            "channel": channel,
        }

    async def handle_response(
        self, project_id: UUID, decision: str, comment: str = ""
    ) -> dict[str, Any]:
        decision = decision.lower()
        if decision in ("approve", "approved", "yes"):
            return {"status": "approved", "project_id": str(project_id), "comment": comment}
        if decision in ("reject", "rejected", "no"):
            return {"status": "rejected", "project_id": str(project_id), "comment": comment}
        return {"status": "unknown", "decision": decision}
