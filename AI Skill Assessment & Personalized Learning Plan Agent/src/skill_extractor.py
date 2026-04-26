from __future__ import annotations

from typing import Dict, List, Tuple

from src.models import SkillRequirement
from src.parsers import pick_evidence_snippets, split_bullets


SKILL_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "Python": {"category": "Programming", "aliases": ["python", "flask", "django", "fastapi"]},
    "JavaScript": {"category": "Programming", "aliases": ["javascript", "node", "react", "typescript"]},
    "SQL": {"category": "Data", "aliases": ["sql", "postgres", "mysql", "query optimization"]},
    "Machine Learning": {"category": "AI", "aliases": ["machine learning", "ml", "model training"]},
    "Deep Learning": {"category": "AI", "aliases": ["deep learning", "tensorflow", "pytorch"]},
    "Data Analysis": {"category": "Data", "aliases": ["data analysis", "pandas", "numpy", "analytics"]},
    "Communication": {"category": "Soft Skill", "aliases": ["communication", "stakeholder", "presentation"]},
    "System Design": {"category": "Architecture", "aliases": ["system design", "scalability", "distributed systems"]},
    "Cloud": {"category": "Infrastructure", "aliases": ["aws", "azure", "gcp", "cloud"]},
    "Git": {"category": "Collaboration", "aliases": ["git", "version control", "github", "gitlab"]},
}

MUST_HAVE_HINTS = ("must", "required", "mandatory", "strong", "expert")
NICE_TO_HAVE_HINTS = ("plus", "preferred", "good to have", "nice to have")


def _line_importance(line: str) -> Tuple[str, float]:
    lowered = line.lower()
    if any(hint in lowered for hint in MUST_HAVE_HINTS):
        return "must-have", 1.0
    if any(hint in lowered for hint in NICE_TO_HAVE_HINTS):
        return "nice-to-have", 0.7
    return "core", 0.85


def extract_required_skills(jd_text: str, resume_text: str) -> List[SkillRequirement]:
    lines = split_bullets(jd_text)
    found: Dict[str, SkillRequirement] = {}

    for line in lines:
        importance, weight = _line_importance(line)
        lowered = line.lower()
        for skill, details in SKILL_KEYWORDS.items():
            if any(alias in lowered for alias in details["aliases"]):
                existing = found.get(skill)
                evidence = pick_evidence_snippets(resume_text, details["aliases"])
                if existing:
                    existing.jd_weight = max(existing.jd_weight, weight)
                    if existing.importance != "must-have" and importance == "must-have":
                        existing.importance = importance
                    for snippet in evidence:
                        if snippet not in existing.evidence_snippets:
                            existing.evidence_snippets.append(snippet)
                else:
                    found[skill] = SkillRequirement(
                        name=skill,
                        category=details["category"],
                        importance=importance,
                        jd_weight=weight,
                        evidence_snippets=evidence,
                    )

    if not found:
        fallback = ["Python", "SQL", "Communication"]
        for skill in fallback:
            details = SKILL_KEYWORDS[skill]
            found[skill] = SkillRequirement(
                name=skill,
                category=details["category"],
                importance="core",
                jd_weight=0.8,
                evidence_snippets=pick_evidence_snippets(resume_text, details["aliases"]),
            )

    return sorted(found.values(), key=lambda s: s.jd_weight, reverse=True)
