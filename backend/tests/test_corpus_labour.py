"""Unit tests for labour-domain corpus curation. See TASKS.md T08."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    COW_SOURCE,
    IDA_SOURCE,
    SECTION_HEADER_RE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

LABOUR_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "labour"

IDA_SAMPLE = """CHAPTER I
PRELIMINARY
1. Short title, extent and commencement.—(1) This Act may be called the Industrial Disputes Act, 1947.
2A. Dismissal, etc., of an individual workman to be deemed to be an industrial dispute.—Where any employer
discharges, dismisses, retrenches, or otherwise terminates the services of an individual workman.
10. Voluntary reference of disputes to arbitration.—Where any industrial dispute exists or is apprehended,
the employer and the workmen may agree to refer the dispute to arbitration.
"""

COW_SAMPLE = """CHAPTER I
PRELIMINARY
1. Short title, extent and commencement.—(1) This Act may be called the Code on Wages, 2019.
9. Power of Central Government to fix floor wage.—(1) The Central Government may, by notification,
fix the floor wage for the whole of India.
"""


def test_normalize_ida_section_headers_adds_section_prefix():
    text = "10. Voluntary reference of disputes to arbitration.—Where any industrial dispute"
    normalized = normalize_ipc_section_headers(text)
    assert normalized.startswith("Section 10. Voluntary reference of disputes to arbitration.—")


def test_curate_ida_sample_produces_expected_headers():
    curated = curate_act_text(IDA_SAMPLE, IDA_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title, extent and commencement.—" in curated
    assert "Section 2A. Dismissal, etc., of an individual workman to be deemed to be an industrial dispute.—" in curated
    assert "Section 10. Voluntary reference of disputes to arbitration.—" in curated
    assert sections == ["1", "2A", "10"]


def test_curate_cow_sample_produces_expected_headers():
    curated = curate_act_text(COW_SAMPLE, COW_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title, extent and commencement.—" in curated
    assert "Section 9. Power of Central Government to fix floor wage.—" in curated
    assert sections == ["1", "9"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_labour_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[
            (IDA_SOURCE, LABOUR_DIR / IDA_SOURCE.filename),
            (COW_SOURCE, LABOUR_DIR / COW_SOURCE.filename),
        ],
        domain_title="Labour domain",
        task_note="T08",
    )
    assert IDA_SOURCE.pdf_url in md
    assert COW_SOURCE.pdf_url in md
    assert IDA_SOURCE.india_code_handle_url in md
    assert COW_SOURCE.india_code_handle_url in md
    assert "Labour domain" in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (LABOUR_DIR / IDA_SOURCE.filename).exists(),
    reason="Run scripts/curate_labour.py to generate ida_1947.txt",
)
def test_ida_file_has_consistent_section_headers():
    text = (LABOUR_DIR / IDA_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=70)

    assert "Section 1." in text
    assert "Section 10." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (LABOUR_DIR / COW_SOURCE.filename).exists(),
    reason="Run scripts/curate_labour.py to generate code_on_wages_2019.txt",
)
def test_cow_file_has_consistent_section_headers():
    text = (LABOUR_DIR / COW_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=50)

    assert "Section 1." in text
    assert "Section 9." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (LABOUR_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_labour.py to generate SOURCES.md",
)
def test_sources_md_documents_both_acts():
    sources = (LABOUR_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert IDA_SOURCE.filename in sources
    assert COW_SOURCE.filename in sources
    assert IDA_SOURCE.pdf_url in sources
    assert COW_SOURCE.pdf_url in sources
