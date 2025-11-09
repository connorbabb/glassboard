from backend.database import SessionLocal
from backend.models import Event

db = SessionLocal()
events = db.query(Event).all()
for e in events:
    print(e.site_id, e.page, e.element, e.text, e.timestamp)
db.close()
