from sqlalchemy import create_engine, text
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
