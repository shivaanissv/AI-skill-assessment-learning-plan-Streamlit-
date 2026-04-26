from __future__ import annotations

import io
import re
from typing import Iterable, List, Tuple

from pypdf import PdfReader


def normalize_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


def split_bullets(text: str) -> List[str]:
    lines = [line.strip("-* ").strip() for line in text.splitlines()]
    return [line for line in lines if len(line) > 2]


def extract_sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def read_uploaded_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith((".txt", ".md", ".csv")):
        return uploaded_file.read().decode("utf-8", errors="ignore")

    if name.endswith(".pdf"):
        data = io.BytesIO(uploaded_file.read())
        reader = PdfReader(data)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages)

    if name.endswith(".docx"):
        try:
            from docx import Document
        except ImportError:
            return ""
        doc = Document(io.BytesIO(uploaded_file.read()))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    return ""


def merge_text_sources(raw_text: str, uploaded_file) -> str:
    source_chunks: List[str] = []
    if raw_text and raw_text.strip():
        source_chunks.append(raw_text.strip())
    if uploaded_file is not None:
        file_text = read_uploaded_file(uploaded_file).strip()
        if file_text:
            source_chunks.append(file_text)
    return normalize_text("\n\n".join(source_chunks))


def pick_evidence_snippets(resume_text: str, skill_tokens: Iterable[str], limit: int = 3) -> List[str]:
    sentences = extract_sentences(resume_text)
    selected: List[str] = []
    token_set = {token.lower() for token in skill_tokens}
    for sentence in sentences:
        lowered = sentence.lower()
        if any(token in lowered for token in token_set):
            selected.append(sentence)
        if len(selected) >= limit:
            break
    return selected


_SECTION_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"^\s*(?:#{0,3}\s*)?projects?(?:\s+experience)?\s*:?\s*$", re.I), "Projects"),
    (re.compile(r"^\s*(?:#{0,3}\s*)?(relevant|academic|personal)?\s*projects?\s*:?\s*$", re.I), "Projects"),
    (re.compile(
        r"^\s*(?:#{0,3}\s*)?(work(\s+history|experience|places)?|professional(\s+experience|background)?|employment|experience)\s*:?\s*$",
        re.I,
    ), "Experience"),
]


def _section_header_name(line: str) -> str | None:
    stripped = line.strip()
    for pat, name in _SECTION_PATTERNS:
        if pat.match(stripped):
            return name
    return None


def _strip_bullet_prefix(line: str) -> str:
    return re.sub(r"^\s*(?:[-*•·◦]|\d+[\).])\s*", "", line).strip()


def iter_section_bullets(resume_text: str) -> List[Tuple[str, str]]:
    """
    Yields (section, bullet_text) for non-empty lines under known Projects/Experience
    section headers. Bullet detection is best-effort for common resume layouts.
    """
    current: str | None = None
    out: List[Tuple[str, str]] = []
    for raw in resume_text.splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        header = _section_header_name(line)
        if header is not None:
            current = header
            continue
        if not current:
            continue
        stripped = line.lstrip()
        is_bullet = bool(
            re.match(r"^[-*•·◦]", stripped) or re.match(r"^\d+[\).]", stripped)
        )
        if is_bullet:
            text = _strip_bullet_prefix(stripped)
            if len(text) > 3:
                out.append((current, text))
        elif len(stripped) > 12 and not stripped.endswith(":"):
            out.append((current, stripped))
    return out


def _norm_snippet_key(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())[:200]


def refine_resume_line(text: str) -> str:
    """
    Strip common section labels and bullet markers so quoted context reads cleanly
    in assessment prompts.
    """
    t = text.strip()
    t = re.sub(
        r"^(?:projects?|relevant projects|experience|work experience|employment|work history)\s*:\s*",
        "",
        t,
        flags=re.IGNORECASE,
    )
    t = t.lstrip()
    t = re.sub(r"^[-*•·◦]\s*", "", t)
    t = re.sub(r"^\d+[\).]\s*", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def grounding_lines_for_skill(
    resume_text: str,
    skill_aliases: List[str],
    prior_snippets: List[str],
    max_lines: int = 5,
) -> List[Tuple[str, str]]:
    """
    Build ordered (section_label, line) pairs to ground questions in projects and experience.
    Merges sentence-based evidence, section bullets that mention the skill, and
    a small fallback of section bullets if matches are thin.
    """
    aliases = [a.lower() for a in skill_aliases if a]
    if not aliases:
        aliases = ["skill"]

    def mentions_skill(text: str) -> bool:
        low = text.lower()
        return any(a in low for a in aliases)

    seen: set[str] = set()
    rows: List[Tuple[str, str]] = []

    def add_row(section: str, text: str) -> None:
        key = _norm_snippet_key(text)
        if not key or key in seen:
            return
        seen.add(key)
        rows.append((section, text))

    # Prefer structured Projects/Experience bullets, then other resume evidence.
    for section, line in iter_section_bullets(resume_text):
        if mentions_skill(line):
            cleaned = refine_resume_line(line)
            if len(cleaned) > 5:
                add_row(section, cleaned)

    for s in prior_snippets:
        cleaned = refine_resume_line(s)
        if len(cleaned) > 5:
            add_row("Resume", cleaned)

    for sent in pick_evidence_snippets(resume_text, skill_aliases, limit=3):
        cleaned = refine_resume_line(sent)
        if len(cleaned) > 5:
            add_row("Resume", cleaned)

    if len(rows) < 2:
        for section, line in iter_section_bullets(resume_text):
            if section in ("Projects", "Experience") and mentions_skill(line):
                cleaned = refine_resume_line(line)
                if len(cleaned) > 5:
                    add_row(section, cleaned)
            if len(rows) >= 3:
                break

    return rows[:max_lines]
