import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load variables from a .env file
load_dotenv()

# Get the URL from Neon (looks like: postgresql://user:pass@ep-name.us-east-2.aws.neon.tech/neondb)
# IMPORTANT: Append ?sslmode=require if it isn't already there
DATABASE_URL = os.getenv("DATABASE_URL")

# Create the engine
# 'pool_recycle' and 'pool_pre_ping' help manage connections to serverless DBs like Neon
engine = create_engine(
    DATABASE_URL,
    pool_recycle=300,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
