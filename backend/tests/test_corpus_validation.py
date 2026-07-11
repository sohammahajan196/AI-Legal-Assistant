"""Tests for app.rag.corpus_validation. See TASKS.md T13."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.rag.corpus_validation import (
    format_validation_report,
    validate_chunk_record,
    validate_corpus,
    validate_domain_file,
)
from app.rag.ingestion import chunk_to_record, write_jsonl
from app.rag.chunking import parse_act_text
from app.rag.corpus_curation import CRPC_SOURCE, IPC_SOURCE
from tests.test_chunking import CRPC_SECTION_154_SAMPLE, IPC_SAMPLE

BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_ROOT = BACKEND_ROOT / "data" / "processed"


def _valid_record(**overrides) -> dict:
    chunks = parse_act_text(
        IPC_SAMPLE,
        "criminal",
        IPC_SOURCE.act_name,
        IPC_SOURCE.act_year,
    )
    record = chunk_to_record(chunks[0])
    record.update(overrides)
    return record


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(record, ensure_ascii=False) for record in records]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_validate_chunk_record_accepts_valid_chunk():
    record = _valid_record()
    issues = validate_chunk_record(record, line_number=1, domain="criminal")
    assert issues == []


def test_validate_chunk_record_flags_empty_text():
    record = _valid_record(text="   ")
    issues = validate_chunk_record(record, line_number=3, domain="criminal")
    assert len(issues) == 1
    assert "empty required field: text" in issues[0].message


def test_validate_chunk_record_flags_missing_and_empty_fields():
    record = _valid_record()
    del record["section_number"]
    record["source_citation"] = ""

    issues = validate_chunk_record(record, line_number=2, domain="criminal")
    messages = [issue.message for issue in issues]
    assert any("missing metadata field(s): section_number" in message for message in messages)
    assert any("empty required field: source_citation" in message for message in messages)


def test_validate_domain_file_allows_subclause_splits(tmp_path: Path):
    chunks = parse_act_text(
        CRPC_SECTION_154_SAMPLE,
        "criminal",
        CRPC_SOURCE.act_name,
        CRPC_SOURCE.act_year,
        max_section_chars=250,
    )
    path = tmp_path / "criminal.jsonl"
    write_jsonl(path, chunks)

    result = validate_domain_file(path, "criminal")

    assert result.chunk_count == 3
    assert result.issues == ()


def test_validate_domain_file_flags_duplicate_section_number(tmp_path: Path):
    record = _valid_record()
    duplicate = dict(record)
    path = tmp_path / "criminal.jsonl"
    _write_jsonl(path, [record, duplicate])

    result = validate_domain_file(path, "criminal")

    assert result.issues
    assert any("duplicate section" in issue.message for issue in result.issues)


def test_validate_domain_file_reports_chunk_count(tmp_path: Path):
    records = [_valid_record(), _valid_record(section_number="2", source_citation="IPC 1860, S.2")]
    path = tmp_path / "criminal.jsonl"
    _write_jsonl(path, records)

    result = validate_domain_file(path, "criminal")

    assert result.chunk_count == 2
    assert result.issues == ()


def test_validate_corpus_returns_nonzero_issues_for_bad_domain_file(tmp_path: Path):
    bad_record = _valid_record(text="")
    path = tmp_path / "criminal.jsonl"
    _write_jsonl(path, [bad_record])

    report = validate_corpus(tmp_path)

    assert not report.ok
    assert report.total_issues >= 1
    assert "criminal: 1 chunks" in format_validation_report(report)


def test_format_validation_report_lists_offending_chunks(tmp_path: Path):
    path = tmp_path / "criminal.jsonl"
    _write_jsonl(path, [_valid_record(section_number="", source_citation="")])

    report = validate_corpus(tmp_path)
    rendered = format_validation_report(report)

    assert "Result: FAIL" in rendered
    assert "empty required field" in rendered
    assert "criminal [line" in rendered


def test_validate_corpus_flags_missing_domain_file(tmp_path: Path):
    report = validate_corpus(tmp_path)

    assert not report.ok
    criminal = next(result for result in report.results if result.domain == "criminal")
    assert criminal.chunk_count == 0
    assert any("missing processed corpus file" in issue.message for issue in criminal.issues)


@pytest.mark.skipif(
    not (PROCESSED_ROOT / "criminal.jsonl").exists(),
    reason="Run scripts/ingest.py to generate processed corpus",
)
def test_validate_current_processed_corpus_is_clean():
    report = validate_corpus(PROCESSED_ROOT)

    assert report.ok, format_validation_report(report)
    assert report.total_chunks > 0
    rendered = format_validation_report(report)
    assert "Result: PASS" in rendered
    for domain in ("criminal", "civil", "family", "labour", "consumer", "property"):
        assert f"{domain}:" in rendered
