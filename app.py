from __future__ import annotations

import json
from dataclasses import asdict
from typing import Dict, List

import streamlit as st

from src.assessment_engine import evaluate_skill_answers, generate_questions
from src.learning_plan import build_learning_plan
from src.models import SkillAssessment, SkillRequirement
from src.parsers import merge_text_sources
from src.scoring import compute_skill_scores
from src.skill_extractor import extract_required_skills


st.set_page_config(page_title="Catalyst Skill Agent", layout="wide")
st.title("AI-Powered Skill Assessment & Personalized Learning Plan")
st.caption(
    "Upload/paste a Job Description and Resume, answer adaptive questions, "
    "and receive a gap-based learning roadmap."
)


def _init_state() -> None:
    defaults = {
        "requirements": [],
        "questions_by_skill": {},
        "assessments": {},
        "skill_scores": [],
        "learning_plan": None,
        "jd_text": "",
        "resume_text": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _serialize_report(
    requirements: List[SkillRequirement],
    assessments: Dict[str, SkillAssessment],
    skill_scores,
    learning_plan,
) -> str:
    payload = {
        "requirements": [asdict(req) for req in requirements],
        "assessments": {skill: asdict(item) for skill, item in assessments.items()},
        "skill_scores": [asdict(score) for score in skill_scores],
        "learning_plan": asdict(learning_plan) if learning_plan else None,
    }
    return json.dumps(payload, indent=2)


_init_state()

with st.sidebar:
    st.header("Instructions")
    st.markdown(
        "- Add JD and resume text (or upload files).\n"
        "- Click **Analyze Skills** to extract required skills.\n"
        "- Answer assessment questions.\n"
        "- Click **Generate Learning Plan** to get final report."
    )

col1, col2 = st.columns(2)
with col1:
    st.subheader("Job Description")
    jd_file = st.file_uploader(
        "Upload JD file (txt/md/pdf/docx)",
        type=["txt", "md", "pdf", "docx"],
        key="jd_file",
    )
    jd_raw = st.text_area("Or paste JD text", height=260, key="jd_raw")

with col2:
    st.subheader("Candidate Resume")
    resume_file = st.file_uploader(
        "Upload Resume file (txt/md/pdf/docx)",
        type=["txt", "md", "pdf", "docx"],
        key="resume_file",
    )
    resume_raw = st.text_area("Or paste resume text", height=260, key="resume_raw")


if st.button("Analyze Skills", type="primary"):
    jd_text = merge_text_sources(jd_raw, jd_file)
    resume_text = merge_text_sources(resume_raw, resume_file)
    if not jd_text or not resume_text:
        st.error("Please provide both Job Description and Resume text.")
    else:
        requirements = extract_required_skills(jd_text, resume_text)
        questions = {
            req.name: generate_questions(req, resume_text=resume_text) for req in requirements
        }
        st.session_state["requirements"] = requirements
        st.session_state["questions_by_skill"] = questions
        st.session_state["assessments"] = {}
        st.session_state["skill_scores"] = []
        st.session_state["learning_plan"] = None
        st.session_state["jd_text"] = jd_text
        st.session_state["resume_text"] = resume_text
        st.success(f"Identified {len(requirements)} skills. Answer the questions below.")


requirements: List[SkillRequirement] = st.session_state["requirements"]
questions_by_skill = st.session_state["questions_by_skill"]

if requirements:
    st.markdown("---")
    st.subheader("Required Skills Extracted")
    skill_rows = [
        {
            "Skill": req.name,
            "Category": req.category,
            "Importance": req.importance,
            "JD Weight": req.jd_weight,
            "Resume Evidence Found": len(req.evidence_snippets),
        }
        for req in requirements
    ]
    st.dataframe(skill_rows, use_container_width=True)

    st.markdown("---")
    st.subheader("Conversational Skill Assessment")
    all_answers: Dict[str, List[str]] = {}

    for req in requirements:
        with st.expander(f"{req.name} ({req.importance})", expanded=False):
            if req.evidence_snippets:
                st.write("Resume evidence:")
                for snippet in req.evidence_snippets[:3]:
                    st.caption(f"- {snippet}")
            answers: List[str] = []
            for idx, question in enumerate(questions_by_skill[req.name], start=1):
                key = f"answer::{req.name}::{idx}"
                answer = st.text_area(
                    f"Q{idx}: {question.prompt}",
                    key=key,
                    placeholder="Write a practical, specific answer.",
                    height=120,
                )
                answers.append(answer)
            all_answers[req.name] = answers

    if st.button("Generate Learning Plan", type="primary"):
        assessments: Dict[str, SkillAssessment] = {}
        for req in requirements:
            assessments[req.name] = evaluate_skill_answers(
                requirement=req,
                questions=questions_by_skill[req.name],
                answers=all_answers[req.name],
            )

        skill_scores = compute_skill_scores(requirements, assessments)
        learning_plan = build_learning_plan(skill_scores)
        st.session_state["assessments"] = assessments
        st.session_state["skill_scores"] = skill_scores
        st.session_state["learning_plan"] = learning_plan
        st.success("Assessment completed. Scroll for the report.")


if st.session_state["skill_scores"]:
    st.markdown("---")
    st.subheader("Skill Gap Report")
    score_rows = [
        {
            "Skill": score.skill,
            "Final Score": score.final_score,
            "Target Score": score.target_score,
            "Gap": score.gap,
            "Priority Score": score.priority_score,
        }
        for score in st.session_state["skill_scores"]
    ]
    st.dataframe(score_rows, use_container_width=True)

    st.subheader("Personalized Learning Plan")
    learning_plan = st.session_state["learning_plan"]
    if learning_plan and learning_plan.tasks:
        st.write(
            f"Estimated effort: **{learning_plan.total_estimated_hours} hours** "
            f"across **~{learning_plan.estimated_weeks} weeks**."
        )
        for task in learning_plan.tasks:
            st.markdown(
                f"### {task.skill} -> {task.adjacent_skill}\n"
                f"- Current vs Target: {task.current_score} -> {task.target_score}\n"
                f"- Estimated Hours: {task.estimated_hours}\n"
                f"- Weekly Focus: {task.weekly_focus}"
            )
            for resource in task.resources:
                st.markdown(f"- [{resource.title}]({resource.url}) ({resource.resource_type})")
    else:
        st.info("No gaps detected. Candidate appears ready for listed requirements.")

    report_json = _serialize_report(
        requirements=st.session_state["requirements"],
        assessments=st.session_state["assessments"],
        skill_scores=st.session_state["skill_scores"],
        learning_plan=st.session_state["learning_plan"],
    )
    st.download_button(
        label="Download Report JSON",
        data=report_json,
        file_name="catalyst_skill_assessment_report.json",
        mime="application/json",
    )
