"""
Embedding-based resume screener.

Uses sentence-transformers (all-MiniLM-L6-v2) to generate embeddings,
then computes cosine similarity between JD and each resume.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from app.extractor import extract_experience_years, extract_skills
from app.models import ResumeInput, ResumeResult

# ---------------------------------------------------------------------------
# Singleton model loader
# ---------------------------------------------------------------------------
_MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    """Load (and cache) the sentence-transformer model."""
    return SentenceTransformer(_MODEL_NAME)


# ---------------------------------------------------------------------------
# Core similarity helpers
# ---------------------------------------------------------------------------

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Return cosine similarity in [0, 1]."""
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def _embed(texts: List[str]) -> np.ndarray:
    """Return L2-normalised embeddings for a list of texts."""
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings  # shape (N, D)


# ---------------------------------------------------------------------------
# Explanation generator
# ---------------------------------------------------------------------------

def _generate_explanation(
    name: str,
    score: float,
    matched: List[str],
    missing: List[str],
    jd_experience: float | None,
    resume_experience: float | None,
) -> str:
    """Produce a 2–3 sentence human-readable explanation."""
    # Tier labels
    if score >= 80:
        tier = "excellent"
    elif score >= 60:
        tier = "good"
    elif score >= 40:
        tier = "moderate"
    else:
        tier = "low"

    matched_str = ", ".join(matched[:5]) if matched else "none"
    missing_str = ", ".join(missing[:5]) if missing else "none"

    sentences = [
        f"{name} shows a {tier} match ({score:.1f}/100) with the job description.",
    ]

    if matched:
        sentences.append(
            f"Key matched skills include: {matched_str}."
        )
    if missing:
        sentences.append(
            f"Notable gaps: {missing_str} are required but not found in this resume."
        )
    elif score >= 70:
        sentences.append(
            "The candidate covers all major skill requirements mentioned in the JD."
        )

    if jd_experience and resume_experience:
        if resume_experience >= jd_experience:
            sentences.append(
                f"Experience requirement ({jd_experience:.0f}+ yrs) is met "
                f"({resume_experience:.0f} yrs claimed)."
            )
        else:
            sentences.append(
                f"Experience gap: JD needs {jd_experience:.0f}+ yrs; "
                f"resume shows only {resume_experience:.0f} yrs."
            )

    return " ".join(sentences[:3])  # cap at 3 sentences


# Main screening function


def screen_resumes(
    job_description: str,
    resumes: List[ResumeInput],
) -> List[ResumeResult]:
    """
    Screen a list of resumes against a job description.

    Steps:
    1. Extract skills from JD and each resume.
    2. Compute embedding-based cosine similarity (semantic score).
    3. Compute skill-overlap score (precision/recall hybrid).
    4. Blend both scores (70% semantic, 30% skill overlap).
    5. Build and return structured ResumeResult objects.
    """
    # --- extract JD skills & experience ---
    jd_skills = set(extract_skills(job_description))
    jd_experience = extract_experience_years(job_description)

    # --- embed JD + all resumes in one batch for efficiency ---
    all_texts = [job_description] + [r.content for r in resumes]
    all_embeddings = _embed(all_texts)

    jd_embedding = all_embeddings[0]
    resume_embeddings = all_embeddings[1:]

    results: List[ResumeResult] = []

    for idx, resume in enumerate(resumes):
        resume_skills = set(extract_skills(resume.content))
        resume_experience = extract_experience_years(resume.content)

        # Semantic similarity (already normalised embeddings → dot product = cosine)
        semantic_sim = float(np.dot(jd_embedding, resume_embeddings[idx]))
        semantic_score = max(0.0, min(1.0, semantic_sim))  # clamp

        # Skill overlap score
        if jd_skills:
            matched_skills = sorted(jd_skills & resume_skills)
            missing_skills = sorted(jd_skills - resume_skills)
            # F1-like blend of recall (coverage) and precision
            recall = len(matched_skills) / len(jd_skills)
            extra = resume_skills - jd_skills
            precision = len(matched_skills) / len(resume_skills) if resume_skills else 0
            skill_overlap = (
                2 * precision * recall / (precision + recall)
                if (precision + recall) > 0 else 0.0
            )
        else:
            matched_skills = []
            missing_skills = []
            skill_overlap = 0.5  # no JD skills → neutral

        # Blended score
        blended = 0.70 * semantic_score + 0.30 * skill_overlap
        match_score = round(blended * 100, 1)

        explanation = _generate_explanation(
            name=resume.name,
            score=match_score,
            matched=matched_skills,
            missing=missing_skills,
            jd_experience=jd_experience,
            resume_experience=resume_experience,
        )

        results.append(
            ResumeResult(
                name=resume.name,
                match_score=match_score,
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                explanation=explanation,
            )
        )

    # Sort by score descending
    results.sort(key=lambda r: r.match_score, reverse=True)
    return results
