
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
    steps = relationship("SequenceStep", back_populates="sequence", cascade="all, delete-orphan")

class SequenceStep(Base):
    __tablename__ = "sequence_steps"
    
    id = Column(Integer, primary_key=True, index=True)
    sequence_id = Column(Integer, ForeignKey("sequences.id"), index=True)
    message = Column(Text)
    channel = Column(String(50))
    subject = Column(String(100), nullable=True)
    position = Column(Integer)
    day = Column(Integer, default=0)
    timing = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    sequence = relationship("Sequence", back_populates="steps") 
