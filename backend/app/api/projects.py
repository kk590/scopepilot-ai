"""Project and workflow endpoints."""

from __future__ import annotations

import uuid
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent_flow import AgentFlow
from app.database.models import Customer, Project, ProjectStatus, ScopeVersion
from app.database.schemas import (
    ClarificationSubmit,
    ProjectCreate,
    ProjectPublic,
    ProjectUpdate,
)
from app.database.session import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
):
    customer = None
    if payload.customer:
        customer = Customer(
            name=payload.customer.name,
            email=payload.customer.email,
            company=payload.customer.company,
        )
        db.add(customer)
        await db.flush()

    project = Project(
        title=payload.title,
        original_prompt=payload.original_prompt,
        customer_id=customer.id if customer else None,
        status=ProjectStatus.DRAFT,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(project_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/run")
async def run_workflow(
    project_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    flow = AgentFlow(db)
    try:
        outcome = await flow.run(project_id)
        return outcome
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{project_id}/clarify")
async def submit_clarification(
    project_id: UUID,
    payload: ClarificationSubmit,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Append clarification to prompt and re-run or update status
    project.original_prompt += f"\n\nClarification: {payload.answers}"
    project.status = ProjectStatus.DRAFT
    await db.commit()
    return {"status": "updated", "project_id": str(project_id)}
