"""Unit tests for criminal-domain corpus curation. See TASKS.md T05."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    CRPC_SOURCE,
    IPC_SOURCE,
    SECTION_HEADER_RE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

CRIMINAL_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "criminal"

IPC_SAMPLE = """CHAPTER I
INTRODUCTION
Preamble.—WHEREAS it is expedient to provide a general Penal Code for India; It is
enacted as follows:—
1. Title and extent of operation of the Code.—This Act shall be called the Indian Penal Code.
304A. Causing death by negligence.—Whoever causes the death of any person by doing any rash
or negligent act not amounting to culpable homicide, shall be punished with imprisonment.
"""

CRPC_SAMPLE = """CHAPTER I
PRELIMINARY
1. Short title extent and commencement. (1) This Act may be called the Code of Criminal Procedure, 1973.
154. Information in cognizable cases. (1) Every information relating to the commission of a cognizable offence,
if given orally to an officer in charge of a police station, shall be reduced to writing by him.
"""


def test_normalize_section_headers_adds_section_prefix():
    text = "304A. Causing death by negligence.—Whoever causes the death"
    normalized = normalize_ipc_section_headers(text)
    assert normalized.startswith("Section 304A. Causing death by negligence.—")


def test_curate_ipc_sample_produces_expected_headers():
    curated = curate_act_text(IPC_SAMPLE, IPC_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Title and extent of operation of the Code.—" in curated
    assert "Section 304A. Causing death by negligence.—" in curated
    assert sections[:2] == ["1", "304A"]


def test_curate_crpc_sample_produces_expected_headers():
    curated = curate_act_text(CRPC_SAMPLE, CRPC_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title extent and commencement. (1)" in curated
    assert "Section 154. Information in cognizable cases. (1)" in curated
    assert sections == ["1", "154"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[(IPC_SOURCE, CRIMINAL_DIR / IPC_SOURCE.filename)],
    )
    assert IPC_SOURCE.pdf_url in md
    assert IPC_SOURCE.india_code_handle_url in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (CRIMINAL_DIR / IPC_SOURCE.filename).exists(),
    reason="Run scripts/curate_criminal.py to generate ipc_1860.txt",
)
def test_ipc_file_has_consistent_section_headers():
    text = (CRIMINAL_DIR / IPC_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=400)

    assert "Section 304A." in text
    assert "Section 1." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (CRIMINAL_DIR / CRPC_SOURCE.filename).exists(),
    reason="Run scripts/curate_criminal.py to generate crpc_1973.txt",
)
def test_crpc_file_has_consistent_section_headers():
    text = (CRIMINAL_DIR / CRPC_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=400)

    assert "Section 154." in text
    assert "Section 1." in text


@pytest.mark.skipif(
    not (CRIMINAL_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_criminal.py to generate SOURCES.md",
)
def test_sources_md_documents_both_acts():
    sources = (CRIMINAL_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert IPC_SOURCE.filename in sources
    assert CRPC_SOURCE.filename in sources
    assert IPC_SOURCE.pdf_url in sources
    assert CRPC_SOURCE.pdf_url in sources
