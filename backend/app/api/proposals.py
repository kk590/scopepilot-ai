"""Proposal endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Proposal
from app.database.schemas import ProposalPublic
from app.database.session import get_db

router = APIRouter(prefix="/proposals", tags=["proposals"])


@router.get("/{proposal_id}", response_model=ProposalPublic)
async def get_proposal(proposal_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id))
    proposal = result.scalar_one_or_none()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/project/{project_id}", response_model=list[ProposalPublic])
async def list_proposals_for_project(
    project_id: UUID, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Proposal).where(Proposal.project_id == project_id)
    )
    return result.scalars().all()
