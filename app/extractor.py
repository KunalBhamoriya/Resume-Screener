"""
Skill extraction utilities.
Uses a curated skills vocabulary + spaCy/regex-based extraction.
"""

import re
from typing import List, Set

# ---------------------------------------------------------------------------
# Curated skills vocabulary (extend as needed)
# ---------------------------------------------------------------------------
SKILLS_VOCAB: Set[str] = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "go",
    "rust", "kotlin", "swift", "ruby", "php", "scala", "r", "matlab",
    "bash", "shell", "powershell", "perl", "dart", "elixir", "haskell",

    # Web Frameworks / Libraries
    "react", "reactjs", "react.js", "angular", "vue", "vuejs", "nextjs",
    "nuxtjs", "svelte", "django", "flask", "fastapi", "express", "expressjs",
    "spring", "spring boot", "laravel", "rails", "asp.net", ".net", "node",
    "nodejs", "node.js", "nestjs",

    # Databases
    "sql", "mysql", "postgresql", "postgres", "sqlite", "oracle", "mongodb",
    "redis", "cassandra", "dynamodb", "firestore", "elasticsearch", "neo4j",
    "mariadb", "mssql",

    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
    "terraform", "ansible", "jenkins", "github actions", "circleci",
    "gitlab ci", "ci/cd", "helm", "prometheus", "grafana", "datadog",

    # AI / ML / Data
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "pytorch", "tensorflow", "keras", "scikit-learn",
    "sklearn", "xgboost", "lightgbm", "pandas", "numpy", "matplotlib",
    "seaborn", "spark", "hadoop", "kafka", "airflow", "mlflow",
    "hugging face", "transformers", "bert", "gpt", "llm", "langchain",
    "rag", "vector database", "pinecone", "weaviate", "chroma",

    # General Engineering
    "git", "github", "gitlab", "bitbucket", "rest", "restful", "graphql",
    "grpc", "microservices", "api", "websocket", "oauth", "jwt", "linux",
    "unix", "agile", "scrum", "jira", "confluence", "system design",
    "object oriented", "oop", "solid", "design patterns", "tdd", "bdd",

    # Testing
    "pytest", "junit", "jest", "cypress", "selenium", "playwright",
    "postman", "unit testing", "integration testing",

    # Data Engineering / Analytics
    "etl", "data pipeline", "data warehouse", "dbt", "snowflake", "bigquery",
    "redshift", "tableau", "power bi", "looker", "excel",

    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",
}

# Compile all skill phrases as regex patterns (longest first to avoid partial matches)
_SORTED_SKILLS = sorted(SKILLS_VOCAB, key=len, reverse=True)
_SKILL_PATTERNS = [
    re.compile(rf"\b{re.escape(skill)}\b", re.IGNORECASE)
    for skill in _SORTED_SKILLS
]


def extract_skills(text: str) -> List[str]:
    """
    Extract skills from text using the curated vocabulary.

    Returns a deduplicated, lowercased list of matched skills.
    """
    found: Set[str] = set()
    normalized_text = text.lower()
    for skill, pattern in zip(_SORTED_SKILLS, _SKILL_PATTERNS):
        if pattern.search(normalized_text):
            found.add(skill.lower())
    return sorted(found)


def extract_experience_years(text: str) -> float | None:
    """
    Attempt to extract total years of experience from text.
    Returns None if not found.
    """
    patterns = [
        r"(\d+)\+?\s*years?\s+(?:of\s+)?experience",
        r"experience\s+(?:of\s+)?(\d+)\+?\s*years?",
        r"(\d+)\+?\s*yrs?\s+(?:of\s+)?experience",
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None
