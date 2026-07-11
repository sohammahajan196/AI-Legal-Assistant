"""
Section-boundary parser and metadata extractor.

Splits raw bare-act text into per-section chunks (not fixed token windows),
attaching domain/act/chapter/section metadata for citation purposes.
See PLAN.md Section 3 and TASKS.md T11.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Default max characters per chunk before splitting on numbered sub-clauses.
DEFAULT_MAX_SECTION_CHARS = 2000

SECTION_HEADER_RE = re.compile(r"^Section\s+(\d+[A-Z]?)\.\s+", re.MULTILINE)

CHAPTER_RE = re.compile(r"^CHAPTER\s+(.+?)\s*$", re.MULTILINE | re.IGNORECASE)

# Numbered sub-clause boundaries such as "(1)", "(2)" at line starts.
SUBCLAUSE_BOUNDARY_RE = re.compile(r"(?:^|\n)\((\d+)\)\s")

# IPC-style title terminator (em dash / hyphen variants after the title period).
_TITLE_EM_DASH_RE = re.compile(
    r"^(.+?)(?:\.[\u2014\u2013\u2015\u2012]|\.--|\.-)\s*",
    re.DOTALL,
)

# CrPC-style: title ends with a period before a numbered sub-clause.
_TITLE_BEFORE_SUBCLAUSE_RE = re.compile(r"^(.+?)\.\s+\((\d+)\)", re.DOTALL)

# CrPC-style: title ends with a period before the operative body text.
_TITLE_BEFORE_BODY_RE = re.compile(r"^(.+?)\.\s+(.+)", re.DOTALL)

_ACT_CITATION_PREFIX: dict[str, str] = {
    "Indian Penal Code": "IPC",
    "Code of Criminal Procedure": "CrPC",
    "Code of Civil Procedure": "CPC",
    "Hindu Marriage Act": "HMA",
    "Special Marriage Act": "SMA",
    "Industrial Disputes Act": "IDA",
    "Code on Wages": "COW",
    "Consumer Protection Act": "CPA",
    "Transfer of Property Act": "TPA",
}


@dataclass
class LegalChunk:
    """A single citable chunk of legal text with its source metadata."""

    domain: str
    act_name: str
    act_year: int
    chapter: str | None
    section_number: str
    section_title: str | None
    source_citation: str
    text: str


def _citation_prefix(act_name: str, act_year: int) -> str:
    abbrev = _ACT_CITATION_PREFIX.get(act_name)
    if abbrev is None:
        words = [word for word in act_name.split() if word and word[0].isupper()]
        abbrev = "".join(word[0] for word in words)
    return f"{abbrev} {act_year}"


def _build_source_citation(act_name: str, act_year: int, section_number: str) -> str:
    return f"{_citation_prefix(act_name, act_year)}, S.{section_number}"


def _extract_chapter_markers(text: str) -> list[tuple[int, str]]:
    """Return (byte-offset, chapter label) pairs in document order."""
    markers: list[tuple[int, str]] = []
    lines = text.splitlines(keepends=True)
    offset = 0

    idx = 0
    while idx < len(lines):
        line = lines[idx]
        match = CHAPTER_RE.match(line.strip())
        if match:
            label = f"CHAPTER {match.group(1).strip()}"
            line_len = len(line)
            next_idx = idx + 1
            if next_idx < len(lines):
                next_stripped = lines[next_idx].strip()
                if (
                    next_stripped
                    and next_stripped.isupper()
                    and not next_stripped.startswith(("CHAPTER", "Section"))
                    and not re.match(r"^\d+\.", next_stripped)
                    and len(next_stripped) < 80
                ):
                    label = f"{label} — {next_stripped}"
            markers.append((offset, label))
        offset += len(line)
        idx += 1

    return markers


def _chapter_at_position(markers: list[tuple[int, str]], position: int) -> str | None:
    current: str | None = None
    for marker_pos, label in markers:
        if marker_pos <= position:
            current = label
        else:
            break
    return current


def _split_title_and_body(section_body: str) -> tuple[str | None, str]:
    """Separate the section title from the operative body text."""
    if not section_body.strip():
        return None, ""

    em_dash_match = _TITLE_EM_DASH_RE.match(section_body)
    if em_dash_match:
        title = em_dash_match.group(1).strip()
        body = section_body[em_dash_match.end() :].strip()
        return title or None, body

    subclause_match = _TITLE_BEFORE_SUBCLAUSE_RE.match(section_body)
    if subclause_match:
        title = subclause_match.group(1).strip()
        body = section_body[subclause_match.start(2) - 1 :].strip()
        return title or None, body

    body_match = _TITLE_BEFORE_BODY_RE.match(section_body)
    if body_match:
        title = body_match.group(1).strip()
        body = body_match.group(2).strip()
        if title and len(title) <= 120:
            return title, body

    return None, section_body.strip()


def _split_on_subclauses(body: str, max_chars: int) -> list[str]:
    """Split an oversized section body on numbered sub-clauses when possible."""
    if len(body) <= max_chars:
        return [body]

    matches = list(SUBCLAUSE_BOUNDARY_RE.finditer(body))
    if len(matches) < 2:
        return [body]

    parts: list[str] = []
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        part = body[start:end].strip()
        if part:
            parts.append(part)

    return parts if len(parts) > 1 else [body]


def _make_chunk(
    *,
    domain: str,
    act_name: str,
    act_year: int,
    chapter: str | None,
    section_number: str,
    section_title: str | None,
    text: str,
) -> LegalChunk:
    if not section_number.strip():
        raise ValueError("section_number must not be empty")

    return LegalChunk(
        domain=domain,
        act_name=act_name,
        act_year=act_year,
        chapter=chapter,
        section_number=section_number,
        section_title=section_title,
        source_citation=_build_source_citation(act_name, act_year, section_number),
        text=text.strip(),
    )


def parse_act_text(
    raw_text: str,
    domain: str,
    act_name: str,
    act_year: int,
    *,
    max_section_chars: int = DEFAULT_MAX_SECTION_CHARS,
) -> list[LegalChunk]:
    """Parse raw act text into a list of `LegalChunk` objects.

    Expects curated bare-act text with ``Section N.`` headers (see T05–T10).
    Oversized section bodies are further split on numbered sub-clauses
    ``(1)``, ``(2)``, … when they exceed *max_section_chars*.
    """
    if not raw_text.strip():
        return []

    chapter_markers = _extract_chapter_markers(raw_text)
    matches = list(SECTION_HEADER_RE.finditer(raw_text))
    if not matches:
        return []

    chunks: list[LegalChunk] = []
    for idx, match in enumerate(matches):
        section_number = match.group(1)
        section_start = match.end()
        section_end = matches[idx + 1].start() if idx + 1 < len(matches) else len(raw_text)
        section_body = raw_text[section_start:section_end].strip()
        chapter = _chapter_at_position(chapter_markers, match.start())
        section_title, body = _split_title_and_body(section_body)

        if not body:
            continue

        body_parts = _split_on_subclauses(body, max_section_chars)
        for part in body_parts:
            if not part.strip():
                continue
            chunks.append(
                _make_chunk(
                    domain=domain,
                    act_name=act_name,
                    act_year=act_year,
                    chapter=chapter,
                    section_number=section_number,
                    section_title=section_title,
                    text=part,
                )
            )

    return chunks
