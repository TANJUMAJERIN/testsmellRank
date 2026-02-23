# app/routes/projects.py
import os
import stat
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import projects_collection, runs_collection
from app.core.security import get_current_user
from app.models.project import ProjectCreate
from app.services.smell_detection import detect_smells_for_project

router = APIRouter(prefix="/api/projects", tags=["projects"])

UPLOAD_DIR = Path("uploaded_projects")
UPLOAD_DIR.mkdir(exist_ok=True)


def _force_remove(func, path, _excinfo):
    """Error handler for shutil.rmtree — removes read-only flag on Windows before retrying."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def _project_to_dict(doc: dict, run_count: int = 0) -> dict:
    return {
        "id": str(doc["_id"]),
        "user_id": str(doc["user_id"]),
        "name": doc["name"],
        "repo_url": doc["repo_url"],
        "cp_weight": doc.get("cp_weight", 0.5),
        "created_at": doc["created_at"],
        "run_count": run_count,
    }


def _run_to_dict(doc: dict, include_analysis: bool = True) -> dict:
    result = {
        "id": str(doc["_id"]),
        "project_id": str(doc["project_id"]),
        "run_number": doc["run_number"],
        "created_at": doc["created_at"],
        "status": doc["status"],
        "cp_weight": doc.get("cp_weight", 0.5),
        "summary": doc.get("summary"),
        "error": doc.get("error"),
    }
    if include_analysis:
        result["smell_analysis"] = doc.get("smell_analysis")
    else:
        result["smell_analysis"] = None
    return result


# ===============================
# Create a new project
# ===============================
@router.post("/")
async def create_project(
    body: ProjectCreate,
    current_user: dict = Depends(get_current_user),
):
    repo_url = body.repo_url.strip()
    if not repo_url.startswith(("https://github.com/", "http://github.com/", "git@github.com:")):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    doc = {
        "user_id": current_user["_id"],
        "name": body.name.strip(),
        "repo_url": repo_url,
        "cp_weight": body.cp_weight,
        "created_at": datetime.now(timezone.utc),
    }
    result = await projects_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _project_to_dict(doc, run_count=0)


# ===============================
# List user's projects
# ===============================
@router.get("/")
async def list_projects(current_user: dict = Depends(get_current_user)):
    cursor = projects_collection.find({"user_id": current_user["_id"]}).sort("created_at", -1)
    projects = await cursor.to_list(length=100)

    result = []
    for p in projects:
        project_id = p["_id"]
        run_count = await runs_collection.count_documents({"project_id": project_id})
        result.append(_project_to_dict(p, run_count=run_count))
    return result


# ===============================
# Delete a project and all its runs
# ===============================
@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection.find_one({"_id": oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    await runs_collection.delete_many({"project_id": oid})
    await projects_collection.delete_one({"_id": oid})
    return {"message": "Project deleted"}


# ===============================
# Trigger a new analysis run
# ===============================
@router.post("/{project_id}/runs")
async def trigger_run(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection.find_one({"_id": oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine run number
    run_count = await runs_collection.count_documents({"project_id": oid})
    run_number = run_count + 1

    # Insert pending run
    run_doc = {
        "project_id": oid,
        "user_id": current_user["_id"],
        "run_number": run_number,
        "created_at": datetime.now(timezone.utc),
        "status": "pending",
        "cp_weight": project.get("cp_weight", 0.5),
        "summary": None,
        "smell_analysis": None,
        "error": None,
    }
    run_result = await runs_collection.insert_one(run_doc)
    run_id = run_result.inserted_id

    # Clone the repo
    repo_url = project["repo_url"]
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    user_dir = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
    user_dir.mkdir(exist_ok=True)
    project_dir = user_dir / repo_name

    try:
        if project_dir.exists():
            shutil.rmtree(project_dir, onerror=_force_remove)

        clone_result = subprocess.run(
            ["git", "clone", repo_url, str(project_dir)],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if clone_result.returncode != 0:
            raise RuntimeError(clone_result.stderr)

        # Run smell detection
        smell_result = detect_smells_for_project(
            project_dir,
            cp_weight=project.get("cp_weight", 0.5),
        )

        summary = {
            "total_files": smell_result.get("total_files", 0),
            "total_smells": smell_result.get("total_smells", 0),
        }

        # Update run as completed
        await runs_collection.update_one(
            {"_id": run_id},
            {"$set": {"status": "completed", "smell_analysis": smell_result, "summary": summary}},
        )
        run_doc.update({"_id": run_id, "status": "completed", "smell_analysis": smell_result, "summary": summary})

    except Exception as e:
        await runs_collection.update_one(
            {"_id": run_id},
            {"$set": {"status": "failed", "error": str(e)}},
        )
        run_doc.update({"_id": run_id, "status": "failed", "error": str(e)})

    return _run_to_dict(run_doc, include_analysis=True)


# ===============================
# List runs for a project (no smell_analysis payload)
# ===============================
@router.get("/{project_id}/runs")
async def list_runs(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(project_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid project ID")

    project = await projects_collection.find_one({"_id": oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    cursor = runs_collection.find(
        {"project_id": oid},
        {"smell_analysis": 0},  # exclude heavy field
    ).sort("run_number", -1)
    runs = await cursor.to_list(length=200)
    return [_run_to_dict(r, include_analysis=False) for r in runs]


# ===============================
# Delete a single run
# ===============================
@router.delete("/{project_id}/runs/{run_id}")
async def delete_run(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        project_oid = ObjectId(project_id)
        run_oid = ObjectId(run_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    project = await projects_collection.find_one({"_id": project_oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one({"_id": run_oid, "project_id": project_oid})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    await runs_collection.delete_one({"_id": run_oid})
    return {"message": "Run deleted"}


# ===============================
# Get single run with full analysis
# ===============================
@router.get("/{project_id}/runs/{run_id}")
async def get_run(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        project_oid = ObjectId(project_id)
        run_oid = ObjectId(run_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    project = await projects_collection.find_one({"_id": project_oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one({"_id": run_oid, "project_id": project_oid})
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    return _run_to_dict(run, include_analysis=True)


# ===============================
# Compare two runs side by side
# ===============================
@router.get("/{project_id}/compare")
async def compare_runs(
    project_id: str,
    run1: str = Query(...),
    run2: str = Query(...),
    current_user: dict = Depends(get_current_user),
):
    try:
        project_oid = ObjectId(project_id)
        run1_oid = ObjectId(run1)
        run2_oid = ObjectId(run2)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID")

    project = await projects_collection.find_one({"_id": project_oid, "user_id": current_user["_id"]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run1_doc = await runs_collection.find_one({"_id": run1_oid, "project_id": project_oid})
    run2_doc = await runs_collection.find_one({"_id": run2_oid, "project_id": project_oid})

    if not run1_doc or not run2_doc:
        raise HTTPException(status_code=404, detail="One or both runs not found")

    # Always treat the higher run_number as run2 (newer run)
    if run1_doc.get("run_number", 0) > run2_doc.get("run_number", 0):
        run1_doc, run2_doc = run2_doc, run1_doc

    # Build comparison from git_metrics prioritization scores
    def get_ranked_smells(run_doc: dict) -> dict:
        """Returns {smell_type: {rank, score}} sorted by prioritization_score desc"""
        analysis = run_doc.get("smell_analysis") or {}
        git_metrics = analysis.get("git_metrics") or {}
        metrics = git_metrics.get("metrics") or {}

        sorted_smells = sorted(
            metrics.items(),
            key=lambda x: x[1].get("prioritization_score", 0),
            reverse=True,
        )
        return {
            smell: {"rank": idx + 1, "score": data.get("prioritization_score", 0)}
            for idx, (smell, data) in enumerate(sorted_smells)
        }

    r1_ranked = get_ranked_smells(run1_doc)
    r2_ranked = get_ranked_smells(run2_doc)

    all_smells = sorted(set(list(r1_ranked.keys()) + list(r2_ranked.keys())))

    comparison = []
    improved = worsened = unchanged = 0

    for smell in all_smells:
        r1 = r1_ranked.get(smell)
        r2 = r2_ranked.get(smell)

        run1_rank = r1["rank"] if r1 else None
        run2_rank = r2["rank"] if r2 else None
        run1_score = r1["score"] if r1 else None
        run2_score = r2["score"] if r2 else None

        rank_change = None
        if run1_rank is not None and run2_rank is not None:
            rank_change = run2_rank - run1_rank
            if rank_change > 0:
                improved += 1   # rank increased = less urgent = improved
            elif rank_change < 0:
                worsened += 1   # rank decreased = more urgent = worsened
            else:
                unchanged += 1

        score_change = None
        if run1_score is not None and run2_score is not None:
            score_change = round(run2_score - run1_score, 4)

        if run2_rank is None:
            status = "removed"
        elif run1_rank is None:
            status = "new"
        else:
            status = "existing"

        comparison.append({
            "smell_type": smell,
            "run1_rank": run1_rank,
            "run2_rank": run2_rank,
            "rank_change": rank_change,
            "run1_score": run1_score,
            "run2_score": run2_score,
            "score_change": score_change,
            "status": status,
        })

    # Sort by run1 rank (smells that existed in run1 first)
    comparison.sort(key=lambda x: (x["run1_rank"] is None, x["run1_rank"] or 999))

    return {
        "project_id": project_id,
        "run1": _run_to_dict(run1_doc, include_analysis=False),
        "run2": _run_to_dict(run2_doc, include_analysis=False),
        "comparison": comparison,
        "summary": {"improved": improved, "worsened": worsened, "unchanged": unchanged},
    }
