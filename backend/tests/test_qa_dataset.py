"""
Unit tests for backend/eval/qa_dataset.jsonl. See TASKS.md T48.

Verifies structural acceptance criteria (30-50 entries, every domain
represented >= 4 times, required fields present) and cross-checks every
`expected_sections` entry against sections actually produced by parsing the
real curated corpus (T05-T10) through the T11 parser -- i.e. "verified by
hand against the actual curated corpus" is additionally enforced as an
automated regression check.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

from app.rag.chunking import parse_act_text
from app.rag.corpus_curation import (
    COW_SOURCE,
    CPA_SOURCE,
    CPC_SOURCE,
    CRPC_SOURCE,
    HMA_SOURCE,
    IDA_SOURCE,
    IPC_SOURCE,
    SMA_SOURCE,
    TPA_SOURCE,
)
from app.rag.ingestion import DOMAIN_ACT_SOURCES, LEGAL_DOMAINS

EVAL_DATASET_PATH = Path(__file__).resolve().parents[1] / "eval" / "qa_dataset.jsonl"
RAW_DATA_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw"

REQUIRED_FIELDS = ("question", "expected_domain", "expected_sections")

ACT_SOURCES_BY_NAME = {
    act.act_name: act
    for act in (
        IPC_SOURCE,
        CRPC_SOURCE,
        CPC_SOURCE,
        HMA_SOURCE,
        SMA_SOURCE,
        IDA_SOURCE,
        COW_SOURCE,
        CPA_SOURCE,
        TPA_SOURCE,
    )
}


def _load_dataset() -> list[dict]:
    with EVAL_DATASET_PATH.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


@pytest.fixture(scope="module")
def dataset() -> list[dict]:
    return _load_dataset()


@pytest.fixture(scope="module")
def available_sections_by_act() -> dict[str, set[str]]:
    """Map each curated act name to the set of section_numbers the real T11
    parser extracts from its raw text file, for every act across all 6
    domains (T05-T10)."""
    sections_by_act: dict[str, set[str]] = {}
    for domain, acts in DOMAIN_ACT_SOURCES.items():
        for act in acts:
            raw_path = RAW_DATA_ROOT / domain / act.filename
            raw_text = raw_path.read_text(encoding="utf-8")
            chunks = parse_act_text(raw_text, domain, act.act_name, act.act_year)
            sections_by_act[act.act_name] = {chunk.section_number for chunk in chunks}
    return sections_by_act


def test_dataset_has_between_30_and_50_entries(dataset: list[dict]):
    assert 30 <= len(dataset) <= 50


def test_every_domain_represented_at_least_four_times(dataset: list[dict]):
    counts = Counter(entry["expected_domain"] for entry in dataset)

    assert set(counts) == set(LEGAL_DOMAINS)
    for domain in LEGAL_DOMAINS:
        assert counts[domain] >= 4, f"domain {domain!r} only has {counts[domain]} entries"


def test_every_entry_has_required_fields_with_non_empty_expected_sections(
    dataset: list[dict],
):
    for entry in dataset:
        for field in REQUIRED_FIELDS:
            assert field in entry, f"entry missing {field!r}: {entry}"
        assert entry["question"].strip()
        assert entry["expected_domain"] in LEGAL_DOMAINS
        assert isinstance(entry["expected_sections"], list)
        assert len(entry["expected_sections"]) > 0


def test_every_expected_section_exists_in_the_curated_corpus(
    dataset: list[dict], available_sections_by_act: dict[str, set[str]]
):
    """Regression check for the "verified by hand against the actual curated
    corpus" acceptance criterion: every (act, section) pair referenced by the
    dataset must be a section the T11 parser actually extracts today."""
    for entry in dataset:
        act_name = entry.get("expected_act")
        assert act_name, f"entry missing expected_act for cross-check: {entry}"
        assert act_name in ACT_SOURCES_BY_NAME, f"unknown expected_act {act_name!r}"

        available = available_sections_by_act[act_name]
        for section in entry["expected_sections"]:
            assert section in available, (
                f"expected_sections entry {section!r} for act {act_name!r} "
                f"not found by the T11 parser (question: {entry['question']!r})"
            )
