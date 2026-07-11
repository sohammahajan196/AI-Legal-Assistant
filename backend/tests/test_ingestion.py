"""Tests for app.rag.ingestion. See TASKS.md T12."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.rag.chunking import parse_act_text
from app.rag.corpus_curation import CRPC_SOURCE, IPC_SOURCE
from app.rag.ingestion import (
    LEGAL_DOMAINS,
    REQUIRED_CHUNK_FIELDS,
    chunk_to_record,
    ingest_all,
    ingest_domain,
    write_jsonl,
)
from tests.test_chunking import CRPC_SECTION_154_SAMPLE, IPC_SAMPLE

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = BACKEND_ROOT / "data" / "raw"


def _write_fixture_corpus(raw_root: Path) -> None:
    """Populate a minimal raw corpus with one small act per domain."""
    fixtures: dict[str, dict[str, str]] = {
        "criminal": {
            IPC_SOURCE.filename: IPC_SAMPLE,
            CRPC_SOURCE.filename: CRPC_SECTION_154_SAMPLE,
        },
        "civil": {"cpc_1908.txt": IPC_SAMPLE},
        "family": {
            "hma_1955.txt": IPC_SAMPLE,
            "sma_1954.txt": IPC_SAMPLE,
        },
        "labour": {
            "ida_1947.txt": IPC_SAMPLE,
            "code_on_wages_2019.txt": IPC_SAMPLE,
        },
        "consumer": {"cpa_2019.txt": IPC_SAMPLE},
        "property": {"tpa_1882.txt": IPC_SAMPLE},
    }

    for domain, files in fixtures.items():
        domain_dir = raw_root / domain
        domain_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (domain_dir / filename).write_text(content, encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_chunk_to_record_contains_required_fields():
    chunks = parse_act_text(
        IPC_SAMPLE,
        "criminal",
        IPC_SOURCE.act_name,
        IPC_SOURCE.act_year,
    )
    record = chunk_to_record(chunks[0])

    assert set(record) == set(REQUIRED_CHUNK_FIELDS)
    assert record["section_number"]
    assert record["source_citation"]
    assert record["text"]


def test_write_jsonl_overwrites_existing_file(tmp_path: Path):
    output_path = tmp_path / "criminal.jsonl"
    output_path.write_text('{"stale": true}\n', encoding="utf-8")

    chunks = parse_act_text(
        IPC_SAMPLE,
        "criminal",
        IPC_SOURCE.act_name,
        IPC_SOURCE.act_year,
    )
    write_jsonl(output_path, chunks)

    records = _read_jsonl(output_path)
    assert len(records) == 3
    assert "stale" not in records[0]


def test_ingest_domain_writes_valid_jsonl(tmp_path: Path):
    raw_root = tmp_path / "raw"
    processed_root = tmp_path / "processed"
    _write_fixture_corpus(raw_root)

    result = ingest_domain(
        raw_root / "criminal",
        processed_root / "criminal.jsonl",
        "criminal",
    )

    assert result.chunk_count == 4
    assert result.act_chunk_counts[IPC_SOURCE.filename] == 3
    assert result.act_chunk_counts[CRPC_SOURCE.filename] == 1

    records = _read_jsonl(result.output_path)
    assert len(records) == 4
    for record in records:
        assert set(record) == set(REQUIRED_CHUNK_FIELDS)
        assert record["domain"] == "criminal"
        json.dumps(record)


def test_ingest_domain_is_idempotent(tmp_path: Path):
    raw_root = tmp_path / "raw"
    processed_root = tmp_path / "processed"
    _write_fixture_corpus(raw_root)

    ingest_domain(raw_root / "criminal", processed_root / "criminal.jsonl", "criminal")
    first_run = (processed_root / "criminal.jsonl").read_text(encoding="utf-8")

    ingest_domain(raw_root / "criminal", processed_root / "criminal.jsonl", "criminal")
    second_run = (processed_root / "criminal.jsonl").read_text(encoding="utf-8")

    assert first_run == second_run
    assert first_run.count("\n") == 4


def test_ingest_all_produces_six_domain_files(tmp_path: Path):
    raw_root = tmp_path / "raw"
    processed_root = tmp_path / "processed"
    _write_fixture_corpus(raw_root)

    results = ingest_all(raw_root, processed_root)

    assert len(results) == len(LEGAL_DOMAINS)
    assert {result.domain for result in results} == set(LEGAL_DOMAINS)

    for result in results:
        assert result.output_path.exists()
        assert result.chunk_count > 0
        records = _read_jsonl(result.output_path)
        assert len(records) == result.chunk_count


def test_ingest_domain_raises_when_act_file_missing(tmp_path: Path):
    raw_root = tmp_path / "raw" / "criminal"
    raw_root.mkdir(parents=True)
    (raw_root / IPC_SOURCE.filename).write_text(IPC_SAMPLE, encoding="utf-8")

    with pytest.raises(FileNotFoundError, match=CRPC_SOURCE.filename):
        ingest_domain(raw_root, tmp_path / "criminal.jsonl", "criminal")


def test_ingest_domain_ignores_unknown_txt_files(tmp_path: Path):
    raw_root = tmp_path / "raw" / "criminal"
    raw_root.mkdir(parents=True)
    (raw_root / IPC_SOURCE.filename).write_text(IPC_SAMPLE, encoding="utf-8")
    (raw_root / CRPC_SOURCE.filename).write_text(CRPC_SECTION_154_SAMPLE, encoding="utf-8")
    (raw_root / "mystery_act.txt").write_text("Section 1. Foo.—Bar.", encoding="utf-8")

    result = ingest_domain(raw_root, tmp_path / "criminal.jsonl", "criminal")
    assert result.chunk_count == 4


@pytest.mark.skipif(
    not all((RAW_ROOT / domain).exists() for domain in LEGAL_DOMAINS),
    reason="Raw domain folders missing",
)
def test_ingest_real_corpus_if_present(tmp_path: Path):
    """Optional integration test against the curated production corpus."""
    processed_root = tmp_path / "processed"
    results = ingest_all(RAW_ROOT, processed_root)

    assert len(results) == 6
    for result in results:
        assert result.chunk_count > 0
        records = _read_jsonl(result.output_path)
        assert records
        for record in records:
            assert record["section_number"]
            assert record["text"].strip()
