"""Tests for app.rag.index_build and scripts/build_index.py. See TASKS.md T17."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings

from app.rag.bm25_index import BM25_INDEX_FILE
from app.rag.chunking import LegalChunk
from app.rag.index_build import IndexBuildError, build_all_indices
from app.rag.ingestion import LEGAL_DOMAINS, load_processed_chunks, record_to_chunk
from app.rag.vectorstore import FAISS_DOCSTORE_FILE, FAISS_INDEX_FILE
from tests.test_corpus_validation import _valid_record, _write_jsonl

BACKEND_ROOT = Path(__file__).resolve().parents[1]


class _TinyEmbeddings(Embeddings):
    """Fixed-dimension offline embedder for fast index-build tests."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        seed = sum(ord(char) for char in text) % 768
        vector = [0.0] * 768
        vector[seed] = 1.0
        return vector


def _load_build_index_script():
    script_path = BACKEND_ROOT / "scripts" / "build_index.py"
    spec = importlib.util.spec_from_file_location("build_index_script", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_valid_corpus(processed_root: Path, *, criminal_records: list[dict] | None = None) -> None:
    """Create minimal valid JSONL files for every configured domain."""
    for domain in LEGAL_DOMAINS:
        if domain == "criminal" and criminal_records is not None:
            records = criminal_records
        else:
            records = [
                _valid_record(
                    domain=domain,
                    act_name=f"{domain.title()} Act",
                    section_number="1",
                    source_citation=f"{domain.upper()} 1900, S.1",
                    text=f"Section 1. Sample {domain} provision.",
                )
            ]
        _write_jsonl(processed_root / f"{domain}.jsonl", records)


def test_load_processed_chunks_reads_all_domains(tmp_path: Path):
    _write_valid_corpus(tmp_path)

    chunks = load_processed_chunks(tmp_path)

    assert len(chunks) == len(LEGAL_DOMAINS)
    assert {chunk.domain for chunk in chunks} == set(LEGAL_DOMAINS)


def test_record_to_chunk_round_trip():
    record = _valid_record(section_number="304A", source_citation="IPC 1860, S.304A")
    chunk = record_to_chunk(record)

    assert isinstance(chunk, LegalChunk)
    assert chunk.section_number == "304A"
    assert chunk.source_citation == "IPC 1860, S.304A"


def test_build_all_indices_writes_faiss_and_bm25_artifacts(tmp_path: Path):
    processed_root = tmp_path / "processed"
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    _write_valid_corpus(processed_root)

    result = build_all_indices(
        processed_root,
        faiss_dir,
        bm25_dir,
        embedding_model=_TinyEmbeddings(),
    )

    assert result.chunk_count == len(LEGAL_DOMAINS)
    assert (faiss_dir / FAISS_INDEX_FILE).is_file()
    assert (faiss_dir / FAISS_DOCSTORE_FILE).is_file()
    assert (bm25_dir / BM25_INDEX_FILE).is_file()
    assert result.validation_report.ok


def test_build_all_indices_aborts_when_validation_fails(tmp_path: Path):
    processed_root = tmp_path / "processed"
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    _write_valid_corpus(
        processed_root,
        criminal_records=[_valid_record(text="")],
    )

    with pytest.raises(IndexBuildError) as exc_info:
        build_all_indices(
            processed_root,
            faiss_dir,
            bm25_dir,
            embedding_model=_TinyEmbeddings(),
        )

    assert "Result: FAIL" in str(exc_info.value)
    assert not (faiss_dir / FAISS_INDEX_FILE).exists()
    assert not (bm25_dir / BM25_INDEX_FILE).exists()


def test_build_index_script_main_success(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    processed_root = tmp_path / "processed"
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    _write_valid_corpus(processed_root)

    module = _load_build_index_script()
    monkeypatch.setattr(module, "PROCESSED_ROOT", processed_root)
    monkeypatch.setattr(module.settings, "faiss_index_dir", str(faiss_dir))
    monkeypatch.setattr(module.settings, "bm25_index_dir", str(bm25_dir))
    monkeypatch.setattr(
        "app.rag.index_build.get_embedding_model",
        lambda: _TinyEmbeddings(),
    )

    assert module.main() == 0
    assert (faiss_dir / FAISS_INDEX_FILE).is_file()
    assert (bm25_dir / BM25_INDEX_FILE).is_file()


def test_build_index_script_main_returns_nonzero_on_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    processed_root = tmp_path / "processed"
    _write_valid_corpus(
        processed_root,
        criminal_records=[_valid_record(text="")],
    )

    module = _load_build_index_script()
    monkeypatch.setattr(module, "PROCESSED_ROOT", processed_root)

    assert module.main() == 1
    captured = capsys.readouterr()
    assert "Result: FAIL" in captured.err
