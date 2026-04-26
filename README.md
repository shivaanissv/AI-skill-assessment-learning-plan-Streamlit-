# Catalyst: AI Skill Assessment & Personalized Learning Plan Agent

This project evaluates what a candidate can actually do (not just claim on a resume) by combining:
- job-description skill extraction,
- conversational proficiency assessment per required skill,
- transparent scoring and gap prioritization,
- and a personalized, adjacent-skill learning roadmap with free resources.

## 1) Working Prototype

- **Local app:** Streamlit
- **Run command:** `streamlit run app.py`
- **Project site URL:** Add your deployment URL here after publishing (for example, Streamlit Community Cloud).

## 2) Quick Setup (Local)

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL shown in terminal (usually `http://localhost:8501`).

## 3) Realistic User Flow

1. Paste or upload a Job Description and Resume.
2. Click **Analyze Skills** to extract required skills and inferred resume evidence.
3. Answer adaptive assessment questions for each required skill.
4. Click **Generate Learning Plan**.
5. Review:
   - skill-wise scores,
   - target vs current gaps,
   - prioritized roadmap,
   - estimated effort (hours/weeks),
   - curated learning resources.
6. Download report as JSON.

## 4) Architecture

Core modules:
- `app.py`: Streamlit UI and workflow orchestration.
- `src/parsers.py`: text/file ingestion and normalization.
- `src/skill_extractor.py`: JD requirement parsing into weighted required skills.
- `src/assessment_engine.py`: adaptive questions and answer scoring.
- `src/scoring.py`: final score and gap-priority calculation.
- `src/learning_plan.py`: adjacent-skill roadmap and effort estimates.
- `src/resources.py`: free learning resource mapping.
- `src/models.py`: typed dataclasses for all entities.

Mermaid architecture source: `docs/architecture.mmd`  
Explanation: `docs/architecture.md`

## 5) Scoring and Logic

For each skill:

- `resumeEvidenceScore`: inferred from resume snippets relevant to that skill.
- `assessmentScore`: derived from answer depth + concept coverage.
- `confidenceConsistency`: rewards complete and consistent responses.

Final score:

`finalSkillScore = 0.35 * resumeEvidence + 0.50 * assessmentAnswers + 0.15 * confidenceConsistency`

Gap priority:

`gapPriority = jdWeight * max(0, targetScore - finalSkillScore)`

Learning effort estimate:

`estimatedHours ~= baseHours * gapFactor * adjacencyModifier`

This is an explainable heuristic MVP and not a psychometric certification system.

