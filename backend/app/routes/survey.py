# app/routes/survey.py
"""
Survey routes — Developer Survey Module

Public endpoints (no auth):
  GET  /api/survey/{token}          — fetch survey form data
  POST /api/survey/{token}/submit   — submit ratings

Protected endpoints (Bearer token required):
  POST /api/projects/{project_id}/runs/{run_id}/survey/start  — launch survey campaign
  GET  /api/projects/{project_id}/runs/{run_id}/survey         — get survey status / results
"""

import uuid
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

from app.core.database import (
    projects_collection,
    runs_collection,
    surveys_collection,
    survey_responses_collection,
)
from app.core.config import settings
from app.core.security import get_current_user
from app.services.survey_service import (
    SMELL_ORDER,
    SMELL_DESCRIPTIONS,
    ABBR_TO_NAME,
    extract_contributors,
    send_survey_emails,
    calculate_dds,
    calculate_quadrant_results,
)

router = APIRouter(tags=["survey"])

UPLOAD_DIR = Path("uploaded_projects")


# ── helpers ────────────────────────────────────────────────────────────────────

async def _get_project_and_run(project_id: str, run_id: str, current_user: dict):
    """Shared guard: verify project belongs to user, fetch run."""
    try:
        proj = await projects_collection.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["_id"],
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Project not found")

    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        run = await runs_collection.find_one({
            "_id": ObjectId(run_id),
            "project_id": ObjectId(project_id),
        })
    except Exception:
        raise HTTPException(status_code=404, detail="Run not found")

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.get("status") != "completed":
        raise HTTPException(status_code=400, detail="Run is not completed yet")

    return proj, run


def _survey_to_dict(doc: dict) -> dict:
    contributors = []
    for c in doc.get("contributors", []):
        contributors.append({
            "name":      c["name"],
            "email":     c["email"],
            "submitted": c.get("submitted", False),
            # Do NOT expose raw token to the project owner view
        })
    return {
        "id":               str(doc["_id"]),
        "project_id":       str(doc["project_id"]),
        "run_id":           str(doc["run_id"]),
        "project_name":     doc.get("project_name", ""),
        "contributors":     contributors,
        "total":            len(contributors),
        "submitted_count":  sum(1 for c in doc.get("contributors", []) if c.get("submitted")),
        "created_at":       doc.get("created_at"),
        "dds":              doc.get("dds"),
        "quadrant_results": doc.get("quadrant_results"),
    }


# ── PROTECTED: start survey ────────────────────────────────────────────────────

