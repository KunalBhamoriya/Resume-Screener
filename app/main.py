"""
FastAPI application entrypoint for the Smart Resume Screening System.
"""

from __future__ import annotations

import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import io

import pdfplumber
from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.models import ScreeningRequest, ScreeningResponse
from app.screener import _get_model, screen_resumes


# pre-load the model at startup so the first request is not slow


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("⚡  Loading sentence-transformer model …")
    _get_model()          # warms the LRU cache
    print("✅  Model ready.")
    yield
    print("👋  Shutting down.")


# App


app = FastAPI(
    title="Smart Resume Screening API",
    description=(
        "AI-powered resume screening using sentence-transformer embeddings. "
        "Submit a Job Description and one or more resumes to get ranked results "
        "with match scores, skill gaps, and explanations."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the web UI
_STATIC_DIR = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


# Helper


def _extract_job_title(jd: str) -> Optional[str]:
    """Very light heuristic to pull a job title hint from the JD."""
    patterns = [
        r"(?:position|role|title|job)[\s:]+([A-Za-z][A-Za-z0-9 /\-&]{3,50})",
        r"^([A-Za-z][A-Za-z0-9 /\-&]{3,50})\n",
        r"(?:we are looking for|hiring)(?: an?| a)?\s+([A-Za-z][A-Za-z0-9 /\-&]{3,50})",
    ]
    for pat in patterns:
        m = re.search(pat, jd, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


# Routes


@app.get("/", tags=["UI"], include_in_schema=False)
async def root():
    """Serve the web UI."""
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/extract-pdf", tags=["Utils"], summary="Extract text from a PDF resume")
async def extract_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file and receive its extracted plain text.
    The UI uses this to auto-fill the resume content field.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are accepted.",
        )

    try:
        pdf_bytes = await file.read()
        text_pages = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text.strip())
        full_text = "\n\n".join(text_pages)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse PDF: {exc}",
        )

    if not full_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text found in PDF. It may be image-based (scanned). Please paste text manually.",
        )

    return {"filename": file.filename, "text": full_text, "pages": len(text_pages)}


@app.get("/health", tags=["Health"])
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "model": "all-MiniLM-L6-v2",
        "embedding_dim": 384,
    }


@app.post(
    "/screen",
    response_model=ScreeningResponse,
    status_code=status.HTTP_200_OK,
    tags=["Screening"],
    summary="Screen resumes against a job description",
    response_description="Ranked list of resume screening results",
)
async def screen(payload: ScreeningRequest):
    """
    **Screen resumes against a Job Description using embeddings.**

    - Encodes JD and each resume with `all-MiniLM-L6-v2`
    - Computes cosine similarity (semantic) + skill-overlap score
    - Returns ranked results with score, matched/missing skills, and explanation

    **Body:**
    - `job_description` – full JD text (min 50 chars)
    - `resumes` – list of `{ name, content }` objects (at least 1)
    """
    if not payload.resumes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one resume is required.",
        )

    try:
        t0 = time.perf_counter()
        results = screen_resumes(payload.job_description, payload.resumes)
        elapsed = round(time.perf_counter() - t0, 3)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Screening failed: {exc}",
        )

    return ScreeningResponse(
        job_title_hint=_extract_job_title(payload.job_description),
        total_resumes=len(results),
        results=results,
    )
