
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from api.db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True, index=True)
    company = Column(String(100))
    company_details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    
    sequences = relationship("Sequence", back_populates="user")
    messages = relationship("Message", back_populates="user")
    sessions = relationship("Session", back_populates="user")
