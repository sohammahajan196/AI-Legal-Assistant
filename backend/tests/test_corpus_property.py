"""Unit tests for property-domain corpus curation. See TASKS.md T10."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    SECTION_HEADER_RE,
    TPA_SOURCE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

PROPERTY_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "property"

TPA_SAMPLE = """CHAPTER I
PRELIMINARY
Preamble.—WHEREAS it is expedient to define and amend certain parts of the law relating to the transfer of property by act of parties; It is hereby enacted as follows:—
1. Short title.—This Act may be called the Transfer of Property Act, 1882.
54. Sale how made.—1[The sale of immoveable property of the value of one hundred rupees and upwards can be made only by a registered instrument.]
106. Duration of certain leases in absence of written contract or local usage.—In the absence of a contract or local law or usage to the contrary, a lease of immoveable property for any purpose other than agriculture or manufacturing shall be deemed to be a lease from year to year.
"""


def test_normalize_tpa_section_headers_adds_section_prefix():
    text = "54. Sale how made.—1[The sale of immoveable property"
    normalized = normalize_ipc_section_headers(text)
    assert normalized.startswith("Section 54. Sale how made.—")


def test_curate_tpa_sample_produces_expected_headers():
    curated = curate_act_text(TPA_SAMPLE, TPA_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title.—" in curated
    assert "Section 54. Sale how made.—" in curated
    assert "Section 106. Duration of certain leases in absence of written contract or local usage.—" in curated
    assert sections == ["1", "54", "106"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_tpa_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[(TPA_SOURCE, PROPERTY_DIR / TPA_SOURCE.filename)],
        domain_title="Property domain",
        task_note="T10",
    )
    assert TPA_SOURCE.pdf_url in md
    assert TPA_SOURCE.india_code_handle_url in md
    assert "Property domain" in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (PROPERTY_DIR / TPA_SOURCE.filename).exists(),
    reason="Run scripts/curate_property.py to generate tpa_1882.txt",
)
def test_tpa_file_has_consistent_section_headers():
    text = (PROPERTY_DIR / TPA_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=100)

    assert "Section 1." in text
    assert "Section 54." in text
    assert "Section 106." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (PROPERTY_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_property.py to generate SOURCES.md",
)
def test_sources_md_documents_tpa_act():
    sources = (PROPERTY_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert TPA_SOURCE.filename in sources
    assert TPA_SOURCE.pdf_url in sources
    assert TPA_SOURCE.india_code_handle_url in sources
