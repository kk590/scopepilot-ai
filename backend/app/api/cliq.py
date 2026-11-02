"""Zoho Cliq webhook and approval endpoints."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cliq", tags=["cliq"])
settings = get_settings()


@router.post("/webhook")
async def cliq_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive approval/rejection actions from Zoho Cliq."""
    body = await request.json()
    logger.info("Cliq webhook received: %s", body)

    # Basic signature check if configured
    if settings.zoho_cliq_webhook_secret:
        # Implement signature verification as needed
        pass

    action = body.get("action") or body.get("type")
    project_id = body.get("project_id") or body.get("params", {}).get("project_id")

    if not project_id:
        raise HTTPException(status_code=400, detail="Missing project_id")

    try:
        pid = UUID(str(project_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid project_id")

    if action in ("approve", "approved"):
        # Update proposal / project status
        logger.info("Project %s approved via Cliq", pid)
        return {"status": "ok", "message": "Approved"}
    elif action in ("reject", "rejected"):
        logger.info("Project %s rejected via Cliq", pid)
        return {"status": "ok", "message": "Rejected"}

    return {"status": "ignored", "action": action}


@router.post("/send-approval/{project_id}")
async def send_approval_request(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Push an approval card to the configured Cliq channel."""
    # Placeholder – real implementation would call Zoho Cliq API
    logger.info("Would send approval request for project %s", project_id)
    return {
        "status": "queued",
        "project_id": str(project_id),
        "channel": settings.zoho_cliq_channel_id,
    }
