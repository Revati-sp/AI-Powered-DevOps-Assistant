from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis, AnalysisType
from app.models.artifact_tag import ArtifactFavorite
from app.models.background_task import BackgroundTask, TaskStatus
from app.models.conversation import Conversation
from app.models.generated_artifact import GeneratedArtifact
from app.models.organization import OrganizationMember
from app.models.policy import PolicyPack
from app.models.usage import OrganizationQuota, UsageEvent
from app.models.user import User
from app.schemas.dashboard import (
    ActivityItem,
    ArtifactCountSummary,
    CountSummary,
    DashboardActivity,
    DashboardFindings,
    DashboardSummary,
    DashboardTasks,
    FindingCountSummary,
    FindingItem,
    OrganizationSummary,
    TaskCountSummary,
    UsageSummary,
)
from app.services.rbac import OrganizationAuthService, Permission

TIME_RANGES = {
    "24h": timedelta(hours=24),
    "7d": timedelta(days=7),
    "30d": timedelta(days=30),
}
SEVERITIES = ("critical", "high", "medium", "low")


class DashboardService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.org_auth = OrganizationAuthService(session)

    async def _authorize(
        self, user: User, organization_id: UUID | None, *, audit: bool = False
    ) -> None:
        if organization_id is None:
            return
        await self.org_auth.require_membership(organization_id, user.id)
        await self.org_auth.require_permission(
            organization_id,
            user.id,
            Permission.AUDIT_READ if audit else Permission.ARTIFACT_READ,
        )

    @staticmethod
    def _scope(model: Any, user_id: UUID, organization_id: UUID | None) -> list[Any]:
        if organization_id is None:
            return [model.user_id == user_id, model.organization_id.is_(None)]
        return [model.organization_id == organization_id]

    @staticmethod
    def _since(time_range: str) -> datetime:
        return datetime.now(UTC) - TIME_RANGES[time_range]

    async def _task_counts(
        self, user_id: UUID, organization_id: UUID | None
    ) -> TaskCountSummary:
        scope = self._scope(BackgroundTask, user_id, organization_id)
        stmt = select(
            func.count().filter(BackgroundTask.status == TaskStatus.QUEUED),
            func.count().filter(BackgroundTask.status == TaskStatus.RUNNING),
            func.count().filter(BackgroundTask.status == TaskStatus.SUCCEEDED),
            func.count().filter(BackgroundTask.status == TaskStatus.FAILED),
        ).where(*scope)
        row = (await self.session.execute(stmt)).one()
        return TaskCountSummary(
            queued=int(row[0]),
            running=int(row[1]),
            succeeded=int(row[2]),
            failed=int(row[3]),
        )

    async def _finding_data(
        self, user_id: UUID, organization_id: UUID | None, since: datetime
    ) -> tuple[FindingCountSummary, list[FindingItem]]:
        # Review findings are persisted inside Analysis.result_json; JSON shape is intentionally
        # parsed in Python so this stays portable across SQLite and PostgreSQL.
        scope = self._scope(Analysis, user_id, organization_id)
        rows = (
            (
                await self.session.execute(
                    select(Analysis)
                    .where(
                        *scope,
                        Analysis.analysis_type == AnalysisType.REVIEW,
                        Analysis.created_at >= since,
                    )
                    .order_by(Analysis.created_at.desc())
                    .limit(100)
                )
            )
            .scalars()
            .all()
        )
        counts = {severity: 0 for severity in SEVERITIES}
        items: list[FindingItem] = []
        for analysis in rows:
            for finding in (analysis.result_json or {}).get("findings", []):
                severity = finding.get("severity")
                if severity not in counts:
                    continue
                counts[severity] += 1
                if len(items) < 20:
                    items.append(
                        FindingItem(
                            analysis_id=analysis.id,
                            severity=severity,
                            title=str(finding.get("title") or "Security finding"),
                            timestamp=analysis.created_at,
                            organization_id=analysis.organization_id,
                        )
                    )
        return FindingCountSummary(**counts), items

    async def summary(
        self, user: User, *, organization_id: UUID | None, time_range: str
    ) -> DashboardSummary:
        await self._authorize(user, organization_id)
        since = self._since(time_range)
        conversation_scope = self._scope(Conversation, user.id, organization_id)
        artifact_scope = self._scope(GeneratedArtifact, user.id, organization_id)
        usage_scope = self._scope(UsageEvent, user.id, organization_id)
        conversation_row = (
            await self.session.execute(
                select(
                    func.count(),
                    func.count().filter(Conversation.created_at >= since),
                ).where(*conversation_scope)
            )
        ).one()
        artifact_row = (
            await self.session.execute(
                select(
                    func.count(func.distinct(GeneratedArtifact.id)),
                    func.count(func.distinct(GeneratedArtifact.id)).filter(
                        ArtifactFavorite.user_id == user.id,
                        ArtifactFavorite.artifact_id.is_not(None),
                    ),
                    func.count(func.distinct(GeneratedArtifact.id)).filter(
                        GeneratedArtifact.archived_at.is_not(None)
                    ),
                )
                .select_from(GeneratedArtifact)
                .outerjoin(
                    ArtifactFavorite,
                    ArtifactFavorite.artifact_id == GeneratedArtifact.id,
                )
                .where(*artifact_scope, GeneratedArtifact.deleted_at.is_(None))
            )
        ).one()
        usage_count = int(
            (
                await self.session.execute(
                    select(func.count())
                    .select_from(UsageEvent)
                    .where(*usage_scope, UsageEvent.created_at >= since)
                )
            ).scalar_one()
        )
        finding_counts, _ = await self._finding_data(user.id, organization_id, since)
        organization = None
        requests_limit = 0
        if organization_id is not None:
            member_count = int(
                (
                    await self.session.execute(
                        select(func.count()).where(
                            OrganizationMember.organization_id == organization_id
                        )
                    )
                ).scalar_one()
            )
            active_packs = int(
                (
                    await self.session.execute(
                        select(func.count()).where(
                            PolicyPack.organization_id == organization_id,
                            PolicyPack.is_active.is_(True),
                            PolicyPack.deleted_at.is_(None),
                        )
                    )
                ).scalar_one()
            )
            quota = await self.session.scalar(
                select(OrganizationQuota).where(
                    OrganizationQuota.organization_id == organization_id
                )
            )
            requests_limit = quota.monthly_request_limit or 0 if quota else 0
            organization = OrganizationSummary(
                member_count=member_count, active_policy_packs=active_packs
            )
        return DashboardSummary(
            conversations=CountSummary(
                total=int(conversation_row[0]), recent=int(conversation_row[1])
            ),
            artifacts=ArtifactCountSummary(
                total=int(artifact_row[0]),
                favorites=int(artifact_row[1]),
                archived=int(artifact_row[2]),
            ),
            tasks=await self._task_counts(user.id, organization_id),
            findings=finding_counts,
            usage=UsageSummary(
                requests_used=usage_count, requests_limit=requests_limit
            ),
            organization=organization,
        )

    async def findings(
        self, user: User, *, organization_id: UUID | None, time_range: str
    ) -> DashboardFindings:
        await self._authorize(user, organization_id)
        counts, items = await self._finding_data(
            user.id, organization_id, self._since(time_range)
        )
        return DashboardFindings(counts=counts, items=items)

    async def tasks(
        self, user: User, *, organization_id: UUID | None, time_range: str
    ) -> DashboardTasks:
        await self._authorize(user, organization_id)
        scope = self._scope(BackgroundTask, user.id, organization_id)
        rows = (
            (
                await self.session.execute(
                    select(BackgroundTask)
                    .where(*scope, BackgroundTask.created_at >= self._since(time_range))
                    .order_by(BackgroundTask.created_at.desc())
                    .limit(20)
                )
            )
            .scalars()
            .all()
        )
        return DashboardTasks(
            counts=await self._task_counts(user.id, organization_id),
            items=[
                ActivityItem(
                    id=task.id,
                    type="task",
                    title=task.task_type,
                    timestamp=task.created_at,
                    status=task.status.value,
                    organization_id=task.organization_id,
                    route_target=f"/tasks/{task.id}",
                )
                for task in rows
            ],
        )

    async def activity(
        self, user: User, *, organization_id: UUID | None, time_range: str
    ) -> DashboardActivity:
        await self._authorize(user, organization_id, audit=organization_id is not None)
        since = self._since(time_range)
        sources: list[ActivityItem] = []
        conversations = (
            await self.session.execute(
                select(Conversation)
                .where(
                    *self._scope(Conversation, user.id, organization_id),
                    Conversation.updated_at >= since,
                )
                .order_by(Conversation.updated_at.desc())
                .limit(20)
            )
        ).scalars()
        for conversation in conversations:
            sources.append(
                ActivityItem(
                    id=conversation.id,
                    type="conversation",
                    title=conversation.title,
                    timestamp=conversation.updated_at,
                    organization_id=conversation.organization_id,
                    route_target=f"/chat/{conversation.id}",
                )
            )
        artifacts = (
            await self.session.execute(
                select(GeneratedArtifact)
                .where(
                    *self._scope(GeneratedArtifact, user.id, organization_id),
                    GeneratedArtifact.deleted_at.is_(None),
                    GeneratedArtifact.updated_at >= since,
                )
                .order_by(GeneratedArtifact.updated_at.desc())
                .limit(20)
            )
        ).scalars()
        for artifact in artifacts:
            sources.append(
                ActivityItem(
                    id=artifact.id,
                    type="artifact",
                    title=artifact.name,
                    timestamp=artifact.updated_at,
                    organization_id=artifact.organization_id,
                    route_target=f"/artifacts/{artifact.id}",
                )
            )
        analyses = (
            await self.session.execute(
                select(Analysis)
                .where(
                    *self._scope(Analysis, user.id, organization_id),
                    Analysis.created_at >= since,
                )
                .order_by(Analysis.created_at.desc())
                .limit(20)
            )
        ).scalars()
        for analysis in analyses:
            sources.append(
                ActivityItem(
                    id=analysis.id,
                    type="analysis",
                    title=analysis.analysis_type.value,
                    timestamp=analysis.created_at,
                    status=analysis.status.value,
                    organization_id=analysis.organization_id,
                    route_target="/logs",
                )
            )
        task_activity = await self.tasks(
            user, organization_id=organization_id, time_range=time_range
        )
        sources.extend(task_activity.items)
        if organization_id is not None:
            packs = (
                await self.session.execute(
                    select(PolicyPack)
                    .where(
                        PolicyPack.organization_id == organization_id,
                        PolicyPack.updated_at >= since,
                    )
                    .order_by(PolicyPack.updated_at.desc())
                    .limit(20)
                )
            ).scalars()
            for pack in packs:
                sources.append(
                    ActivityItem(
                        id=pack.id,
                        type="policy",
                        title=pack.name,
                        timestamp=pack.updated_at,
                        status="active" if pack.is_active else "inactive",
                        organization_id=organization_id,
                        route_target=(
                            f"/organizations/{organization_id}/policies/{pack.id}"
                        ),
                    )
                )
            members = (
                await self.session.execute(
                    select(OrganizationMember)
                    .where(
                        OrganizationMember.organization_id == organization_id,
                        OrganizationMember.updated_at >= since,
                    )
                    .order_by(OrganizationMember.updated_at.desc())
                    .limit(20)
                )
            ).scalars()
            for member in members:
                sources.append(
                    ActivityItem(
                        id=member.id,
                        type="member",
                        title="Organization member updated",
                        timestamp=member.updated_at,
                        organization_id=organization_id,
                        route_target=f"/organizations/{organization_id}/members",
                    )
                )
        return DashboardActivity(
            items=sorted(sources, key=lambda item: item.timestamp, reverse=True)[:20]
        )
