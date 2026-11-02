"""Pydantic schemas for API and agent contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str
    email: Optional[str] = None
    company: Optional[str] = None


class CustomerPublic(BaseModel):
    id: UUID
    name: str
    email: Optional[str] = None
    company: Optional[str] = None

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    title: str
    original_prompt: str
    customer: Optional[CustomerCreate] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None


class ProjectPublic(BaseModel):
    id: UUID
    title: str
    original_prompt: str
    status: str
    customer_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClarificationSubmit(BaseModel):
    answers: str


class FeatureItem(BaseModel):
    name: str
    description: str
    priority: str = "medium"


class StructuredRequirements(BaseModel):
    summary: str = ""
    features: list[FeatureItem] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    timeline_weeks: Optional[int] = None
    missing_info: list[str] = Field(default_factory=list)


class ProjectScope(BaseModel):
    summary: str
    features: list[FeatureItem] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)
    timeline_weeks: Optional[int] = None


class VerificationResult(BaseModel):
    verified: bool
    feedback: str = ""
    issues: list[str] = Field(default_factory=list)


class ProjectEstimate(BaseModel):
    total_hours: float
    total_cost: float
    currency: str = "USD"
    breakdown: dict[str, float] = Field(default_factory=dict)
    confidence: str = "medium"


class ProposalPublic(BaseModel):
    id: UUID
    project_id: UUID
    content: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
