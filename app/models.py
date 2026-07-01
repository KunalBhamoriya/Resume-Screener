"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class ResumeInput(BaseModel):
    """Input model for a single resume."""
    name: str = Field(..., description="Candidate name or resume identifier")
    content: str = Field(..., description="Full resume text content")


class ScreeningRequest(BaseModel):
    """Request payload for screening multiple resumes against a JD."""
    job_description: str = Field(
        ...,
        description="Full job description text",
        min_length=50,
    )
    resumes: List[ResumeInput] = Field(
        ...,
        description="List of resumes to screen",
        min_length=1,
    )


class ResumeResult(BaseModel):
    """Screening result for a single resume."""
    name: str
    match_score: float = Field(..., ge=0, le=100, description="Match score 0–100")
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: str


class ScreeningResponse(BaseModel):
    """Response payload containing results for all resumes."""
    job_title_hint: Optional[str] = None
    total_resumes: int
    results: List[ResumeResult]
