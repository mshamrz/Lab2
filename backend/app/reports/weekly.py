import csv
import io
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Meeting


def _iso_week_bounds(week: str) -> tuple[datetime, datetime]:
    """'2026-W40' -> (Monday 00:00 UTC, next Monday 00:00 UTC)."""
    year, w = week.split("-W")
    monday = date.fromisocalendar(int(year), int(w), 1)
    start = datetime(monday.year, monday.month, monday.day)
    end = start + timedelta(days=7)
    return start, end


def _prev_week(week: str) -> str:
    year, w = week.split("-W")
    monday = date.fromisocalendar(int(year), int(w), 1)
    prev_monday = monday - timedelta(days=7)
    iso_year, iso_week, _ = prev_monday.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


def _week_totals(db: Session, week: str) -> tuple[int, float]:
    start, end = _iso_week_bounds(week)
    stmt = select(Meeting).where(Meeting.starts_at >= start, Meeting.starts_at < end)
    meetings = db.execute(stmt).scalars().all()
    count = len(meetings)
    hours = sum((m.ends_at - m.starts_at).total_seconds() for m in meetings) / 3600
    return count, hours


def build_weekly_report(db: Session, week: str) -> bytes:
    """Query the meetings of one ISO week (e.g. "2026-W40") and return the CSV."""
    start, end = _iso_week_bounds(week)
    prev_week = _prev_week(week)

    count, hours = _week_totals(db, week)
    prev_count, prev_hours = _week_totals(db, prev_week)

    stmt = (
        select(Meeting)
        .where(Meeting.starts_at >= start, Meeting.starts_at < end)
        .order_by(Meeting.starts_at.asc())
    )
    meetings = db.execute(stmt).scalars().all()
    longest = sorted(
        meetings,
        key=lambda m: (m.ends_at - m.starts_at).total_seconds(),
        reverse=True,
    )[:5]

    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Spry weekly report", week])
    writer.writerow([])
    writer.writerow(["Metric", week, prev_week, "Change"])
    writer.writerow(["Meetings", count, prev_count, count - prev_count])
    writer.writerow(
        ["Hours", round(hours, 2), round(prev_hours, 2), round(hours - prev_hours, 2)]
    )
    writer.writerow([])
    writer.writerow(["Top 5 longest meetings"])
    writer.writerow(["Title", "Starts at", "Duration (h)", "Attendees"])
    for m in longest:
        duration_h = round((m.ends_at - m.starts_at).total_seconds() / 3600, 2)
        writer.writerow([m.title, m.starts_at.isoformat(), duration_h, m.attendee_count])

    return buf.getvalue().encode("utf-8")
