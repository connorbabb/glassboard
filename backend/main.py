from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import events, stats, snippet
from .models import Base
from .database import engine

# Create tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI()

# CORS setup for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or ["http://127.0.0.1:5500"] for stricter testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(snippet.router)

# Optional root route to avoid 404 at "/"
@app.get("/")
def root():
    return {"message": "Glassboard backend running!"}
