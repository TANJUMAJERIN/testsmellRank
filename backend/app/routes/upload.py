# app/routes/upload.py
"""
Quick-analysis upload endpoints.

Both /github and /zip now:
  1. Run smell detection as before.
  2. Persist a Project + Run document to MongoDB.
  3. Automatically extract contributor emails (from git log) and send the
     Developer Survey to each one.
  4. Return project_id + run_id so the frontend can navigate to the full
     project-run Results page (which renders the survey control strip).
"""

from datetime import datetime, timezone
import os
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import projects_collection, runs_collection
from app.core.security import get_current_user
from app.services.smell_detection import detect_smells_for_project
from app.services.survey_service import (
    extract_contributor_emails,
    send_survey_emails,
)

router = APIRouter(prefix="/api/upload", tags=["upload"])

UPLOAD_DIR = Path("uploaded_projects")
UPLOAD_DIR.mkdir(exist_ok=True)


def _force_remove(func, path, _excinfo):
    """Error handler for shutil.rmtree — removes read-only flag on Windows before retrying."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


async def _persist_and_survey(
    current_user: dict,
    project_name: str,
    repo_url: str,
    project_dir: Path,
    smell_result: dict,
) -> dict:
    """
    Create (or reuse) a Project + Run in MongoDB, auto-extract contributor
    emails, and dispatch the Developer Survey.

    Returns a dict with project_id / run_id and survey metadata.
    """
    user_id = current_user["_id"]

    # ── Reuse existing project for the same repo_url, or create a new one ──
    existing_project = await projects_collection.find_one(
        {"user_id": user_id, "repo_url": repo_url}
    )
    if existing_project:
        project_id = existing_project["_id"]
        project_display_name = existing_project["name"]
    else:
        project_doc = {
            "user_id": user_id,
            "name": project_name,
            "repo_url": repo_url,
            "created_at": datetime.now(timezone.utc),
        }
        ins = await projects_collection.insert_one(project_doc)
        project_id = ins.inserted_id
        project_display_name = project_name

    # ── Run number ──────────────────────────────────────────────────────────
    run_count = await runs_collection.count_documents({"project_id": project_id})
    run_number = run_count + 1

    summary = {
        "total_files": smell_result.get("total_files", 0),
        "total_smells": smell_result.get("total_smells", 0),
    }

    run_doc = {
        "project_id": project_id,
        "user_id": user_id,
        "run_number": run_number,
        "created_at": datetime.now(timezone.utc),
        "status": "completed",
        "summary": summary,
        "smell_analysis": smell_result,
        "error": None,
    }
    run_ins = await runs_collection.insert_one(run_doc)
    run_id = run_ins.inserted_id

    # ── Auto-send Developer Survey (non-fatal) ───────────────────────────────
    survey_emails_sent = 0
    contributor_emails: list[str] = []
    survey_url = ""

    try:
        contributor_emails = extract_contributor_emails(project_dir)
        if contributor_emails:
            survey_url = f"{settings.frontend_url}/survey/{str(run_id)}"
            survey_emails_sent = await send_survey_emails(
                contributor_emails, survey_url, project_display_name
            )
            await runs_collection.update_one(
                {"_id": run_id},
                {
                    "$set": {
                        "survey_status": "sent",
                        "contributor_emails": contributor_emails,
                        "survey_url": survey_url,
                    }
                },
            )
            print(
                f"[SURVEY] Auto-sent to {survey_emails_sent}/{len(contributor_emails)} "
                f"contributor(s) for run {run_id}"
            )
        else:
            print(f"[SURVEY] No contributor emails found in {project_dir.name}")
    except Exception as survey_err:
        print(f"[SURVEY] Auto-send failed (non-fatal): {survey_err}")

    return {
        "project_id": str(project_id),
        "run_id": str(run_id),
        "survey_emails_sent": survey_emails_sent,
        "contributor_count": len(contributor_emails),
        "survey_url": survey_url,
    }


class GithubRepoRequest(BaseModel):
    repo_url: str


# ===============================
# GitHub Upload
# ===============================
@router.post("/github")
async def upload_github_repo(
    request: GithubRepoRequest,
    current_user: dict = Depends(get_current_user),
):
    repo_url = request.repo_url.strip()

    if not repo_url.startswith(
        ("https://github.com/", "http://github.com/", "git@github.com:")
    ):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")

    user_dir = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
    user_dir.mkdir(exist_ok=True)
    project_dir = user_dir / repo_name

    if project_dir.exists():
        shutil.rmtree(project_dir, onerror=_force_remove)

    clone_result = subprocess.run(
        ["git", "clone", repo_url, str(project_dir)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if clone_result.returncode != 0:
        raise HTTPException(status_code=400, detail=clone_result.stderr)

    try:
        smell_result = detect_smells_for_project(project_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    meta = await _persist_and_survey(
        current_user=current_user,
        project_name=repo_name,
        repo_url=repo_url,
        project_dir=project_dir,
        smell_result=smell_result,
    )

    return {
        "message": "Repository cloned and analysed successfully",
        **meta,
        "project_path": str(project_dir),
        "smell_analysis": smell_result,
    }


# ===============================
# ZIP Upload
# ===============================
@router.post("/zip")
async def upload_zip_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files allowed")

    user_dir = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
    user_dir.mkdir(exist_ok=True)

    project_name = file.filename.replace(".zip", "")
    project_dir = user_dir / project_name

    if project_dir.exists():
        shutil.rmtree(project_dir, onerror=_force_remove)
    project_dir.mkdir(exist_ok=True)

    zip_path = user_dir / file.filename
    try:
        with open(zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(project_dir)
    finally:
        if zip_path.exists():
            zip_path.unlink()

    try:
        smell_result = detect_smells_for_project(project_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Use a placeholder repo_url for ZIP uploads (no real remote URL)
    zip_repo_url = f"zip://{project_name}"

    meta = await _persist_and_survey(
        current_user=current_user,
        project_name=project_name,
        repo_url=zip_repo_url,
        project_dir=project_dir,
        smell_result=smell_result,
    )

    return {
        "message": "ZIP uploaded and analysed successfully",
        **meta,
        "project_path": str(project_dir),
        "smell_analysis": smell_result,
    }

