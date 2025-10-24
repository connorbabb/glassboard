# Glassboard

Notes:
- Eventually I'll need to replace allow_origins=["*"] with allow_origins=["https://myglassboard.com"] or something similar. The asterisk allows all sites which is a security hole and bad for production.

10/1/25 - Created Project

10/22/25 - Instructions to Run
- [In parent directory]
- uvicorn backend.main.app --reload
- Open link to confirm it works.
- Open tracking-snippet/index.html
- Open frontend/index.html
- Click buttons and watch it show up on the tracker.
- Uses fastAPI with Python for backend. PostreSQL in AWS RDS for database. React for Frontend.
- React + FastAPI + PostgreSQL.
