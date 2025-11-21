from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- RDS Postgres configuration ---
RDS_HOST = "glassboard-rds.c1ymcqk8mlq7.us-west-2.rds.amazonaws.com"
RDS_DB = "glassboard-rds"           # your RDS database name
RDS_USER = "adminuser"              # your master username
RDS_PASSWORD = "BlueSpartan03!"     # the password you set
RDS_PORT = 5432

DATABASE_URL = f"postgresql+psycopg2://{RDS_USER}:{RDS_PASSWORD}@{RDS_HOST}:{RDS_PORT}/glassboard"

# --- Create engine ---
engine = create_engine(DATABASE_URL)

# --- ORM session setup ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
