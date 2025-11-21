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
    conn = psycopg2.connect(DATABASE_URL)
    print("SUCCESS: Connected!")
    conn.close()
except Exception as e:
    print("FAILED:", e)