from __future__ import annotations

from typing import Dict, List

from src.models import SkillAssessment, SkillRequirement, SkillScore


def estimate_resume_evidence_score(requirement: SkillRequirement) -> float:
    snippets = requirement.evidence_snippets
    if not snippets:
        return 20.0
    richness = min(100.0, 35 + len(snippets) * 18)
    keyword_diversity = min(15.0, len(set(" ".join(snippets).lower().split())) * 0.15)
    return min(100.0, richness + keyword_diversity)


def target_score_from_importance(importance: str) -> float:
    mapping = {
        "must-have": 82.0,
        "core": 72.0,
        "nice-to-have": 60.0,
    }
    return mapping.get(importance, 70.0)


def compute_skill_scores(
    requirements: List[SkillRequirement],
    assessments: Dict[str, SkillAssessment],
) -> List[SkillScore]:
    results: List[SkillScore] = []
    for requirement in requirements:
        assessment = assessments.get(requirement.name)
        resume_score = estimate_resume_evidence_score(requirement)
        assessment_score = assessment.assessment_score if assessment else 0.0
        confidence = assessment.confidence_consistency if assessment else 30.0
        final_score = (
            0.35 * resume_score
            + 0.50 * assessment_score
            + 0.15 * confidence
        )
        target = target_score_from_importance(requirement.importance)
        gap = max(0.0, target - final_score)
        priority = requirement.jd_weight * gap

        results.append(
            SkillScore(
                skill=requirement.name,
                resume_evidence_score=round(resume_score, 2),
                assessment_score=round(assessment_score, 2),
                confidence_consistency=round(confidence, 2),
                final_score=round(final_score, 2),
                target_score=round(target, 2),
                gap=round(gap, 2),
                jd_weight=requirement.jd_weight,
                priority_score=round(priority, 2),
            )
        )

    return sorted(results, key=lambda x: x.priority_score, reverse=True)
