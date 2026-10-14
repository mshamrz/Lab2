from app.database import SessionLocal
from app.reports.weekly import build_weekly_report

db = SessionLocal()
csv_bytes = build_weekly_report(db, "2026-W40")
print(csv_bytes.decode("utf-8"))
db.close()
