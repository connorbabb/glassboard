from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
from datetime import datetime

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, index=True)
    page = Column(String)
    element = Column(String)
    event_type = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
