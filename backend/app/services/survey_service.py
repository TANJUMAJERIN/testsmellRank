"""
Developer Survey Module — survey_service.py

Handles:
  1. Contributor email extraction from git history
  2. Survey email dispatch via Gmail SMTP (fastapi-mail)
  3. DDS calculation (rolling avg after each submission)
  4. Quadrant classification: PS × DDS → Technical Debt Quadrant
"""

import subprocess
import uuid
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict

from app.services.git_metrics import SMELL_ABBREVIATIONS

# ── Canonical 15 smells (abbr → full name) ──────────────────────────
ABBR_TO_NAME: Dict[str, str] = {v: k for k, v in SMELL_ABBREVIATIONS.items()}

# Ordered list of abbreviations used throughout the survey
SMELL_ORDER = [
    "CTL", "AR", "DA", "MNT", "OS",
    "RA",  "EH", "CI", "SA",  "TM",
    "RP",  "GF", "ST", "ET",  "LCTC",
]

# One-sentence description shown in the survey form
SMELL_DESCRIPTIONS: Dict[str, str] = {
    "CTL":  "Test contains if/for/while logic, creating multiple execution paths.",
    "AR":   "Multiple assertions without explanatory messages—hard to know which one fails.",
    "DA":   "The same assertion expression is repeated more than once.",
    "MNT":  "Assertion uses an unexplained numeric literal (magic number).",
    "OS":   "Test body contains extensive setup code that obscures the test's intent.",
    "RA":   "Assertion always passes (e.g. assert True) and provides no verification.",
    "EH":   "Test uses try/except instead of assertRaises().",
    "CI":   "Test class uses __init__ instead of setUp() for initialization.",
    "SA":   "assertTrue(x == y) used instead of the more specific assertEqual(x, y).",
    "TM":   "Test class contains only one isolated test method.",
    "RP":   "Print statements inside tests add noise without aiding assertions.",
    "GF":   "setUp() initialises more objects than any single test method needs.",
    "ST":   "Test calls time.sleep(), making it slow and non-deterministic.",
    "ET":   "Test has no body or contains only 'pass'.",
    "LCTC": "Test methods in a class share no common attributes—unrelated concerns.",
}

# Quadrant → priority label
QUADRANT_PRIORITY: Dict[str, str] = {
    "Prudent & Deliberate":   "HIGH — Refactor Immediately",
    "Reckless & Deliberate":  "MODERATE-HIGH — Refactor Soon",
    "Prudent & Inadvertent":  "MODERATE-LOW — Refactor When Possible",
    "Reckless & Inadvertent": "LOW — Monitor / Defer",
}

# Bot-like email patterns to exclude
_BOT_PATTERNS = [
    "noreply", "no-reply", "github-actions", "dependabot",
    "bot@", "bot+", "actions@", "notifications@",
    "users.noreply",
]


# =====================================================
# PART 1 — CONTRIBUTOR EXTRACTION
# =====================================================

