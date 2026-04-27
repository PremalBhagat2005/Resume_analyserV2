"""
Detects the target industry/role from resume text.
Uses keyword frequency - no hardcoded names.
"""
from collections import Counter


# Each industry has weighted signal terms.
# Terms are generic enough to work across any resume.
INDUSTRY_PROFILES = {
    "Software Engineering": {
        "terms": [
            "python", "java", "javascript", "typescript",
            "react", "node", "flask", "django", "api",
            "backend", "frontend", "fullstack", "full stack",
            "microservices", "rest", "graphql", "git",
            "docker", "kubernetes", "ci/cd", "software engineer",
            "developer", "programming", "code", "repository",
        ],
        "weight": 1.0,
    },
    "Data Science / ML": {
        "terms": [
            "machine learning", "deep learning", "neural network",
            "data science", "pandas", "numpy", "tensorflow",
            "pytorch", "sklearn", "scikit", "model", "dataset",
            "prediction", "classification", "regression",
            "nlp", "computer vision", "jupyter", "colab",
            "data analysis", "statistics", "matplotlib",
        ],
        "weight": 1.0,
    },
    "Cloud / DevOps": {
        "terms": [
            "aws", "azure", "gcp", "cloud", "devops",
            "terraform", "ansible", "jenkins", "kubernetes",
            "docker", "pipeline", "infrastructure", "deployment",
            "monitoring", "logging", "container", "serverless",
            "lambda", "ec2", "s3", "linux", "bash",
        ],
        "weight": 1.0,
    },
    "Product Management": {
        "terms": [
            "product manager", "product roadmap", "stakeholder",
            "user story", "agile", "scrum", "sprint", "backlog",
            "kpi", "metrics", "product strategy", "go-to-market",
            "customer discovery", "mvp", "prioritization",
            "product owner", "jira", "confluence",
        ],
        "weight": 1.0,
    },
    "UI/UX Design": {
        "terms": [
            "figma", "sketch", "adobe xd", "user research",
            "wireframe", "prototype", "usability", "user experience",
            "user interface", "design system", "accessibility",
            "interaction design", "visual design", "ui", "ux",
            "user testing", "information architecture",
        ],
        "weight": 1.0,
    },
    "Data Engineering": {
        "terms": [
            "etl", "data pipeline", "spark", "hadoop", "airflow",
            "kafka", "data warehouse", "dbt", "snowflake",
            "bigquery", "redshift", "data lake", "sql",
            "data modelling", "ingestion", "transformation",
        ],
        "weight": 1.0,
    },
    "Cybersecurity": {
        "terms": [
            "security", "penetration testing", "vulnerability",
            "firewall", "encryption", "siem", "soc", "malware",
            "threat", "compliance", "iso 27001", "owasp",
            "network security", "identity management", "zero trust",
        ],
        "weight": 1.0,
    },
    "Finance / Fintech": {
        "terms": [
            "financial analysis", "investment", "portfolio",
            "trading", "risk management", "valuation",
            "excel", "financial modelling", "bloomberg",
            "accounting", "audit", "revenue", "p&l",
            "fintech", "banking", "equity",
        ],
        "weight": 1.0,
    },
    "Marketing": {
        "terms": [
            "marketing", "seo", "sem", "content strategy",
            "social media", "campaign", "brand", "analytics",
            "google analytics", "conversion", "growth hacking",
            "email marketing", "copywriting", "paid ads",
        ],
        "weight": 1.0,
    },
    "General / Other": {
        "terms": [],
        "weight": 0.1,
    },
}


def detect_industry(text: str) -> dict:
    """
    Detect the most likely target industry from resume text.

    Returns:
    {
        "primary": str,
        "secondary": str,
        "confidence": str,
        "scores": dict,
    }
    """
    text_lower = text.lower()
    scores = {}

    for industry, profile in INDUSTRY_PROFILES.items():
        if not profile["terms"]:
            scores[industry] = 0
            continue
        count = sum(
            1 for term in profile["terms"]
            if term in text_lower
        )
        scores[industry] = count * profile["weight"]

    # Sort descending
    ranked = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    primary = ranked[0][0] if ranked else "General / Other"
    secondary = ranked[1][0] if len(ranked) > 1 else "General / Other"
    top_score = ranked[0][1] if ranked else 0

    if top_score >= 8:
        confidence = "High"
    elif top_score >= 4:
        confidence = "Medium"
    else:
        confidence = "Low"
        primary = "General / Other"

    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "scores": {k: round(v, 1) for k, v in ranked[:5]},
    }
