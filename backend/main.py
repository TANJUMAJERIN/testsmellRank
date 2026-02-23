import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.upload import router as upload_router
from app.routes.projects import router as projects_router
from app.routes.survey import router as survey_router

app = FastAPI(title="Test Smell Rank API")

# Build allowed origins list.
# ALLOWED_ORIGINS  — comma-separated list (takes priority, most flexible)
# FRONTEND_URL     — single production URL (legacy / fallback)
_default_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]

_extra = os.getenv("ALLOWED_ORIGINS", "")
if _extra.strip():
    _extra_list = [o.strip().rstrip("/") for o in _extra.split(",") if o.strip()]
else:
    # fall back to single FRONTEND_URL
    _frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    _extra_list = [_frontend_url] if _frontend_url else []

_origins = _default_origins + _extra_list

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(upload_router)
app.include_router(projects_router)
app.include_router(survey_router)

@app.get("/")
async def root():
    return {"message": "Test Smell Rank API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