def extract_contributors(repo_path: Path) -> List[Dict[str, str]]:
    """
    Run `git log` to get all unique contributor names + emails.
    Filters out bots and noreply addresses.

    Returns: [{"name": str, "email": str}, ...]
    """
    try:
        result = subprocess.run(
            ["git", "log", "--format=%an|%ae", "--no-merges"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return []

        seen_emails: set = set()
        contributors: List[Dict[str, str]] = []

        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if "|" not in line:
                continue
            name, email = line.split("|", 1)
            name  = name.strip()
            email = email.strip().lower()

            if not email or "@" not in email:
                continue
            if email in seen_emails:
                continue
            if any(p in email for p in _BOT_PATTERNS):
                continue

            seen_emails.add(email)
            contributors.append({"name": name, "email": email})

        return contributors

    except Exception as exc:
        print(f"[SURVEY] extract_contributors error: {exc}")
        return []


# =====================================================
# PART 2 — EMAIL DISPATCH
# =====================================================

async def send_survey_emails(
    contributors: List[Dict],
    survey_id: str,
    project_name: str,
    base_url: str,
) -> Dict[str, int]:
    """
    Send personalised survey links to each contributor via Gmail SMTP.
    Each contributor dict must have 'name', 'email', 'token' fields.

    Returns: {"sent": N, "failed": M}
    """
    try:
        from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
        from app.core.config import settings

        if not settings.mail_username or not settings.mail_password:
            print("[SURVEY] Email credentials not configured — skipping send")
            return {"sent": 0, "failed": len(contributors), "skipped": True}

        conf = ConnectionConfig(
            MAIL_USERNAME=settings.mail_username,
            MAIL_PASSWORD=settings.mail_password,
            MAIL_FROM=settings.mail_from or settings.mail_username,
            MAIL_FROM_NAME=settings.mail_from_name,
            MAIL_PORT=587,
            MAIL_SERVER="smtp.gmail.com",
            MAIL_STARTTLS=True,
            MAIL_SSL_TLS=False,
            USE_CREDENTIALS=True,
            VALIDATE_CERTS=True,
        )

        fm = FastMail(conf)
        sent = 0
        failed = 0

        for contributor in contributors:
            survey_url = f"{base_url}/survey/{contributor['token']}"
            html_body = _build_email_html(
                name=contributor["name"],
                project_name=project_name,
                survey_url=survey_url,
            )
            try:
                msg = MessageSchema(
                    subject=f"[Test Smell Rank] Developer Survey — {project_name}",
                    recipients=[contributor["email"]],
                    body=html_body,
                    subtype=MessageType.html,
                )
                await fm.send_message(msg)
                sent += 1
                print(f"[SURVEY] Email sent to {contributor['email']}")
            except Exception as e:
                print(f"[SURVEY] Failed to send to {contributor['email']}: {e}")
                failed += 1

        return {"sent": sent, "failed": failed}

    except ImportError:
        print("[SURVEY] fastapi-mail not installed — skipping email send")
        return {"sent": 0, "failed": len(contributors), "skipped": True}
    except Exception as exc:
        print(f"[SURVEY] send_survey_emails error: {exc}")
        return {"sent": 0, "failed": len(contributors)}


def _build_email_html(name: str, project_name: str, survey_url: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
      <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                  padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
        <h1 style="color: white; margin: 0; font-size: 24px;">Test Smell Rank</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 8px 0 0;">Developer Perception Survey</p>
      </div>

      <div style="background: #f9f9f9; padding: 30px; border: 1px solid #e0e0e0;
                  border-top: none; border-radius: 0 0 12px 12px;">
        <p style="font-size: 16px;">Hi <strong>{name}</strong>,</p>

        <p>You are a contributor to <strong>{project_name}</strong>. We are
        running a developer perception study on <em>test smells</em> — patterns
        in test code that can reduce maintainability and reliability.</p>

        <p>We would love to hear your opinion on how important each type of test
        smell is to fix. The survey takes <strong>less than 5 minutes</strong>
        and uses a simple 1–5 scale.</p>

        <div style="text-align: center; margin: 30px 0;">
          <a href="{survey_url}"
             style="background: #667eea; color: white; padding: 14px 32px;
                    border-radius: 8px; text-decoration: none; font-size: 16px;
                    font-weight: bold; display: inline-block;">
            Take the Survey →
          </a>
        </div>

        <p style="color: #888; font-size: 13px;">
          Or copy this link into your browser:<br>
          <a href="{survey_url}" style="color: #667eea;">{survey_url}</a>
        </p>

        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 20px 0;">
        <p style="color: #aaa; font-size: 12px; text-align: center;">
          This link is unique to you. You can submit the survey only once.<br>
          Sent by Test Smell Rank — automated research tool.
        </p>
      </div>
    </body>
    </html>
    """


# =====================================================
# PART 3 — DDS CALCULATION (rolling average)
# =====================================================

def calculate_dds(responses: List[Dict]) -> Optional[Dict[str, float]]:
    """
    Compute Developer-Driven Score for each smell from a list of response dicts.
    Each response has a 'ratings' field: {"CTL": 3, "AR": 5, ...}

    Returns None if no responses yet, otherwise:
        {"CTL": 2.67, "AR": 1.80, ...}
    """
    if not responses:
        return None

    sums: Dict[str, float] = defaultdict(float)
    counts: Dict[str, int] = defaultdict(int)

    for resp in responses:
        ratings = resp.get("ratings", {})
        for abbr in SMELL_ORDER:
            val = ratings.get(abbr)
            if val is not None:
                try:
                    sums[abbr] += float(val)
                    counts[abbr] += 1
                except (TypeError, ValueError):
                    pass

    dds: Dict[str, float] = {}
    for abbr in SMELL_ORDER:
        if counts[abbr] > 0:
            dds[abbr] = round(sums[abbr] / counts[abbr], 4)
        else:
            dds[abbr] = None   # no ratings received for this smell yet

    return dds


# =====================================================
# PART 4 — QUADRANT CLASSIFICATION
# =====================================================

def calculate_quadrant_results(
    run_smell_analysis: Dict,
    dds: Dict[str, float],
) -> List[Dict]:
    """
    Combines PS (from run's smell_analysis) with DDS to produce
    mean-centred quadrant classification for each of the 15 smells.

    run_smell_analysis: the 'smell_analysis' dict stored inside a run document
    dds: {"CTL": 2.67, ...}

    Returns a list of 15 dicts matching the final output schema.
    """
    git_metrics = (run_smell_analysis or {}).get("git_metrics") or {}
    raw_metrics = git_metrics.get("metrics") or {}

    # Build PS and instance_count lookups keyed by abbreviation
    ps_by_abbr: Dict[str, float] = {}
    instance_count_by_abbr: Dict[str, int] = {}

    for full_name, abbr in SMELL_ABBREVIATIONS.items():
        entry = raw_metrics.get(full_name) or raw_metrics.get(abbr)
        if entry:
            ps_by_abbr[abbr] = float(entry.get("prioritization_score", 0.0))
            instance_count_by_abbr[abbr] = int(entry.get("instance_count", 0))
        else:
            ps_by_abbr[abbr] = 0.0
            instance_count_by_abbr[abbr] = 0

    # Only include smells that were:
    #   1. Actually detected in the project (instance_count > 0)
    #   2. Have a DDS rating from the survey
    valid_abbrs = [
        a for a in SMELL_ORDER
        if dds.get(a) is not None
        and instance_count_by_abbr.get(a, 0) > 0
    ]

    if not valid_abbrs:
        return []

    # Mean-centre PS
    ps_vals = [ps_by_abbr.get(a, 0.0) for a in valid_abbrs]
    ps_mean = sum(ps_vals) / len(ps_vals)

    # Mean-centre DDS
    dds_vals = [float(dds[a]) for a in valid_abbrs]
    dds_mean = sum(dds_vals) / len(dds_vals)

    results: List[Dict] = []
    for abbr in valid_abbrs:
        ps   = ps_by_abbr.get(abbr, 0.0)
        dds_val = float(dds[abbr])
        norm_ps  = round(ps - ps_mean, 6)
        norm_dds = round(dds_val - dds_mean, 6)

        quadrant = _classify_quadrant(norm_ps, norm_dds)
        priority = QUADRANT_PRIORITY[quadrant]

        results.append({
            "smellName":     ABBR_TO_NAME.get(abbr, abbr),
            "abbreviation":  abbr,
            "PS":            round(ps, 4),
            "DDS":           round(dds_val, 4),
            "normalizedPS":  norm_ps,
            "normalizedDDS": norm_dds,
            "quadrant":      quadrant,
            "priority":      priority,
        })

    # Sort by quadrant importance then by normalizedPS desc
    _order = {
        "Prudent & Deliberate":   0,
        "Reckless & Deliberate":  1,
        "Prudent & Inadvertent":  2,
        "Reckless & Inadvertent": 3,
    }
    results.sort(key=lambda r: (_order[r["quadrant"]], -r["PS"]))

    return results


def _classify_quadrant(norm_ps: float, norm_dds: float) -> str:
    if norm_ps >= 0 and norm_dds >= 0:
        return "Prudent & Deliberate"
    if norm_ps >= 0 and norm_dds < 0:
        return "Reckless & Deliberate"
    if norm_ps < 0 and norm_dds >= 0:
        return "Prudent & Inadvertent"
    return "Reckless & Inadvertent"
