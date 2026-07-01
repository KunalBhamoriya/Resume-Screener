"""
Unit tests for the Resume Screening System.
Run: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.extractor import extract_skills, extract_experience_years
from app.screener import screen_resumes
from app.models import ResumeInput

client = TestClient(app)


# tests


class TestExtractSkills:
    def test_basic_skills(self):
        text = "I know Python, FastAPI, PostgreSQL, and Docker."
        skills = extract_skills(text)
        assert "python" in skills
        assert "fastapi" in skills
        assert "postgresql" in skills
        assert "docker" in skills

    def test_case_insensitive(self):
        text = "PYTHON REACT AWS"
        skills = extract_skills(text)
        assert "python" in skills
        assert "react" in skills
        assert "aws" in skills

    def test_no_skills(self):
        text = "I love cooking and hiking."
        skills = extract_skills(text)
        assert skills == []

    def test_multi_word_skills(self):
        text = "Machine learning and deep learning experience with scikit-learn"
        skills = extract_skills(text)
        assert "machine learning" in skills
        assert "deep learning" in skills


class TestExtractExperience:
    def test_years_pattern(self):
        text = "I have 5 years of experience in software development."
        years = extract_experience_years(text)
        assert years == 5.0

    def test_plus_years_pattern(self):
        text = "Looking for 3+ years experience in Python."
        years = extract_experience_years(text)
        assert years == 3.0

    def test_no_experience(self):
        text = "Recent graduate seeking entry-level position."
        years = extract_experience_years(text)
        assert years is None


# Screener tests

class TestScreenResumes:
    def test_basic_screening(self):
        jd = (
            "We need a Python developer with FastAPI, PostgreSQL, Docker experience. "
            "3+ years of experience required."
        )
        resumes = [
            ResumeInput(
                name="Expert",
                content="5 years of Python, FastAPI, PostgreSQL, Docker, AWS, Redis experience.",
            ),
            ResumeInput(
                name="Beginner",
                content="Fresh graduate. Know basic HTML and CSS.",
            ),
        ]
        results = screen_resumes(jd, resumes)
        assert len(results) == 2
        # Expert should score higher
        assert results[0].name == "Expert"
        assert results[0].match_score > results[1].match_score

    def test_matched_skills_subset_of_jd_skills(self):
        jd = "Need Python and Docker skills."
        resumes = [
            ResumeInput(name="A", content="I use Python and Docker daily."),
        ]
        results = screen_resumes(jd, resumes)
        for skill in results[0].matched_skills:
            assert skill in ["python", "docker"]

    def test_score_range(self):
        jd = "Python FastAPI developer needed with 3+ years experience."
        resumes = [
            ResumeInput(name="Dev", content="Python developer with FastAPI experience."),
        ]
        results = screen_resumes(jd, resumes)
        assert 0 <= results[0].match_score <= 100

    def test_explanation_not_empty(self):
        jd = "Python and React developer with AWS experience."
        resumes = [
            ResumeInput(name="Cand", content="I know Python, React, and Node.js."),
        ]
        results = screen_resumes(jd, resumes)
        assert len(results[0].explanation) > 10


# API endpoint tests

class TestScreenEndpoint:
    def test_health(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_screen_valid(self):
        payload = {
            "job_description": (
                "We are looking for a Python Backend Engineer with 3+ years of experience. "
                "Must know FastAPI, PostgreSQL, Docker, and AWS. REST API design is essential."
            ),
            "resumes": [
                {
                    "name": "Good Candidate",
                    "content": (
                        "5 years of Python experience. Expert in FastAPI and Django. "
                        "PostgreSQL, Redis, Docker, Kubernetes, AWS. REST API, GraphQL."
                    ),
                },
                {
                    "name": "Weak Candidate",
                    "content": "I know a bit of HTML and CSS. Learning JavaScript.",
                },
            ],
        }
        resp = client.post("/screen", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_resumes"] == 2
        assert len(data["results"]) == 2
        # Good candidate should rank first
        assert data["results"][0]["name"] == "Good Candidate"
        # All required fields present
        for r in data["results"]:
            assert "match_score" in r
            assert "matched_skills" in r
            assert "missing_skills" in r
            assert "explanation" in r

    def test_screen_jd_too_short(self):
        payload = {
            "job_description": "Short JD",  # < 50 chars
            "resumes": [{"name": "X", "content": "Some resume content here."}],
        }
        resp = client.post("/screen", json=payload)
        assert resp.status_code == 422

    def test_screen_no_resumes(self):
        payload = {
            "job_description": "A" * 60,
            "resumes": [],
        }
        resp = client.post("/screen", json=payload)
        assert resp.status_code == 422
