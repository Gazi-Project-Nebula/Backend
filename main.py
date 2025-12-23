from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

# Imports from new structure
from src.infrastructure.database.session import engine, SessionLocal
from src.infrastructure.database.models import Base
from src.infrastructure.repositories.election_repository import SqlAlchemyElectionRepository
from src.presentation.api.v1 import auth_router, election_router, vote_router

# Create database tables
Base.metadata.create_all(bind=engine)

# --- SCHEDULER ---
scheduler = BackgroundScheduler()

def trigger_start_election(election_id: int):
    db = SessionLocal()
    try:
        repo = SqlAlchemyElectionRepository(db)
        repo.start_election(election_id)
    finally:
        db.close()

def trigger_end_election(election_id: int):
    db = SessionLocal()
    try:
        repo = SqlAlchemyElectionRepository(db)
        repo.end_election(election_id)
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not scheduler.running:
        scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://fluffy-waffle-omega.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router)
app.include_router(election_router.router)
app.include_router(vote_router.router)

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to the Secure E-Voting API (Refactored)"}
