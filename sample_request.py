"""
Sample data and quick demo script.
Run: python sample_request.py
"""

import json
import urllib.request
import urllib.error

SAMPLE_PAYLOAD = {
    "job_description": """
    Position: Senior Python Backend Engineer

    We are looking for a Senior Python Backend Engineer to join our AI team.
    
    Requirements:
    - 4+ years of experience in Python development
    - Strong knowledge of FastAPI or Django or Flask
    - Experience with machine learning frameworks (PyTorch, TensorFlow, scikit-learn)
    - Proficiency with SQL and NoSQL databases (PostgreSQL, MongoDB, Redis)
    - Hands-on experience with Docker and Kubernetes
    - Knowledge of AWS or GCP cloud services
    - Familiarity with REST API design and GraphQL
    - Experience with Git and CI/CD pipelines
    - Understanding of NLP and transformers is a big plus
    - Strong problem-solving skills and system design knowledge
    """,
    "resumes": [
        {
            "name": "Alice Johnson",
            "content": """
            Alice Johnson | Senior Software Engineer | alice@email.com

            EXPERIENCE (6 years):
            - Senior Backend Engineer at TechCorp (3 years)
              * Built REST APIs using FastAPI and Python
              * Deployed microservices on AWS using Docker and Kubernetes
              * Integrated PostgreSQL and Redis for data storage
              * Implemented CI/CD pipelines with GitHub Actions
            
            - Backend Developer at StartupXYZ (3 years)
              * Developed Django applications
              * Worked with MongoDB and MySQL
              * Used PyTorch for recommendation engine
            
            SKILLS:
            Python, FastAPI, Django, Flask, PostgreSQL, MongoDB, Redis,
            Docker, Kubernetes, AWS, GCP, Git, REST, GraphQL,
            PyTorch, scikit-learn, NLP, transformers, CI/CD, GitHub Actions,
            SQL, Linux, Agile, System Design
            
            EDUCATION: B.Tech Computer Science
            """
        },
        {
            "name": "Bob Smith",
            "content": """
            Bob Smith | Full Stack Developer | bob@email.com
            
            EXPERIENCE (3 years):
            - Full Stack Developer at WebAgency
              * Built React and Vue.js frontends
              * Node.js and Express backend APIs
              * MySQL and MongoDB databases
              * Deployed on AWS EC2
            
            SKILLS:
            JavaScript, TypeScript, React, Vue, Node.js, Express,
            MySQL, MongoDB, AWS, Docker, Git, REST API,
            HTML, CSS, Jest, Agile
            
            EDUCATION: B.Sc Computer Science
            """
        },
        {
            "name": "Carol White",
            "content": """
            Carol White | Data Scientist | carol@email.com
            
            EXPERIENCE (5 years):
            - Data Scientist at AnalyticsCo (5 years)
              * Built ML models using Python, PyTorch and TensorFlow
              * NLP pipeline development with transformers and BERT
              * Data processing with Pandas, NumPy
              * Used Scikit-learn for model training and evaluation
              * SQL queries on PostgreSQL and BigQuery
              * Deployed models as Python FastAPI services on GCP
              * MLflow for experiment tracking
            
            SKILLS:
            Python, PyTorch, TensorFlow, Scikit-learn, NLP, Transformers,
            BERT, Pandas, NumPy, FastAPI, PostgreSQL, SQL, GCP, BigQuery,
            MLflow, Docker, Git, REST, Jupyter
            
            EDUCATION: M.Sc Data Science
            """
        },
        {
            "name": "David Lee",
            "content": """
            David Lee | Junior Developer | david@email.com
            
            EXPERIENCE (1 year):
            - Junior Python Developer at SmallStartup
              * Helped maintain a Flask web application
              * Basic SQL queries with SQLite
              * Used Git for version control
            
            SKILLS:
            Python, Flask, SQLite, SQL, Git, HTML, CSS, JavaScript
            
            EDUCATION: B.Tech Information Technology (2023)
            """
        }
    ]
}


def main():
    url = "http://127.0.0.1:8000/screen"
    data = json.dumps(SAMPLE_PAYLOAD).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print("🚀 Sending screening request to", url)
    print("-" * 60)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"❌ Could not reach server: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return

    print(f"📌 Job Title Hint : {result.get('job_title_hint', 'N/A')}")
    print(f"📄 Total Resumes  : {result['total_resumes']}")
    print("=" * 60)

    for i, res in enumerate(result["results"], 1):
        print(f"\n#{i} {res['name']}")
        print(f"   Score          : {res['match_score']}/100")
        print(f"   Matched Skills : {', '.join(res['matched_skills'][:8]) or 'None'}")
        print(f"   Missing Skills : {', '.join(res['missing_skills'][:5]) or 'None'}")
        print(f"   Explanation    : {res['explanation']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
