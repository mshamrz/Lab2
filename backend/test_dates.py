from sqlalchemy import select
from app.database import SessionLocal
from app.models import Meeting

db = SessionLocal()
meetings = db.execute(select(Meeting)).scalars().all()
for m in meetings:
    print(m.id, m.title, repr(m.starts_at), repr(m.ends_at))
db.close()
