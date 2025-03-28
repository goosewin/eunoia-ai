from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.db import Base


class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(String(50), primary_key=True, index=True)  # UUID string
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
    sequences = relationship("Sequence", back_populates="session") 
