from __future__ import annotations

import re
from statistics import mean
from typing import Dict, List, Tuple

from src.models import AssessmentQuestion, SkillAssessment, SkillRequirement
from src.parsers import grounding_lines_for_skill
from src.skill_extractor import SKILL_KEYWORDS

QUESTION_TEMPLATES: List[Tuple[str, str]] = [
    (
        "Explain a recent scenario where you used {skill}. What was the challenge and outcome?",
        "applied",
    ),
    (
        "What are the top mistakes teams make with {skill}, and how do you avoid them?",
        "applied",
    ),
    (
        "If you had to teach a junior teammate one practical concept in {skill}, what would you choose?",
        "fundamental",
    ),
]

# Used when we have at least one resume or project line to anchor the prompt.
RESUME_GROUNDED_TEMPLATES: List[Tuple[str, str]] = [
    (
        "From {section} — {context} — How did {skill} show up in that work, what did you "
        "own, and what was a concrete result or learning?",
        "applied",
    ),
    (
        "This appears in {section}: {context} — For {skill}, what would you do differently "
        "on a second pass, and what trade-offs or risks would you name?",
        "applied",
    ),
    (
        "Grounded in {section} — {context} — If a junior on that work asked for one {skill} "
        "lesson you took from the experience, what would you teach, and how would you verify they "
        "could apply it?",
        "fundamental",
    ),
]


def _format_section_phrase(section: str) -> str:
    if section == "Resume":
        return "your resume"
    if section in ("Projects", "Experience"):
        return f"your {section.lower()}"
    return f"your {section}"


def _clip_context(s: str, max_len: int = 200) -> str:
    t = s.strip().replace("\n", " ")
    if len(t) <= max_len:
        return t
    return t[: max(1, max_len - 1)].rstrip() + "…"


_STOP = frozenset(
    "a an the and or to of in for on with at from by as is are was were be been "
    "it this that we i my our your they he she them their a few some any".split()
)

SKILL_EXPECTED_KEYWORDS: Dict[str, List[str]] = {
    "Python": ["function", "class", "api", "testing", "performance"],
    "JavaScript": ["async", "event loop", "component", "state", "api"],
    "SQL": ["join", "index", "query", "normalization", "aggregation"],
    "Machine Learning": ["feature", "validation", "overfitting", "metric", "model"],
    "Deep Learning": ["layer", "backpropagation", "epoch", "optimizer", "loss"],
    "Data Analysis": ["eda", "visualization", "pandas", "insight", "hypothesis"],
    "Communication": ["stakeholder", "clarity", "feedback", "alignment", "impact"],
    "System Design": ["scalability", "latency", "tradeoff", "availability", "consistency"],
    "Cloud": ["deployment", "monitoring", "cost", "security", "scaling"],
    "Git": ["branch", "merge", "rebase", "commit", "pull request"],
}


def _content_word_boost(context: str, cap: int = 6) -> List[str]:
    out: List[str] = []
    for w in re.findall(r"[A-Za-z][A-Za-z0-9\-]+", context):
        low = w.lower()
        if len(low) < 3 or low in _STOP:
            continue
        if low not in out:
            out.append(low)
        if len(out) >= cap:
            break
    return out


def _expected_keywords_for_question(skill: str, context: str) -> List[str]:
    base = list(SKILL_EXPECTED_KEYWORDS.get(skill, [skill.lower()]))
    for w in _content_word_boost(context):
        if w not in {b.lower() for b in base}:
            base.append(w)
    return base[: 14]


def _format_context_quoted(context: str) -> str:
    c = _clip_context(context)
    if not c:
        return '""'
    return f"“{c}”"


def generate_questions(
    requirement: SkillRequirement,
    resume_text: str = "",
    max_questions: int = 3,
) -> List[AssessmentQuestion]:
    meta = SKILL_KEYWORDS.get(requirement.name) or {
        "aliases": [requirement.name.lower()],
    }
    aliases: List[str] = list(meta.get("aliases", [requirement.name.lower()]))

    rows = grounding_lines_for_skill(resume_text, aliases, requirement.evidence_snippets, max_lines=5)
    use_grounded = bool(rows)
    questions: List[AssessmentQuestion] = []

    if use_grounded:
        for i, (template, difficulty) in enumerate(RESUME_GROUNDED_TEMPLATES[:max_questions]):
            section, line = rows[i % len(rows)]
            context_display = _format_context_quoted(line)
            section_phrase = _format_section_phrase(section)
            prompt = template.format(
                section=section_phrase,
                context=context_display,
                skill=requirement.name,
            )
            expected = _expected_keywords_for_question(requirement.name, line)
            questions.append(
                AssessmentQuestion(
                    skill=requirement.name,
                    prompt=prompt,
                    expected_keywords=expected,
                    difficulty=difficulty,
                )
            )
        return questions

    for template, difficulty in QUESTION_TEMPLATES[:max_questions]:
        prompt = template.format(skill=requirement.name)
        expected = SKILL_EXPECTED_KEYWORDS.get(requirement.name, [requirement.name.lower()])
        questions.append(
            AssessmentQuestion(
                skill=requirement.name,
                prompt=prompt,
                expected_keywords=expected,
                difficulty=difficulty,
            )
        )
    return questions


def _score_single_answer(answer: str, expected_keywords: List[str], resume_evidence_count: int) -> Tuple[float, str]:
    if not answer.strip():
        return 0.0, "No answer provided."

    lowered = answer.lower()
    tokens = set(re.findall(r"[a-zA-Z0-9\-\+]+", lowered))
    keyword_hits = sum(1 for kw in expected_keywords if kw.lower() in lowered)
    keyword_score = min(100.0, (keyword_hits / max(1, len(expected_keywords))) * 100)

    length_bonus = min(20.0, len(tokens) * 0.8)
    evidence_bonus = min(10.0, resume_evidence_count * 3.0)

    score = min(100.0, keyword_score * 0.7 + length_bonus + evidence_bonus)
    note = f"Matched {keyword_hits}/{len(expected_keywords)} expected concepts."
    if len(tokens) < 20:
        note += " Response is short; depth may be limited."
    return score, note


def evaluate_skill_answers(
    requirement: SkillRequirement,
    questions: List[AssessmentQuestion],
    answers: List[str],
) -> SkillAssessment:
    answer_scores: List[float] = []
    notes: List[str] = []
    for question, answer in zip(questions, answers):
        score, note = _score_single_answer(
            answer=answer,
            expected_keywords=question.expected_keywords,
            resume_evidence_count=len(requirement.evidence_snippets),
        )
        answer_scores.append(score)
        notes.append(note)

    assessment_score = mean(answer_scores) if answer_scores else 0.0
    non_empty = [answer for answer in answers if answer.strip()]
    confidence_consistency = min(100.0, 40 + len(non_empty) * 20 + (assessment_score * 0.2))

    return SkillAssessment(
        skill=requirement.name,
        answer_scores=answer_scores,
        answer_notes=notes,
        assessment_score=assessment_score,
        confidence_consistency=confidence_consistency,
    )
