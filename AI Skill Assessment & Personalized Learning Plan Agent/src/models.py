from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class SkillRequirement:
    name: str
    category: str
    importance: str
    jd_weight: float
    evidence_snippets: List[str] = field(default_factory=list)


@dataclass
class AssessmentQuestion:
    skill: str
    prompt: str
    expected_keywords: List[str]
    difficulty: str


@dataclass
class SkillAssessment:
    skill: str
    answer_scores: List[float]
    answer_notes: List[str]
    assessment_score: float
    confidence_consistency: float


@dataclass
class SkillScore:
    skill: str
    resume_evidence_score: float
    assessment_score: float
    confidence_consistency: float
    final_score: float
    target_score: float
    gap: float
    jd_weight: float
    priority_score: float


@dataclass
class LearningResource:
    title: str
    url: str
    resource_type: str


@dataclass
class LearningTask:
    skill: str
    adjacent_skill: str
    current_score: float
    target_score: float
    estimated_hours: int
    weekly_focus: str
    resources: List[LearningResource]


@dataclass
class LearningPlan:
    tasks: List[LearningTask]
    total_estimated_hours: int
    estimated_weeks: int
    rationale: Dict[str, str]
