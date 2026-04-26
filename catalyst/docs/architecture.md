# Architecture and Scoring Logic

## System Overview

The system is a deterministic, explainable assessment pipeline with a conversational UI:

1. **Input ingestion**
   - Candidate provides Job Description (JD) and Resume via text or file upload.
   - Files supported: `txt`, `md`, `pdf`, `docx`.

2. **Skill extraction**
   - The JD is parsed for canonical skill aliases.
   - Each extracted skill gets:
     - a category,
     - an importance label (`must-have`, `core`, `nice-to-have`),
     - and a normalized JD weight used for prioritization.
   - Resume snippets are matched as evidence for each extracted skill.

3. **Conversational assessment**
   - The app generates 2-3 practical questions per required skill.
   - Candidate responses are scored on:
     - expected concept coverage,
     - response depth/length,
     - consistency across prompts.

4. **Scoring + gap analysis**
   - Per-skill final score is computed by blending resume evidence, answer quality, and confidence consistency.
   - A target score is derived from JD importance.
   - Gap and priority scores identify where learning effort should focus first.

5. **Learning plan generation**
   - Highest-priority gaps are transformed into learning tasks.
   - Each task includes:
     - an adjacent learnable skill path,
     - estimated hours and week-wise focus,
     - curated free resources.

6. **Output**
   - UI report with score table and roadmap.
   - Downloadable JSON artifact for recruiter/candidate workflows.

## Scoring Formulas

- `finalSkillScore = 0.35 * resumeEvidence + 0.50 * assessmentAnswers + 0.15 * confidenceConsistency`
- `gap = max(0, targetScore - finalSkillScore)`
- `priorityScore = jdWeight * gap`

Target score by importance:
- `must-have`: 82
- `core`: 72
- `nice-to-have`: 60

## Why this design works for MVP

- **Transparent**: every score is explainable.
- **Fast**: no paid API dependency required.
- **Extensible**: LLM-based questioning/scoring can replace heuristics later without changing core flow.
- **Practical**: outputs are action-oriented (not just pass/fail).