@router.post("/api/projects/{project_id}/runs/{run_id}/survey/start")
async def start_survey(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    1. Find the cloned repo path for this project
    2. Extract contributors from git history
    3. Create a survey document (one per run, idempotent re-start)
    4. Send survey emails
    5. Return survey summary
    """
    proj, run = await _get_project_and_run(project_id, run_id, current_user)

    # Resolve repo path (same logic as projects.py trigger run)
    user_dir  = UPLOAD_DIR / f"user_{str(current_user['_id'])}"
    repo_name = proj.get("repo_url", "").rstrip("/").split("/")[-1].replace(".git", "")
    repo_path = user_dir / repo_name

    if not repo_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Cloned repository not found at {repo_path}. Re-run the analysis first.",
        )

    # Extract contributors
    contributors_raw = extract_contributors(repo_path)
    if not contributors_raw:
        raise HTTPException(
            status_code=400,
            detail="No contributor emails found in git history. "
                   "The repository may have no commits or only bot commits.",
        )

    # Check for existing survey — allow re-send but don't duplicate
    existing = await surveys_collection.find_one({
        "project_id": ObjectId(project_id),
        "run_id":     ObjectId(run_id),
    })

    if existing:
        # Re-use existing tokens so links already sent remain valid
        existing_by_email = {c["email"]: c for c in existing.get("contributors", [])}
        contributors_with_tokens = []
        for c in contributors_raw:
            existing_c = existing_by_email.get(c["email"])
            token = existing_c["token"] if existing_c else str(uuid.uuid4())
            contributors_with_tokens.append({
                "name":      c["name"],
                "email":     c["email"],
                "token":     token,
                "submitted": existing_c.get("submitted", False) if existing_c else False,
            })
        await surveys_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"contributors": contributors_with_tokens}},
        )
        survey_id = str(existing["_id"])
    else:
        contributors_with_tokens = [
            {
                "name":      c["name"],
                "email":     c["email"],
                "token":     str(uuid.uuid4()),
                "submitted": False,
            }
            for c in contributors_raw
        ]
        survey_doc = {
            "project_id":    ObjectId(project_id),
            "run_id":        ObjectId(run_id),
            "project_name":  proj["name"],
            "contributors":  contributors_with_tokens,
            "created_at":    datetime.now(timezone.utc),
            "dds":           None,
            "quadrant_results": None,
        }
        result = await surveys_collection.insert_one(survey_doc)
        survey_id = str(result.inserted_id)

    # Send emails (async, best-effort)
    email_result = await send_survey_emails(
        contributors=contributors_with_tokens,
        survey_id=survey_id,
        project_name=proj["name"],
        base_url=settings.frontend_url,
    )

    # Reload and return
    updated = await surveys_collection.find_one({"_id": ObjectId(survey_id)})
    response = _survey_to_dict(updated)
    response["email_dispatch"] = email_result

    return response


# ── PROTECTED: get survey status ───────────────────────────────────────────────

@router.get("/api/projects/{project_id}/runs/{run_id}/survey")
async def get_survey(
    project_id: str,
    run_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Return survey status, contributor submission state, DDS and quadrant results."""
    await _get_project_and_run(project_id, run_id, current_user)

    survey = await surveys_collection.find_one({
        "project_id": ObjectId(project_id),
        "run_id":     ObjectId(run_id),
    })

    if not survey:
        return {"exists": False}

    result = _survey_to_dict(survey)
    result["exists"] = True
    return result


# ── PUBLIC: get survey form ────────────────────────────────────────────────────

@router.get("/api/survey/{token}")
async def get_survey_form(token: str):
    """
    Public endpoint — no auth required.
    Returns project name + the 15 smell prompts for the survey form.
    """
    survey = await surveys_collection.find_one({"contributors.token": token})
    if not survey:
        raise HTTPException(status_code=404, detail="Invalid or expired survey link.")

    # Find this specific contributor
    contributor = next(
        (c for c in survey.get("contributors", []) if c["token"] == token),
        None,
    )
    if not contributor:
        raise HTTPException(status_code=404, detail="Survey token not found.")

    if contributor.get("submitted"):
        return {"already_submitted": True, "project_name": survey.get("project_name", "")}

    smells = [
        {
            "abbreviation": abbr,
            "name":         ABBR_TO_NAME.get(abbr, abbr),
            "description":  SMELL_DESCRIPTIONS.get(abbr, ""),
        }
        for abbr in SMELL_ORDER
    ]

    return {
        "already_submitted": False,
        "survey_id":         str(survey["_id"]),
        "project_name":      survey.get("project_name", ""),
        "contributor_name":  contributor["name"],
        "smells":            smells,
    }


# ── PUBLIC: submit survey response ────────────────────────────────────────────

class SurveySubmission(BaseModel):
    ratings: Dict[str, int]  # {"CTL": 3, "AR": 5, ...}


@router.post("/api/survey/{token}/submit")
async def submit_survey(token: str, submission: SurveySubmission):
    """
    Public endpoint — no auth required.
    Saves ratings, marks contributor as submitted, recalculates DDS + quadrant results.
    """
    survey = await surveys_collection.find_one({"contributors.token": token})
    if not survey:
        raise HTTPException(status_code=404, detail="Invalid or expired survey link.")

    contributor = next(
        (c for c in survey.get("contributors", []) if c["token"] == token),
        None,
    )
    if not contributor:
        raise HTTPException(status_code=404, detail="Survey token not found.")

    if contributor.get("submitted"):
        raise HTTPException(status_code=400, detail="You have already submitted your response.")

    # Validate ratings: 1–5, only known smells accepted
    valid_ratings: Dict[str, int] = {}
    for abbr in SMELL_ORDER:
        val = submission.ratings.get(abbr)
        if val is None:
            raise HTTPException(
                status_code=422,
                detail=f"Missing rating for smell: {abbr}",
            )
        if not isinstance(val, int) or val < 1 or val > 5:
            raise HTTPException(
                status_code=422,
                detail=f"Rating for {abbr} must be an integer 1–5, got: {val}",
            )
        valid_ratings[abbr] = val

    # Save response
    response_doc = {
        "survey_id":          survey["_id"],
        "project_id":         survey["project_id"],
        "run_id":             survey["run_id"],
        "contributor_token":  token,
        "ratings":            valid_ratings,
        "submitted_at":       datetime.now(timezone.utc),
    }
    await survey_responses_collection.insert_one(response_doc)

    # Mark contributor as submitted
    updated_contributors = []
    for c in survey.get("contributors", []):
        entry = dict(c)
        if entry["token"] == token:
            entry["submitted"] = True
        updated_contributors.append(entry)

    # Recalculate DDS from ALL responses for this survey
    all_responses = await survey_responses_collection.find(
        {"survey_id": survey["_id"]}
    ).to_list(length=None)

    new_dds = calculate_dds(all_responses)

    # Recompute quadrant results if we have DDS
    new_quadrant = None
    if new_dds:
        run_doc = await runs_collection.find_one({"_id": survey["run_id"]})
        if run_doc:
            new_quadrant = calculate_quadrant_results(
                run_doc.get("smell_analysis"), new_dds
            )

    # Persist updates
    await surveys_collection.update_one(
        {"_id": survey["_id"]},
        {"$set": {
            "contributors":     updated_contributors,
            "dds":              new_dds,
            "quadrant_results": new_quadrant,
        }},
    )

    return {
        "success":          True,
        "message":          "Thank you! Your response has been recorded.",
        "responses_so_far": len(all_responses),
    }
