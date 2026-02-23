import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.auth import router as auth_router
from app.routes.upload import router as upload_router
from app.routes.projects import router as projects_router
from app.routes.survey import router as survey_router

app = FastAPI(title="Test Smell Rank API")

# Build allowed origins: always include localhost for development,
# plus the production Vercel URL from FRONTEND_URL env var.
_origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
_frontend_url = os.getenv("FRONTEND_URL", "").strip()
if _frontend_url:
    _origins.append(_frontend_url)

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
