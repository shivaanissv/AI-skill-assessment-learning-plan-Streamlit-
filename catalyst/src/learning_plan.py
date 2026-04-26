from __future__ import annotations

import math
from typing import Dict, List

from src.models import LearningPlan, LearningTask, SkillScore
from src.resources import get_resources_for_skill


ADJACENT_SKILLS: Dict[str, List[str]] = {
    "Python": ["Testing", "APIs", "Performance Optimization"],
    "JavaScript": ["TypeScript", "Frontend Architecture", "Node.js APIs"],
    "SQL": ["Data Modeling", "ETL", "Query Optimization"],
    "Machine Learning": ["Feature Engineering", "Model Monitoring", "MLOps Basics"],
    "Deep Learning": ["Computer Vision", "NLP", "Model Compression"],
    "Data Analysis": ["Data Visualization", "Statistics", "Dashboarding"],
    "System Design": ["Caching", "Distributed Messaging", "Observability"],
    "Cloud": ["Infrastructure as Code", "CI/CD", "Cloud Security"],
    "Communication": ["Storytelling", "Stakeholder Management", "Technical Writing"],
    "Git": ["Code Review Practices", "Release Branching", "Monorepo Workflows"],
}


def _estimate_hours(skill_score: SkillScore) -> int:
    gap_factor = max(0.4, skill_score.gap / 50)
    base = 12 if skill_score.target_score <= 65 else 18
    weighted = base * gap_factor * (1 + (skill_score.jd_weight - 0.7))
    return max(4, int(round(weighted)))


def _weekly_focus(task_index: int, skill: str, adjacent_skill: str) -> str:
    return (
        f"Week {task_index + 1}: strengthen {skill} through practical work, "
        f"then bridge into {adjacent_skill} with one mini-project."
    )


def build_learning_plan(skill_scores: List[SkillScore], max_tasks: int = 5) -> LearningPlan:
    tasks: List[LearningTask] = []
    rationale: Dict[str, str] = {}

    gaps = [score for score in skill_scores if score.gap > 0]
    selected = gaps[:max_tasks]

    for idx, score in enumerate(selected):
        adjacent = ADJACENT_SKILLS.get(score.skill, ["Adjacent fundamentals"])[0]
        hours = _estimate_hours(score)
        resources = get_resources_for_skill(score.skill)
        rationale[score.skill] = (
            f"Prioritized because {score.skill} has a gap of {score.gap} "
            f"against target {score.target_score} and JD weight {score.jd_weight}."
        )
        tasks.append(
            LearningTask(
                skill=score.skill,
                adjacent_skill=adjacent,
                current_score=score.final_score,
                target_score=score.target_score,
                estimated_hours=hours,
                weekly_focus=_weekly_focus(idx, score.skill, adjacent),
                resources=resources,
            )
        )

    total_hours = sum(task.estimated_hours for task in tasks)
    estimated_weeks = max(1, math.ceil(total_hours / 8))
    return LearningPlan(
        tasks=tasks,
        total_estimated_hours=total_hours,
        estimated_weeks=estimated_weeks,
        rationale=rationale,
    )
