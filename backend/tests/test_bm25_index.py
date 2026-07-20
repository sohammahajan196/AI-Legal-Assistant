"""Unit tests for app.rag.bm25_index. See TASKS.md T16."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.rag.bm25_index import (
    BM25_INDEX_FILE,
    Bm25QueryResult,
    build_bm25_index,
    load_bm25_index,
    query_bm25_index,
)
from app.rag.chunking import LegalChunk
from app.rag.exceptions import RetrievalIndexNotFoundError


@pytest.fixture
def fixture_chunks() -> list[LegalChunk]:
    return [
        LegalChunk(
            domain="criminal",
            act_name="Indian Penal Code",
            act_year=1860,
            chapter="CHAPTER XVI",
            section_number="304A",
            section_title="Causing death by negligence",
            source_citation="IPC 1860, S.304A",
            text=(
                "Section 304A. Causing death by negligence.—Whoever causes the death of any "
                "person by doing any rash or negligent act not amounting to culpable homicide, "
                "shall be punished with imprisonment."
            ),
        ),
        LegalChunk(
            domain="criminal",
            act_name="Code of Criminal Procedure",
            act_year=1973,
            chapter="CHAPTER XII",
            section_number="154",
            section_title="Information in cognizable cases",
            source_citation="CrPC 1973, S.154",
            text=(
                "Section 154. Information in cognizable cases. (1) Every information relating "
                "to the commission of a cognizable offence shall be reduced to writing."
            ),
        ),
        LegalChunk(
            domain="property",
            act_name="Transfer of Property Act",
            act_year=1882,
            chapter="CHAPTER II",
            section_number="54",
            section_title="Sale how made",
            source_citation="TPA 1882, S.54",
            text=(
                "Section 54. Sale how made.—'Sale' is a transfer of ownership in exchange "
                "for a price paid or promised or part-paid and part-promised."
            ),
        ),
    ]


def test_build_bm25_index_writes_persisted_artifact(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
):
    persist_dir = tmp_path / "bm25_index"

    build_bm25_index(fixture_chunks, str(persist_dir))

    assert (persist_dir / BM25_INDEX_FILE).is_file()


def test_build_bm25_index_rejects_empty_chunk_list(tmp_path: Path):
    with pytest.raises(ValueError, match="empty chunk list"):
        build_bm25_index([], str(tmp_path / "bm25_index"))


def test_query_section_number_returns_matching_chunk(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
):
    persist_dir = tmp_path / "bm25_index"
    build_bm25_index(fixture_chunks, str(persist_dir))
    index = load_bm25_index(str(persist_dir))

    results = query_bm25_index(index, "304A", k=3)

    assert results
    assert results[0].section_number == "304A"
    assert results[0].domain == "criminal"
    assert "304A" in results[0].text


def test_load_and_query_without_rebuilding(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
):
    persist_dir = tmp_path / "bm25_index"
    build_bm25_index(fixture_chunks, str(persist_dir))

    reloaded = load_bm25_index(str(persist_dir))
    results = query_bm25_index(reloaded, "Section 154 cognizable", k=3)

    assert results
    assert results[0].section_number == "154"
    assert "cognizable" in results[0].text.lower()


def test_query_with_domain_filter_excludes_other_domains(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
):
    persist_dir = tmp_path / "bm25_index"
    build_bm25_index(fixture_chunks, str(persist_dir))
    index = load_bm25_index(str(persist_dir))

    property_results = query_bm25_index(index, "Section 54 transfer sale", k=5, domain="property")
    criminal_results = query_bm25_index(index, "Section 154 cognizable", k=5, domain="criminal")

    assert property_results
    assert all(result.domain == "property" for result in property_results)
    assert property_results[0].section_number == "54"

    assert criminal_results
    assert all(result.domain == "criminal" for result in criminal_results)
    assert criminal_results[0].section_number == "154"


def test_load_bm25_index_missing_file_raises(
    tmp_path: Path,
):
    with pytest.raises(RetrievalIndexNotFoundError, match="BM25 index not found") as exc_info:
        load_bm25_index(str(tmp_path / "missing"))

    assert "build_index.py" in str(exc_info.value)
    assert isinstance(exc_info.value, FileNotFoundError)


def test_query_bm25_index_rejects_invalid_k(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
):
    persist_dir = tmp_path / "bm25_index"
    build_bm25_index(fixture_chunks, str(persist_dir))
    index = load_bm25_index(str(persist_dir))

    with pytest.raises(ValueError, match="k must be at least 1"):
        query_bm25_index(index, "304A", k=0)


def test_bm25_query_result_round_trip_from_document(fixture_chunks: list[LegalChunk]):
    from app.rag.vectorstore import chunk_to_document

    document = chunk_to_document(fixture_chunks[0])
    result = Bm25QueryResult.from_document(document, rank=0)

    assert result.section_number == "304A"
    assert result.domain == "criminal"
    assert result.score == 1.0
