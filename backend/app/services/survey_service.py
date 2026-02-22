# app/services/survey_service.py
"""
Developer Survey Service.

Handles:
  - Extracting contributor emails from git history
  - Sending the shared survey link via Gmail SMTP
  - Calculating the Developer-Driven Score (DDS) from collected responses
  - Computing the Technical Debt Quadrant classification (PS + DDS → quadrant)
  - Auto-triggering DDS calculation once the response threshold is met
"""

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Dict, List

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.database import survey_responses_collection, runs_collection


# =====================================================
# SMELL CONSTANTS
# =====================================================

SMELL_SURVEY_ITEMS = [
    {
        "abbr": "CTL",
        "name": "Conditional Test Logic",
        "description": (
            "Test contains if/for/while statements creating multiple paths — "
            "harder to understand, prone to flaky behavior."
        ),
    },
    {
        "abbr": "AR",
        "name": "Assertion Roulette",
        "description": (
            "Multiple undocumented assertions in one test — "
            "hard to know which one failed."
        ),
    },
    {
        "abbr": "DA",
        "name": "Duplicate Assert",
        "description": (
            "Same assertion repeated with same parameters — "
            "redundant and adds maintenance overhead."
        ),
    },
    {
        "abbr": "MNT",
        "name": "Magic Number Test",
        "description": (
            "Assert uses unexplained numeric literals instead of named constants."
        ),
    },
    {
        "abbr": "OS",
        "name": "Obscure In-Line Setup",
        "description": (
            "Setup logic is embedded inside the test method instead of setUp()."
        ),
    },
    {
        "abbr": "RA",
        "name": "Redundant Assertion",
        "description": (
            "Assertions that always pass (e.g., assertTrue(True)) — no real value."
        ),
    },
    {
        "abbr": "EH",
        "name": "Exception Handling",
        "description": (
            "Test uses try/except instead of assertRaises() — misuses the framework."
        ),
    },
    {
        "abbr": "CI",
        "name": "Constructor Initialization",
        "description": (
            "Test class uses __init__ instead of setUp() for initialization."
        ),
    },
    {
        "abbr": "SA",
        "name": "Suboptimal Assert",
        "description": (
            "Weaker assertion used (e.g., assertTrue(a==b) instead of assertEqual)."
        ),
    },
    {
        "abbr": "TM",
        "name": "Test Maverick",
        "description": (
            "Test class doesn't follow project's standard naming or structure."
        ),
    },
    {
        "abbr": "RP",
        "name": "Redundant Print",
        "description": (
            "Test contains print() statements that clutter output with no assertion purpose."
        ),
    },
    {
        "abbr": "GF",
        "name": "General Fixture",
        "description": (
            "setUp() initializes more objects than any single test actually needs."
        ),
    },
    {
        "abbr": "ST",
        "name": "Sleepy Test",
        "description": (
            "Test uses time.sleep() to wait — slow and non-deterministic."
        ),
    },
    {
        "abbr": "ET",
        "name": "Empty Test",
        "description": (
            "Test method has no body (just pass) — always passes, zero value."
        ),
    },
    {
        "abbr": "LCTC",
        "name": "Lack of Cohesion of Test Cases",
        "description": (
            "Test class tests unrelated functionality — violates single responsibility."
        ),
    },
]

ALL_ABBRS: List[str] = [item["abbr"] for item in SMELL_SURVEY_ITEMS]
ABBR_TO_NAME: Dict[str, str] = {item["abbr"]: item["name"] for item in SMELL_SURVEY_ITEMS}

QUADRANT_PRIORITY: Dict[str, str] = {
    "Prudent & Deliberate":   "HIGH — Refactor Immediately",
    "Reckless & Deliberate":  "MODERATE-HIGH — Refactor Soon",
    "Prudent & Inadvertent":  "MODERATE-LOW — Refactor When Possible",
    "Reckless & Inadvertent": "LOW — Monitor / Defer",
}

_PRIORITY_ORDER: Dict[str, int] = {
    "HIGH — Refactor Immediately":           0,
    "MODERATE-HIGH — Refactor Soon":         1,
    "MODERATE-LOW — Refactor When Possible": 2,
    "LOW — Monitor / Defer":                 3,
}


# =====================================================
# PART 1 — CONTRIBUTOR EMAIL EXTRACTION
# =====================================================

