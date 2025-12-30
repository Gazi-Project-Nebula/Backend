from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Imports from new structure
from src.infrastructure.database.session import engine, SessionLocal
from src.infrastructure.database.models import Base
from src.infrastructure.database.seeder import seed_database  # <--- Import Seeder
from src.presentation.api.v1 import auth_router, election_router, vote_router
from src.core.scheduler import scheduler
# Create database tables
Base.metadata.create_all(bind=engine)

# --- SCHEDULER ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Run Seeder
    with SessionLocal() as db:
        seed_database(db)

    # Startup: Scheduler'ı başlat
    if not scheduler.running:
        scheduler.start()
    yield
    # Shutdown: Scheduler'ı kapat
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