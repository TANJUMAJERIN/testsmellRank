# app/routes/survey.py
"""
Developer Survey Routes

Endpoints:
  POST /api/projects/{project_id}/runs/{run_id}/survey/send      - Extract emails & send survey
  GET  /api/projects/{project_id}/runs/{run_id}/survey/status    - Poll response count
  GET  /api/survey/{run_id}                                       - Public: load survey form
  POST /api/survey/submit/{run_id}                               - Public: submit responses
  GET  /api/projects/{project_id}/runs/{run_id}/survey/results   - Fetch DDS + quadrant data
  POST /api/projects/{project_id}/runs/{run_id}/survey/calculate - Force-calculate DDS
"""

from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.database import (
    projects_collection,
    runs_collection,
    survey_responses_collection,
)
from app.core.security import get_current_user
from app.models.project import SurveyStatusResponse, SurveySubmission
from app.services.survey_service import (
    SMELL_SURVEY_ITEMS,
    _compute_and_store_dds,
    check_and_auto_calculate,
    extract_contributor_emails,
    send_survey_emails,
)

router = APIRouter(tags=["survey"])

# Base directory for uploaded/cloned projects (same as projects.py)
UPLOAD_DIR = Path("uploaded_projects")


def _repo_path(user_id: str, repo_url: str) -> Path:
    """Reconstruct the cloned repo directory from user_id and repo URL."""
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    return UPLOAD_DIR / f"user_{user_id}" / repo_name


# ── 1. Send survey emails ────────────────────────────────────────────────────