def extract_contributor_emails(repo_path: Path) -> List[str]:
    """
    Run `git log --format=%ae` and return unique, valid contributor emails.

    Only filters out clearly automated / bot addresses:
      - anything with 'noreply' in it
      - GitHub Actions / bot service accounts (@github.com)
      - The GitHub no-reply format  (digits+name@users.noreply.github.com)

    Regular institutional / personal emails (e.g. user@iit.du.ac.bd,
    user@gmail.com, user@university.edu) are always kept.
    """
    try:
        result = subprocess.run(
            ["git", "log", "--format=%ae"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(f"[SURVEY] git log failed: {result.stderr}")
            return []

        # Only strip clearly automated senders
        bot_pattern = re.compile(
            r"(noreply"                              # any noreply address
            r"|@github\.com$"                        # GitHub service accounts
            r"|\d+\+.*@users\.noreply\.github\.com"  # GitHub no-reply format
            r")",
            re.IGNORECASE,
        )

        seen: set[str] = set()
        emails: List[str] = []
        for raw in result.stdout.strip().splitlines():
            email = raw.strip().lower()
            if not email:
                continue
            if bot_pattern.search(email):
                print(f"[SURVEY] Filtered bot/noreply: {email}")
                continue
            if email in seen:
                continue
            seen.add(email)
            emails.append(email)
            print(f"[SURVEY] Found contributor email: {email}")

        print(f"[SURVEY] Total unique contributor emails: {len(emails)}")
        return emails

    except Exception as exc:
        print(f"[SURVEY] extract_contributor_emails error: {exc}")
        return []


# =====================================================
# PART 2 — SURVEY EMAIL DISPATCH
# =====================================================

async def send_survey_emails(
    recipients: List[str],
    survey_url: str,
    project_name: str,
) -> int:
    """
    Send the shared survey link to all contributor recipients via Gmail SMTP.
    Returns the count of successfully delivered emails.
    """
    if not settings.gmail_user or not settings.gmail_app_password:
        raise RuntimeError(
            "Gmail credentials are not configured. "
            "Set GMAIL_USER and GMAIL_APP_PASSWORD in your .env file."
        )

    subject = f"[TestSmellRank] Developer Survey — {project_name}"
    body = f"""\
Hello,

You are receiving this email because you have contributed to the project \"{project_name}\".

As part of a test smell prioritization study, we would like to know how you perceive
the urgency of refactoring each of 15 common test smells.

👉 Please take 2-3 minutes to fill in the survey:
{survey_url}

Rating guide (1 = Very low priority to refactor, 5 = Very high priority):
  1 — Not important, can be left as is
  2 — Low priority, address someday
  3 — Moderate priority, worth planning
  4 — High priority, should be fixed soon
  5 — Critical, refactor immediately

Your response helps combine empirical code metrics with developer perception
to produce a more meaningful refactoring priority ranking.

Thank you for your time!
— TestSmellRank System
"""

    sent = 0
    for recipient in recipients:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.gmail_user
            msg["To"] = recipient
            msg.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                msg,
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True,
                username=settings.gmail_user,
                password=settings.gmail_app_password,
            )
            sent += 1
            print(f"[SURVEY] Email sent → {recipient}")

        except Exception as exc:
            print(f"[SURVEY] Failed to send email to {recipient}: {exc}")

    return sent


# =====================================================
# PART 4 — DDS CALCULATION
# =====================================================

async def calculate_dds(run_id: str) -> Dict[str, float]:
    """
    Query all survey_responses for this run_id and compute per-smell mean ratings.

    Returns: {"CTL": 2.67, "AR": 1.80, ..., "LCTC": 3.10}
    Smells with no responses default to 0.0.
    """
    cursor = survey_responses_collection.find({"run_id": run_id})
    responses = await cursor.to_list(length=None)

    if not responses:
        raise ValueError(f"No survey responses found for run_id={run_id}")

    # Accumulate ratings per abbreviation
    ratings: Dict[str, List[float]] = {abbr: [] for abbr in ALL_ABBRS}
    for resp in responses:
        for abbr in ALL_ABBRS:
            val = resp.get("responses", {}).get(abbr)
            if val is not None:
                try:
                    ratings[abbr].append(float(val))
                except (TypeError, ValueError):
                    pass

    dds: Dict[str, float] = {}
    for abbr in ALL_ABBRS:
        vals = ratings[abbr]
        dds[abbr] = round(mean(vals), 4) if vals else 0.0

    return dds


# =====================================================
# PART 5 — QUADRANT CLASSIFICATION
# =====================================================

def calculate_quadrant_results(
    ps_map: Dict[str, float],
    dds_map: Dict[str, float],
) -> List[Dict]:
    """
    Mean-center PS and DDS across the 15 smells, then classify each into one
    of the four Technical Debt quadrants.

    ps_map  : { abbreviation: prioritization_score }  (from git metrics)
    dds_map : { abbreviation: dds_score }              (from survey)

    Returns a list of quadrant entry dicts sorted by priority (HIGH first).
    """
    # Only process abbreviations present in both maps
    abbrs = [a for a in ALL_ABBRS if a in ps_map and a in dds_map]
    if not abbrs:
        return []

    ps_values  = [ps_map[a]  for a in abbrs]
    dds_values = [dds_map[a] for a in abbrs]

    ps_mean  = mean(ps_values)
    dds_mean = mean(dds_values)

    results: List[Dict] = []
    for abbr in abbrs:
        ps  = ps_map[abbr]
        dds = dds_map[abbr]
        norm_ps  = round(ps  - ps_mean,  4)
        norm_dds = round(dds - dds_mean, 4)

        if norm_ps >= 0 and norm_dds >= 0:
            quadrant = "Prudent & Deliberate"
        elif norm_ps >= 0 and norm_dds < 0:
            quadrant = "Reckless & Deliberate"
        elif norm_ps < 0 and norm_dds >= 0:
            quadrant = "Prudent & Inadvertent"
        else:
            quadrant = "Reckless & Inadvertent"

        results.append({
            "smellName":    ABBR_TO_NAME.get(abbr, abbr),
            "abbreviation": abbr,
            "PS":           round(ps,  4),
            "DDS":          round(dds, 4),
            "normalizedPS":  norm_ps,
            "normalizedDDS": norm_dds,
            "quadrant":     quadrant,
            "priority":     QUADRANT_PRIORITY[quadrant],
        })

    results.sort(key=lambda x: _PRIORITY_ORDER.get(x["priority"], 99))
    return results


# =====================================================
# AUTO-CALCULATE HELPERS
# =====================================================

async def check_and_auto_calculate(run_id: str, run_doc: dict) -> bool:
    """
    Called after every new survey submission.
    If submitted_count / total_contributors >= threshold, compute and store DDS.
    Returns True if DDS was calculated in this call.
    """
    contributor_emails = run_doc.get("contributor_emails", [])
    total_sent = len(contributor_emails)

    if total_sent == 0:
        return False

    total_submitted = await survey_responses_collection.count_documents(
        {"run_id": run_id}
    )

    if total_submitted / total_sent < settings.survey_response_threshold:
        return False

    # Threshold met — compute and store
    return await _compute_and_store_dds(run_id, run_doc)


async def _compute_and_store_dds(run_id: str, run_doc: dict) -> bool:
    """
    Compute DDS + quadrant results and persist them directly to the run document.
    Returns True on success.
    """
    try:
        dds_results = await calculate_dds(run_id)

        # Build ps_map: abbreviation -> prioritization_score from the run's git metrics
        smell_analysis = run_doc.get("smell_analysis") or {}
        git_metrics    = smell_analysis.get("git_metrics") or {}
        ranked_smells  = git_metrics.get("ranked_smells", [])

        ps_map: Dict[str, float] = {
            item["abbreviation"]: item["prioritization_score"]
            for item in ranked_smells
            if "abbreviation" in item and "prioritization_score" in item
        }

        quadrant_results = calculate_quadrant_results(ps_map, dds_results)

        await runs_collection.update_one(
            {"_id": run_doc["_id"]},
            {
                "$set": {
                    "dds_results":      dds_results,
                    "quadrant_results": quadrant_results,
                    "survey_status":    "completed",
                }
            },
        )

        print(
            f"[SURVEY] DDS calculated for run {run_id}. "
            f"{len(quadrant_results)} smells classified."
        )
        return True

    except Exception as exc:
        print(f"[SURVEY] _compute_and_store_dds error: {exc}")
        return False
