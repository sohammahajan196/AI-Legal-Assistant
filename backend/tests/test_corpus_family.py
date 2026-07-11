"""Unit tests for family-domain corpus curation. See TASKS.md T07."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    HMA_SOURCE,
    SECTION_HEADER_RE,
    SMA_SOURCE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

FAMILY_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "family"

HMA_SAMPLE = """PRELIMINARY
1. Short title and extent.—(1) This Act may be called the Hindu Marriage Act, 1955.
13. Divorce.—(1) Any marriage solemnized, whether before or after the commencement of this Act,
may, on a petition presented by either the husband or the wife, be dissolved by a decree of divorce.
"""

SMA_SAMPLE = """CHAPTER I
PRELIMINARY
1. Short title, extent and commencement.―(1) This Act may be called the Special Marriage Act, 1954.
13. Void marriages.—Any marriage solemnized under this Act shall be null and void and may,
on a petition presented by either party thereto, be so declared by a decree of nullity.
"""


def test_normalize_hma_section_headers_adds_section_prefix():
    text = "13. Divorce.—(1) Any marriage solemnized"
    normalized = normalize_ipc_section_headers(text)
    assert normalized.startswith("Section 13. Divorce.—")


def test_curate_hma_sample_produces_expected_headers():
    curated = curate_act_text(HMA_SAMPLE, HMA_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title and extent.—" in curated
    assert "Section 13. Divorce.—" in curated
    assert sections == ["1", "13"]


def test_curate_sma_sample_produces_expected_headers():
    curated = curate_act_text(SMA_SAMPLE, SMA_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title, extent and commencement." in curated
    assert "Section 13. Void marriages." in curated
    assert sections == ["1", "13"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_family_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[
            (HMA_SOURCE, FAMILY_DIR / HMA_SOURCE.filename),
            (SMA_SOURCE, FAMILY_DIR / SMA_SOURCE.filename),
        ],
        domain_title="Family domain",
        task_note="T07",
    )
    assert HMA_SOURCE.pdf_url in md
    assert SMA_SOURCE.pdf_url in md
    assert HMA_SOURCE.india_code_handle_url in md
    assert SMA_SOURCE.india_code_handle_url in md
    assert "Family domain" in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (FAMILY_DIR / HMA_SOURCE.filename).exists(),
    reason="Run scripts/curate_family.py to generate hma_1955.txt",
)
def test_hma_file_has_consistent_section_headers():
    text = (FAMILY_DIR / HMA_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=25)

    assert "Section 1." in text
    assert "Section 13." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (FAMILY_DIR / SMA_SOURCE.filename).exists(),
    reason="Run scripts/curate_family.py to generate sma_1954.txt",
)
def test_sma_file_has_consistent_section_headers():
    text = (FAMILY_DIR / SMA_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=45)

    assert "Section 1." in text
    assert "Section 13." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (FAMILY_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_family.py to generate SOURCES.md",
)
def test_sources_md_documents_both_acts():
    sources = (FAMILY_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert HMA_SOURCE.filename in sources
    assert SMA_SOURCE.filename in sources
    assert HMA_SOURCE.pdf_url in sources
    assert SMA_SOURCE.pdf_url in sources
