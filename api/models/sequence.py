from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.db import Base


class Sequence(Base):
    __tablename__ = "sequences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String(50), ForeignKey("sessions.id"), index=True)
    title = Column(String(100))
    target_role = Column(String(100))
    target_industry = Column(String(100))
    sequence_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="sequences")
    session = relationship("Session", back_populates="sequences") 
