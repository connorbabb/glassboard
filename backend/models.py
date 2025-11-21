from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password_hash = Column(String)

    websites = relationship("Website", back_populates="owner")  # add this

class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(String, unique=True, index=True)  # used in snippet
    name = Column(String, nullable=True)               # optional label/business name
    domain = Column(String, nullable=True)             # optional actual domain
    user_id = Column(Integer, ForeignKey("users.id"))  # owner

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # ORM relationship (not required, just nice to have)
    owner = relationship("User", back_populates="websites")