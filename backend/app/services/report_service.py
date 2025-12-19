from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Report, ReportReason, ReportStatus


async def create_report(
    db: AsyncSession,
    reporter_id: int,
    reason: str,
    details: Optional[str] = None,
    reported_user_id: Optional[int] = None,
    reported_project_id: Optional[int] = None
) -> Report:
    report = Report(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        reported_project_id=reported_project_id,
        reason=ReportReason(reason),
        details=details
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def get_report_by_id(db: AsyncSession, report_id: int) -> Optional[Report]:
    result = await db.execute(select(Report).where(Report.id == report_id))
    return result.scalar_one_or_none()


async def get_user_reports(db: AsyncSession, user_id: int) -> List[Report]:
    result = await db.execute(
        select(Report)
        .where(Report.reporter_id == user_id)
        .order_by(Report.created_at.desc())
    )
    return result.scalars().all()
