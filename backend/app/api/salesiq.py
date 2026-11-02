"""Zoho SalesIQ webhook for lead/discovery intake."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import Customer, Project, ProjectStatus
from app.database.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salesiq", tags=["salesiq"])
settings = get_settings()


@router.post("/webhook")
async def salesiq_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Ingest a new conversation or lead from SalesIQ and create a project."""
    body = await request.json()
    logger.info("SalesIQ webhook: %s", body)

    # Extract visitor / message data (shape depends on SalesIQ payload)
    visitor = body.get("visitor") or body.get("data", {}).get("visitor") or {}
    message = body.get("message") or body.get("data", {}).get("message") or ""

    name = visitor.get("name") or "Unknown"
    email = visitor.get("email")

    customer = Customer(name=name, email=email)
    db.add(customer)
    await db.flush()

    project = Project(
        title=f"SalesIQ lead: {name}",
        original_prompt=message or "New lead from SalesIQ – details to follow",
        customer_id=customer.id,
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return {"status": "created", "project_id": str(project.id)}
