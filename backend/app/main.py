
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import admin, auth, documents
from app.core.config import settings
from app.db.session import Base, engine

# Import models so SQLAlchemy knows about their tables
from app.models.user import User
from app.models.document import Document


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Create missing tables in the configured database
    Base.metadata.create_all(bind=engine)

    yield


app = FastAPI(title="Document Manager API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(admin.router, prefix="/api")

@app.get("/")
def home():
    return {
        "message": "Document Manager API is running",
        "docs": "/docs",
        "health": "/api/health"
    }

@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


# --- Serve the built React app (CI copies frontend/dist to backend/dist) -----------------
# Registered last so that every /api route above takes priority.
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "dist"

if (FRONTEND_DIST / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str):
        if full_path.startswith("api/") or full_path == "api":
            raise HTTPException(404, detail="Not found")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if full_path and candidate.is_file() and FRONTEND_DIST.resolve() in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")  # client-side routes (/login, /admin, ...)
