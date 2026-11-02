"""
Complete workflow orchestrator.
All state transitions and the verifier correction loop live here.
Only the two LLM agents (imported from agents.py) make model calls.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import ScopeIntelligenceAgent, VerifierLoopAgent
from app.database.models import (
    AgentExecutionLog,
    Project,
    ProjectStatus,
    Proposal,
    ScopeVersion,
    VerificationRun,
)
from app.database.schemas import (
    ProjectEstimate,
    ProjectScope,
    StructuredRequirements,
    VerificationResult,
)
from app.shell_agents.estimator import EstimationAgent
from app.shell_agents.parser import ParserAgent
from app.shell_agents.proposal_generator import ProposalGeneratorAgent
from app.validation.rules import detect_repeated_failure, validate_scope_deterministically

logger = logging.getLogger(__name__)


class WorkflowBlockedError(Exception):
    def __init__(self, reason: str, questions: Optional[list[str]] = None):
        self.reason = reason
        self.questions = questions or []
        super().__init__(reason)


class AgentFlow:
    """Orchestrates the full ScopePilot pipeline for a single project."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.parser = ParserAgent()
        self.scope_agent = ScopeIntelligenceAgent()
        self.verifier = VerifierLoopAgent()
        self.estimator = EstimationAgent()
        self.proposal_gen = ProposalGeneratorAgent()

    async def run(self, project_id: UUID) -> dict[str, Any]:
        project = await self._get_project(project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        requirements = await self._parse(project)
        if requirements.missing_info:
            await self._update_status(project, ProjectStatus.NEEDS_CUSTOMER_INPUT)
            raise WorkflowBlockedError(
                "Missing information from customer",
                questions=requirements.missing_info,
            )

        scope = await self._generate_scope(project, requirements)
        verified_scope, _ = await self._verify_loop(project, scope)
        estimate = await self._estimate(project, verified_scope)
        proposal = await self._generate_proposal(project, verified_scope, estimate)

        await self._update_status(project, ProjectStatus.PROPOSAL_READY)
        return {
            "project_id": str(project_id),
            "status": project.status.value,
            "scope": verified_scope.model_dump() if hasattr(verified_scope, "model_dump") else verified_scope,
            "estimate": estimate.model_dump() if hasattr(estimate, "model_dump") else estimate,
            "proposal_id": str(proposal.id) if proposal else None,
        }

    async def _get_project(self, project_id: UUID) -> Optional[Project]:
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def _update_status(self, project: Project, status: ProjectStatus):
        project.status = status
        project.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def _parse(self, project: Project) -> StructuredRequirements:
        start = time.time()
        try:
            requirements = await self.parser.parse(project.original_prompt)
            await self._log(project.id, "parser", int((time.time() - start) * 1000), "success")
            return requirements
        except Exception as e:
            await self._log(project.id, "parser", int((time.time() - start) * 1000), "error", str(e))
            raise

    async def _generate_scope(
        self, project: Project, requirements: StructuredRequirements
    ) -> ProjectScope:
        start = time.time()
        try:
            scope = await self.scope_agent.generate(requirements)
            version = ScopeVersion(
                project_id=project.id,
                version=1,
                scope_json=scope.model_dump() if hasattr(scope, "model_dump") else scope,
                created_by="scope_intelligence",
            )
            self.db.add(version)
            await self.db.commit()
            await self._log(project.id, "scope_intelligence", int((time.time() - start) * 1000), "success")
            return scope
        except Exception as e:
            await self._log(project.id, "scope_intelligence", int((time.time() - start) * 1000), "error", str(e))
            raise

    async def _verify_loop(
        self, project: Project, scope: ProjectScope, max_iterations: int = 5
    ) -> tuple[ProjectScope, VerificationResult]:
        current = scope
        history: list[dict] = []
        for i in range(max_iterations):
            start = time.time()
            result = await self.verifier.verify(current)
            history.append(result.model_dump() if hasattr(result, "model_dump") else result)

            run = VerificationRun(
                project_id=project.id,
                iteration=i + 1,
                verified=result.verified,
                feedback=result.feedback,
                result_json=result.model_dump() if hasattr(result, "model_dump") else result,
            )
            self.db.add(run)
            await self.db.commit()
            await self._log(
                project.id,
                "verifier",
                int((time.time() - start) * 1000),
                "success" if result.verified else "needs_correction",
            )

            if result.verified:
                return current, result

            if detect_repeated_failure(history):
                raise WorkflowBlockedError("Verifier failed repeatedly; human intervention required")

            det = validate_scope_deterministically(
                current.model_dump() if hasattr(current, "model_dump") else current
            )
            if not det.get("ok", True):
                logger.warning("Deterministic validation issues: %s", det)

            current = await self.scope_agent.correct(current, result.feedback)

        raise WorkflowBlockedError("Max verification iterations exceeded")

    async def _estimate(self, project: Project, scope: ProjectScope) -> ProjectEstimate:
        start = time.time()
        estimate = await self.estimator.estimate(scope)
        await self._log(project.id, "estimator", int((time.time() - start) * 1000), "success")
        return estimate

    async def _generate_proposal(
        self, project: Project, scope: ProjectScope, estimate: ProjectEstimate
    ) -> Proposal:
        start = time.time()
        content = await self.proposal_gen.generate(project, scope, estimate)
        proposal = Proposal(
            project_id=project.id,
            content=content,
            status="draft",
        )
        self.db.add(proposal)
        await self.db.commit()
        await self.db.refresh(proposal)
        await self._log(project.id, "proposal_generator", int((time.time() - start) * 1000), "success")
        return proposal

    async def _log(
        self,
        project_id: UUID,
        agent: str,
        duration_ms: int,
        status: str,
        error_message: Optional[str] = None,
    ):
        log = AgentExecutionLog(
            project_id=project_id,
            agent_name=agent,
            duration_ms=duration_ms,
            status=status,
            error_message=error_message,
        )
        self.db.add(log)
        await self.db.commit()
