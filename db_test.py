from sqlalchemy import create_engine, text
import psycopg2
from backend.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version();"))
        print("✅ Connected successfully!")
        for row in result:
            print(row)
except Exception as e:
    print("❌ Connection failed:", e)

try:
    conn = psycopg2.connect(
        dbname="glassboard",
        user="adminuser",
        password="BlueSpartan03!",
        host="glassboard-rds.c1ymcqk8mlq7.us-west-2.rds.amazonaws.com",
        port="5432"
    )
    print("SUCCESS: Connected!")
    conn.close()
except Exception as e:
    print("FAILED:", e)