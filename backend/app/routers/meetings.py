from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Meeting
from app.schemas import MeetingCreate, MeetingOut

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.get("", response_model=list[MeetingOut])
def list_meetings(db: Session = Depends(get_db)):
    stmt = select(Meeting).order_by(Meeting.starts_at.asc())
    return db.execute(stmt).scalars().all()


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/agenda", response_model=MeetingOut)
def save_agenda(meeting_id: int, payload: dict, db: Session = Depends(get_db)):
    meeting = db.get(Meeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting.agenda = payload.get("agenda")
    if "ai_suggestion" in payload:
        meeting.ai_suggestion = payload.get("ai_suggestion")
    db.commit()
    db.refresh(meeting)
    return meeting
