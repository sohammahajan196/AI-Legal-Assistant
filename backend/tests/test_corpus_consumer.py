"""Unit tests for consumer-domain corpus curation. See TASKS.md T09."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from app.rag.corpus_curation import (
    CPA_SOURCE,
    SECTION_HEADER_RE,
    curate_act_text,
    list_section_numbers,
    normalize_ipc_section_headers,
    render_sources_markdown,
    validate_curated_text,
)

CONSUMER_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "consumer"

CPA_SAMPLE = """CHAPTER I
PRELIMINARY
1. Short title, extent, commencement and application.—(1) This Act may be called the Consumer
Protection Act, 2019.
35. Penalties for manufacture, sale, etc., of goods or provision of services in contravention of orders of Central Authority.—Whoever manufactures for sale or stores or sells or distributes or
imports any goods in contravention of any order issued by the Central Authority shall be punished.
"""


def test_normalize_cpa_section_headers_adds_section_prefix():
    text = "35. Penalties for manufacture, sale, etc., of goods or provision of services in contravention of"
    normalized = normalize_ipc_section_headers(
        text + " orders of Central Authority.—Whoever manufactures"
    )
    assert normalized.startswith(
        "Section 35. Penalties for manufacture, sale, etc., of goods or provision of services in contravention of"
    )


def test_curate_cpa_sample_produces_expected_headers():
    curated = curate_act_text(CPA_SAMPLE, CPA_SOURCE)
    sections = list_section_numbers(curated)

    assert "Section 1. Short title, extent, commencement and application.—" in curated
    assert "Section 35. Penalties for manufacture, sale, etc., of goods or provision of services" in curated
    assert sections == ["1", "35"]


def test_validate_curated_text_rejects_empty():
    with pytest.raises(ValueError, match="empty"):
        validate_curated_text("   \n")


def test_render_sources_markdown_includes_cpa_urls_and_date():
    md = render_sources_markdown(
        retrieval_date=date(2026, 7, 11),
        acts=[(CPA_SOURCE, CONSUMER_DIR / CPA_SOURCE.filename)],
        domain_title="Consumer domain",
        task_note="T09",
    )
    assert CPA_SOURCE.pdf_url in md
    assert CPA_SOURCE.india_code_handle_url in md
    assert "Consumer domain" in md
    assert "2026-07-11" in md


@pytest.mark.skipif(
    not (CONSUMER_DIR / CPA_SOURCE.filename).exists(),
    reason="Run scripts/curate_consumer.py to generate cpa_2019.txt",
)
def test_cpa_file_has_consistent_section_headers():
    text = (CONSUMER_DIR / CPA_SOURCE.filename).read_text(encoding="utf-8")
    validate_curated_text(text, min_sections=90)

    assert "Section 1." in text
    assert "Section 35." in text
    assert SECTION_HEADER_RE.search(text) is not None


@pytest.mark.skipif(
    not (CONSUMER_DIR / "SOURCES.md").exists(),
    reason="Run scripts/curate_consumer.py to generate SOURCES.md",
)
def test_sources_md_documents_cpa_act():
    sources = (CONSUMER_DIR / "SOURCES.md").read_text(encoding="utf-8")
    assert CPA_SOURCE.filename in sources
    assert CPA_SOURCE.pdf_url in sources
    assert CPA_SOURCE.india_code_handle_url in sources
