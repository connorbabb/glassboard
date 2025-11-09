from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    page = Column(String)
    element = Column(String)
    text = Column(String)                # 👈 new field for button/link text
    href = Column(String, nullable=True) # 👈 optional link target (if any)
    event_type = Column(String)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
