"""Unit tests for civil-domain corpus curation. See TASKS.md T06."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    CPC_SOURCE,
    SECTION_HEADER_RE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

CIVIL_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "civil"

CPC_SAMPLE = """PRELIMINARY
1. Short title, commencement and extent.—(1) This Act may be cited as the Code of Civil
Procedure, 1908.
9. Courts to try all civil suits unless barred.—The Courts shall (subject to the provisions herein
contained) have jurisdiction to try all suits of a civil nature.
"""


def test_normalize_cpc_section_headers_adds_section_prefix():
    text = "9. Courts to try all civil suits unless barred.—The Courts shall"
    normalized = normalize_ipc_section_headers(text)
    assert normalized.startswith("Section 9. Courts to try all civil suits unless barred.—")


def test_curate_cpc_sample_produces_expected_headers():
    curated = curate_act_text(CPC_SAMPLE, CPC_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title, commencement and extent.—" in curated
    assert "Section 9. Courts to try all civil suits unless barred.—" in curated
    assert sections == ["1", "9"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_cpc_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[(CPC_SOURCE, CIVIL_DIR / CPC_SOURCE.filename)],
        domain_title="Civil domain",
        task_note="T06",
    )
    assert CPC_SOURCE.pdf_url in md
    assert CPC_SOURCE.india_code_handle_url in md
    assert "Civil domain" in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (CIVIL_DIR / CPC_SOURCE.filename).exists(),
    reason="Run scripts/curate_civil.py to generate cpc_1908.txt",
)
def test_cpc_file_has_consistent_section_headers():
    text = (CIVIL_DIR / CPC_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=100)

    assert "Section 1." in text
    assert "Section 9." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (CIVIL_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_civil.py to generate SOURCES.md",
)
def test_sources_md_documents_cpc_act():
    sources = (CIVIL_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert CPC_SOURCE.filename in sources
    assert CPC_SOURCE.pdf_url in sources
    assert CPC_SOURCE.india_code_handle_url in sources
