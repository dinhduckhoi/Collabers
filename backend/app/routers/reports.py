from fastapi import APIRouter, HTTPException, status
from app.routers.deps import DBSession, VerifiedUser
from app.schemas import ReportCreate, ReportResponse
from app.services import create_report, get_project_by_id, get_user_by_id

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(data: ReportCreate, current_user: VerifiedUser, db: DBSession):
    if not data.reported_user_id and not data.reported_project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must specify either reported_user_id or reported_project_id"
        )
    
    if data.reported_user_id:
        user = await get_user_by_id(db, data.reported_user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported user not found"
            )
        if data.reported_user_id == current_user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot report yourself"
            )
    
    if data.reported_project_id:
        project = await get_project_by_id(db, data.reported_project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reported project not found"
            )
    
    report = await create_report(
        db,
        current_user.id,
        data.reason,
        data.details,
        data.reported_user_id,
        data.reported_project_id
    )
    
    return ReportResponse(
        id=report.id,
        reporter_id=report.reporter_id,
        reported_user_id=report.reported_user_id,
        reported_project_id=report.reported_project_id,
        reason=report.reason.value,
        details=report.details,
        status=report.status.value,
        created_at=report.created_at
    )
