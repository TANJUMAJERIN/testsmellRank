# app/api/upload.py
from app.services.smell_detection import detect_smells_for_project


from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field
import os
import stat
import shutil
import zipfile
import subprocess
from pathlib import Path
from app.core.security import get_current_user
from app.services.smell_detection import detect_smells_for_project

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("uploaded_projects")
UPLOAD_DIR.mkdir(exist_ok=True)


def _force_remove(func, path, _excinfo):
    """Error handler for shutil.rmtree — removes read-only flag on Windows before retrying."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


class GithubRepoRequest(BaseModel):
    repo_url: str
    cp_weight: float = Field(default=0.5, ge=0.0, le=1.0)


# ===============================
# GitHub Upload
# ===============================
@router.post("/github")
async def upload_github_repo(
    request: GithubRepoRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        repo_url = request.repo_url.strip()

        if not repo_url.startswith(("https://github.com/", "http://github.com/", "git@github.com:")):
            raise HTTPException(status_code=400, detail="Invalid GitHub URL")

        repo_name = repo_url.rstrip('/').split('/')[-1].replace('.git', '')

        user_dir = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
        user_dir.mkdir(exist_ok=True)

        project_dir = user_dir / repo_name

        if project_dir.exists():
            shutil.rmtree(project_dir, onerror=_force_remove)

        result = subprocess.run(
            ["git", "clone", repo_url, str(project_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )

        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr)

        # 🔥 Call smell detection
        smell_result = detect_smells_for_project(project_dir, cp_weight=request.cp_weight)

        return {
            "message": "Repository cloned successfully",
            "project_path": str(project_dir),
            "cp_weight": request.cp_weight,
            "smell_analysis": smell_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# ZIP Upload
# ===============================
@router.post("/zip")
async def upload_zip_file(
    file: UploadFile = File(...),
    cp_weight: float = Form(default=0.5, ge=0.0, le=1.0),
    current_user: dict = Depends(get_current_user)
):
    try:
        if not file.filename.endswith('.zip'):
            raise HTTPException(status_code=400, detail="Only ZIP files allowed")

        user_dir = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
        user_dir.mkdir(exist_ok=True)

        project_name = file.filename.replace('.zip', '')
        project_dir = user_dir / project_name

        if project_dir.exists():
            shutil.rmtree(project_dir, onerror=_force_remove)

        project_dir.mkdir(exist_ok=True)

        zip_path = user_dir / file.filename
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_dir)

        zip_path.unlink()

        # 🔥 Call smell detection
        smell_result = detect_smells_for_project(project_dir, cp_weight=cp_weight)

        return {
            "message": "ZIP uploaded successfully",
            "project_path": str(project_dir),
            "cp_weight": cp_weight,
            "smell_analysis": smell_result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
