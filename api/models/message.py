
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.db import Base


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), ForeignKey("sessions.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    role = Column(String(15))
    content = Column(Text)
    tool_calls = Column(JSONB, nullable=True)
    tool_call_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="messages")
    session = relationship("Session", back_populates="messages") 
