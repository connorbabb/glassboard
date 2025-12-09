from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
from datetime import datetime
from uuid import uuid4

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), index=True)    
    page = Column(String)
    element = Column(String)
    text = Column(String)                # 👈 new field for button/link text
    href = Column(String, nullable=True) # 👈 optional link target (if any)
    event_type = Column(String)
    timestamp = Column(DateTime(timezone=True), default=datetime.utcnow)
    referrer = Column(String, nullable=True)
    website = relationship("Website", back_populates="events")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    password_hash = Column(String)

    websites = relationship("Website", back_populates="owner")  # add this

class Website(Base):
    __tablename__ = "websites"

    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid4,           # Automatically generate a UUID upon creation
        unique=True, 
        nullable=False
    )
    name = Column(String, nullable=True)               # optional label/business name
    domain = Column(String, nullable=True)             # optional actual domain
    user_id = Column(Integer, ForeignKey("users.id"))  # owner

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # ORM relationship (not required, just nice to have)
    owner = relationship("User", back_populates="websites")

    events = relationship(
        "Event", 
        back_populates="website", 
        cascade="all, delete-orphan",  # Deletes objects in Python session
        passive_deletes=True          # Allows DB to handle cascades for performance
    )
    labels = relationship(
        "EventLabel", 
        back_populates="website", 
        cascade="all, delete-orphan",  # Deletes objects in Python session
        passive_deletes=True          # Allows DB to handle cascades for performance
    )
    ignored_events = relationship(
        "IgnoredEvent", 
        back_populates="website", 
        cascade="all, delete-orphan",  # Deletes objects in Python session
        passive_deletes=True          # Allows DB to handle cascades for performance
    )

class EventLabel(Base):
    __tablename__ = "event_labels"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), index=True, nullable=True)
    website = relationship("Website", back_populates="labels")
    element = Column(String, nullable=False)
    original_text = Column(String, nullable=False)
    custom_text = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint("site_id", "element", "original_text", name="uix_event_label"),
    )

class IgnoredEvent(Base):
    __tablename__ = "ignored_events"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), index=True, nullable=True)
    website = relationship("Website", back_populates="ignored_events") 
    element = Column(String, nullable=False)
    original_text = Column(String, nullable=False)
    
    # Ensures no duplicate mute rules exist for the same element/text pair on the same site
    __table_args__ = (
        UniqueConstraint("site_id", "element", "original_text", name="uix_ignored_event"),
    )