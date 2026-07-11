"""Tests for app.rag.chunking. See TASKS.md T11."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.rag.chunking import DEFAULT_MAX_SECTION_CHARS, LegalChunk, parse_act_text
from app.rag.corpus_curation import CRPC_SOURCE, IPC_SOURCE, curate_act_text

CRIMINAL_DIR = Path(__file__).resolve().parents[1] / "data" / "raw" / "criminal"

IPC_SAMPLE = """CHAPTER I
INTRODUCTION
Preamble.—WHEREAS it is expedient to provide a general Penal Code for India; It is
enacted as follows:—
Section 1. Title and extent of operation of the Code.—This Act shall be called the Indian Penal Code, and
shall extend to the whole of India.
Section 2. Punishment of offences committed within India.—Every person shall be liable to punishment
under this Code and not otherwise for every act or omission contrary to the provisions thereof.
Section 304A. Causing death by negligence.—Whoever causes the death of any person by doing any rash
or negligent act not amounting to culpable homicide, shall be punished with imprisonment of either
description for a term which may extend to two years, or with fine, or with both.
"""

CRPC_SECTION_154_SAMPLE = """CHAPTER XII
GENERAL PROVISIONS AS TO INQUIRIES AND TRIALS
Section 154. Information in cognizable cases. (1) Every information relating to the commission of a cognizable offence,
if given orally to an officer in charge of a police station, shall be reduced to writing by him or under his direction,
and be read over to the informant; and every such information, whether given in writing or reduced to writing as aforesaid,
shall be signed by the person giving it, and the substance thereof shall be entered in a book to be kept by such officer.
(2) A copy of the information as recorded under sub-section (1) shall be given forthwith, free of cost, to the informant.
(3) Any person aggrieved by a refusal on the part of an officer in charge of a police station to record the information
referred to in subsection (1) may send the substance of such information, in writing and by post, to the Superintendent
of Police concerned who, if satisfied that such information discloses the commission of a cognizable offence, shall
either investigate the case himself or direct an investigation to be made by any police officer subordinate to him.
"""

LONG_SECTION_SAMPLE = """CHAPTER I
PRELIMINARY
Section 99. Long procedural section. (1) Alpha text that is intentionally verbose so this subsection exceeds the configured
threshold for sub-clause splitting during unit tests and must therefore stand alone as its own chunk in the parser output.
(2) Beta text continues with additional procedural detail that should also become a separate chunk once the threshold is low.
(3) Gamma text completes the section with a third numbered sub-clause for deterministic chunk-count assertions.
"""


def _assert_chunk_metadata(chunk: LegalChunk) -> None:
    assert chunk.domain
    assert chunk.act_name
    assert chunk.act_year
    assert chunk.section_number
    assert chunk.source_citation
    assert chunk.text
    assert f"S.{chunk.section_number}" in chunk.source_citation


def test_parse_ipc_sample_extracts_expected_sections():
    chunks = parse_act_text(
        IPC_SAMPLE,
        domain="criminal",
        act_name=IPC_SOURCE.act_name,
        act_year=IPC_SOURCE.act_year,
    )

    assert len(chunks) == 3
    numbers = [chunk.section_number for chunk in chunks]
    assert numbers == ["1", "2", "304A"]

    section_304a = chunks[-1]
    assert section_304a.section_title == "Causing death by negligence"
    assert section_304a.source_citation == "IPC 1860, S.304A"
    assert section_304a.chapter == "CHAPTER I — INTRODUCTION"
    assert "rash" in section_304a.text
    assert "negligent act" in section_304a.text

    for chunk in chunks:
        _assert_chunk_metadata(chunk)


def test_parse_crpc_section_splits_on_subclauses_when_long():
    chunks = parse_act_text(
        CRPC_SECTION_154_SAMPLE,
        domain="criminal",
        act_name=CRPC_SOURCE.act_name,
        act_year=CRPC_SOURCE.act_year,
        max_section_chars=250,
    )

    assert len(chunks) == 3
    assert all(chunk.section_number == "154" for chunk in chunks)
    assert chunks[0].section_title == "Information in cognizable cases"
    assert chunks[0].text.startswith("(1)")
    assert chunks[1].text.startswith("(2)")
    assert chunks[2].text.startswith("(3)")
    assert all(chunk.source_citation == "CrPC 1973, S.154" for chunk in chunks)


def test_short_section_is_not_split_even_with_low_threshold():
    chunks = parse_act_text(
        IPC_SAMPLE,
        domain="criminal",
        act_name=IPC_SOURCE.act_name,
        act_year=IPC_SOURCE.act_year,
        max_section_chars=50,
    )

    section_2_chunks = [chunk for chunk in chunks if chunk.section_number == "2"]
    assert len(section_2_chunks) == 1


def test_long_section_splits_only_when_threshold_exceeded():
    chunks_default = parse_act_text(
        LONG_SECTION_SAMPLE,
        domain="criminal",
        act_name=CRPC_SOURCE.act_name,
        act_year=CRPC_SOURCE.act_year,
        max_section_chars=DEFAULT_MAX_SECTION_CHARS,
    )
    chunks_split = parse_act_text(
        LONG_SECTION_SAMPLE,
        domain="criminal",
        act_name=CRPC_SOURCE.act_name,
        act_year=CRPC_SOURCE.act_year,
        max_section_chars=120,
    )

    assert len(chunks_default) == 1
    assert len(chunks_split) == 3
    assert chunks_split[0].text.startswith("(1)")
    assert chunks_split[1].text.startswith("(2)")
    assert chunks_split[2].text.startswith("(3)")


def test_parse_empty_text_returns_empty_list():
    assert parse_act_text("", "criminal", IPC_SOURCE.act_name, IPC_SOURCE.act_year) == []


def test_parse_text_without_section_headers_returns_empty_list():
    text = "CHAPTER I\nINTRODUCTION\nPreamble only, no sections."
    assert parse_act_text(text, "criminal", IPC_SOURCE.act_name, IPC_SOURCE.act_year) == []


@pytest.mark.skipif(
    not (CRIMINAL_DIR / IPC_SOURCE.filename).exists(),
    reason="Run scripts/curate_criminal.py to generate ipc_1860.txt",
)
def test_parse_curated_ipc_file_produces_many_valid_chunks():
    raw = (CRIMINAL_DIR / IPC_SOURCE.filename).read_text(encoding="utf-8")
    chunks = parse_act_text(
        raw,
        domain="criminal",
        act_name=IPC_SOURCE.act_name,
        act_year=IPC_SOURCE.act_year,
    )

    assert len(chunks) >= 400
    numbers = {chunk.section_number for chunk in chunks}
    assert "304A" in numbers
    assert "1" in numbers

    for chunk in chunks:
        _assert_chunk_metadata(chunk)


@pytest.mark.skipif(
    not (CRIMINAL_DIR / CRPC_SOURCE.filename).exists(),
    reason="Run scripts/curate_criminal.py to generate crpc_1973.txt",
)
def test_parse_curated_crpc_file_includes_section_154():
    raw = (CRIMINAL_DIR / CRPC_SOURCE.filename).read_text(encoding="utf-8")
    chunks = parse_act_text(
        raw,
        domain="criminal",
        act_name=CRPC_SOURCE.act_name,
        act_year=CRPC_SOURCE.act_year,
    )

    section_154 = [chunk for chunk in chunks if chunk.section_number == "154"]
    assert section_154
    assert section_154[0].section_title == "Information in cognizable cases"
    assert section_154[0].source_citation == "CrPC 1973, S.154"


def test_curated_ipc_sample_end_to_end_via_curation_helper():
    """Parser works on output from the T05 curation normalizer."""
    curated = curate_act_text(
        """CHAPTER I
INTRODUCTION
Preamble.—WHEREAS it is expedient to provide a general Penal Code for India; It is
enacted as follows:—
1. Title and extent of operation of the Code.—This Act shall be called the Indian Penal Code.
304A. Causing death by negligence.—Whoever causes the death of any person by doing any rash act.
""",
        IPC_SOURCE,
    )
    chunks = parse_act_text(
        curated,
        domain="criminal",
        act_name=IPC_SOURCE.act_name,
        act_year=IPC_SOURCE.act_year,
    )

    assert [chunk.section_number for chunk in chunks] == ["1", "304A"]