@router.post("/api/projects/{project_id}/runs/{run_id}/survey/send")
async def send_survey(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Extract contributor emails from the cloned repo's git history,
    then send every contributor the shared survey URL.
    """
    project = await projects_collection.find_one(
        {"_id": ObjectId(project_id), "user_id": current_user["_id"]}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one(
        {"_id": ObjectId(run_id), "project_id": ObjectId(project_id)}
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Run is not yet completed")

    # Locate the cloned repo on disk
    user_id   = str(current_user["_id"])
    repo_path = _repo_path(user_id, project["repo_url"])

    if not repo_path.exists():
        raise HTTPException(
            status_code=422,
            detail=f"Cloned repository not found at expected path: {repo_path}",
        )

    # Extract contributor emails
    emails = extract_contributor_emails(repo_path)
    if not emails:
        raise HTTPException(
            status_code=422,
            detail=(
                "No valid contributor emails found in git history. "
                "Ensure the repository has commit history with author emails."
            ),
        )

    # Build the shared survey URL (run_id is the identifier)
    survey_url = f"{settings.frontend_url}/survey/{run_id}"

    # Send emails
    sent_count = await send_survey_emails(emails, survey_url, project["name"])

    # Persist state to the run document
    await runs_collection.update_one(
        {"_id": ObjectId(run_id)},
        {
            "$set": {
                "survey_status":      "sent",
                "contributor_emails": emails,
                "survey_url":         survey_url,
            }
        },
    )

    return {
        "message":     f"Survey sent to {sent_count} of {len(emails)} contributor(s)",
        "emails_sent": sent_count,
        "emails":      emails,
        "survey_url":  survey_url,
    }


# ── 2. Survey status ─────────────────────────────────────────────────────────

@router.get(
    "/api/projects/{project_id}/runs/{run_id}/survey/status",
    response_model=SurveyStatusResponse,
)
async def get_survey_status(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    project = await projects_collection.find_one(
        {"_id": ObjectId(project_id), "user_id": current_user["_id"]}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one(
        {"_id": ObjectId(run_id), "project_id": ObjectId(project_id)}
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    total_sent      = len(run.get("contributor_emails", []))
    total_submitted = await survey_responses_collection.count_documents(
        {"run_id": run_id}
    )

    return SurveyStatusResponse(
        survey_status   = run.get("survey_status", "not_sent"),
        total_sent      = total_sent,
        total_submitted = total_submitted,
        threshold_pct   = settings.survey_response_threshold * 100,
        dds_ready       = run.get("dds_results") is not None,
        survey_url      = run.get("survey_url"),
    )


# ── 3. Get survey form data (public — no auth) ───────────────────────────────

@router.get("/api/survey/{run_id}")
async def get_survey_form(run_id: str):
    """
    Public endpoint. Returns project name + the 15-smell question list.
    Only accessible after the survey has been sent.
    """
    try:
        run = await runs_collection.find_one({"_id": ObjectId(run_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid survey link")

    if not run:
        raise HTTPException(status_code=404, detail="Survey not found")

    survey_status = run.get("survey_status", "not_sent")
    if survey_status == "not_sent":
        raise HTTPException(status_code=403, detail="Survey has not been opened yet")

    project = await projects_collection.find_one({"_id": run.get("project_id")})
    project_name = project["name"] if project else "Unknown Project"

    return {
        "run_id":       run_id,
        "project_name": project_name,
        "survey_open":  survey_status in ("sent", "completed"),
        "survey_status": survey_status,
        "smell_list":   SMELL_SURVEY_ITEMS,
    }


# ── 4. Submit survey response (public — no auth) ─────────────────────────────

@router.post("/api/survey/submit/{run_id}")
async def submit_survey(run_id: str, submission: SurveySubmission):
    """
    Public endpoint. Any developer with the survey URL can submit once.
    Validates all ratings are 1–5, stores the response, and auto-calculates
    DDS if the response threshold is reached.
    """
    try:
        run = await runs_collection.find_one({"_id": ObjectId(run_id)})
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid survey link")

    if not run:
        raise HTTPException(status_code=404, detail="Survey not found")

    if run.get("survey_status", "not_sent") == "not_sent":
        raise HTTPException(status_code=403, detail="Survey has not been opened yet")

    # Validate all provided ratings
    for abbr, val in submission.responses.items():
        if not isinstance(val, int) or val < 1 or val > 5:
            raise HTTPException(
                status_code=422,
                detail=f"Rating for '{abbr}' must be an integer between 1 and 5. Got: {val}",
            )

    # Persist the response
    await survey_responses_collection.insert_one(
        {
            "run_id":       run_id,
            "responses":    submission.responses,
            "submitted_at": datetime.now(timezone.utc),
        }
    )

    # Auto-calculate DDS if threshold is now met
    dds_calculated = await check_and_auto_calculate(run_id, run)

    return {
        "message":        "Your response has been recorded. Thank you!",
        "dds_calculated": dds_calculated,
    }


# ── 5. Get survey results (authenticated) ────────────────────────────────────

@router.get("/api/projects/{project_id}/runs/{run_id}/survey/results")
async def get_survey_results(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    project = await projects_collection.find_one(
        {"_id": ObjectId(project_id), "user_id": current_user["_id"]}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one(
        {"_id": ObjectId(run_id), "project_id": ObjectId(project_id)}
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    dds_results      = run.get("dds_results")
    quadrant_results = run.get("quadrant_results")

    if not dds_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "DDS results are not yet available. "
                "Survey may still be collecting responses."
            ),
        )

    return {
        "dds_results":      dds_results,
        "quadrant_results": quadrant_results,
        "survey_status":    run.get("survey_status", "not_sent"),
    }


# ── 6. Force-calculate DDS (authenticated) ───────────────────────────────────

@router.post("/api/projects/{project_id}/runs/{run_id}/survey/calculate")
async def force_calculate_dds(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Manually trigger DDS + quadrant calculation regardless of the response
    threshold. Useful when the owner decides enough data has been collected.
    """
    project = await projects_collection.find_one(
        {"_id": ObjectId(project_id), "user_id": current_user["_id"]}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    run = await runs_collection.find_one(
        {"_id": ObjectId(run_id), "project_id": ObjectId(project_id)}
    )
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    count = await survey_responses_collection.count_documents({"run_id": run_id})
    if count == 0:
        raise HTTPException(
            status_code=400,
            detail="No survey responses yet. Cannot calculate DDS.",
        )

    success = await _compute_and_store_dds(run_id, run)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="DDS calculation failed. Check server logs.",
        )

    # Return the freshly calculated data
    updated_run = await runs_collection.find_one({"_id": ObjectId(run_id)})
    return {
        "message":          "DDS calculated successfully",
        "dds_results":      updated_run.get("dds_results"),
        "quadrant_results": updated_run.get("quadrant_results"),
    }
