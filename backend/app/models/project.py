# app/models/project.py
from pydantic import BaseModel, Field
from typing import Optional, Any, List
from datetime import datetime


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    repo_url: str = Field(..., min_length=1)


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    name: str
    repo_url: str
    created_at: datetime
    run_count: int = 0


class RunSummary(BaseModel):
    total_files: int = 0
    total_smells: int = 0


class RunResponse(BaseModel):
    id: str
    project_id: str
    run_number: int
    created_at: datetime
    status: str  # "pending" | "completed" | "failed"
    summary: Optional[RunSummary] = None
    smell_analysis: Optional[Any] = None
    error: Optional[str] = None


class CompareSmellEntry(BaseModel):
    smell_type: str
    run1_rank: Optional[int] = None
    run2_rank: Optional[int] = None
    rank_change: Optional[int] = None  # negative = improved (rank went down)
    run1_score: Optional[float] = None
    run2_score: Optional[float] = None
    score_change: Optional[float] = None


class CompareResponse(BaseModel):
    project_id: str
    run1: RunResponse
    run2: RunResponse
    comparison: List[CompareSmellEntry]
    summary: dict  # improved, worsened, unchanged counts
