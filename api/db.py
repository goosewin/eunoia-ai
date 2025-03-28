import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost/eunoia")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Import here to avoid circular imports
    from api.models import User
    
    # Create a default user if none exists
    db = SessionLocal()
    try:
        # Check if default user exists
        default_user = db.query(User).filter(User.id == 1).first()
        
        if not default_user:
            logger.info("Creating default user")
            default_user = User(
                id=1,
                name="Default User",
                email="default@example.com",
                company="Eunoia AI",
                company_details="AI-powered recruiting solution"
            )
            db.add(default_user)
            db.commit()
            logger.info("Default user created successfully")
    except Exception as e:
        logger.error(f"Error creating default user: {str(e)}")
        db.rollback()
    finally:
        db.close() 
