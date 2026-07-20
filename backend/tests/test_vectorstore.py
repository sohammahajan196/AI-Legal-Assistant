"""Unit tests for app.rag.vectorstore. See TASKS.md T15."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings

from app.rag.chunking import LegalChunk
from app.rag.exceptions import RetrievalIndexNotFoundError
from app.rag.vectorstore import (
    FAISS_DOCSTORE_FILE,
    FAISS_INDEX_FILE,
    FaissQueryResult,
    build_faiss_index,
    chunk_to_document,
    load_faiss_index,
    query_faiss_index,
)


class KeywordEmbeddings(Embeddings):
    """Deterministic offline embedder keyed on legal tokens (no network)."""

    KEYWORD_DIMS = {
        "304a": 0,
        "negligence": 1,
        "154": 2,
        "cognizable": 3,
        "property": 4,
        "transfer": 5,
    }
    SIZE = 768

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * self.SIZE
        lower = text.lower()
        for keyword, dim in self.KEYWORD_DIMS.items():
            if keyword in lower:
                vec[dim] = 1.0

        norm = math.sqrt(sum(value * value for value in vec))
        if norm == 0:
            vec[0] = 1.0
            return vec
        return [value / norm for value in vec]


@pytest.fixture
def embedding_model() -> KeywordEmbeddings:
    return KeywordEmbeddings()


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


def test_chunk_to_document_preserves_citation_metadata(fixture_chunks: list[LegalChunk]):
    document = chunk_to_document(fixture_chunks[0])

    assert "Section 304A." in document.page_content
    assert "IPC 1860, S.304A" in document.page_content
    assert fixture_chunks[0].text in document.page_content
    assert document.metadata["domain"] == "criminal"
    assert document.metadata["section_number"] == "304A"
    assert document.metadata["source_citation"] == "IPC 1860, S.304A"


def test_build_faiss_index_writes_persisted_artifacts(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
    embedding_model: KeywordEmbeddings,
):
    persist_dir = tmp_path / "faiss_index"

    build_faiss_index(fixture_chunks, embedding_model, str(persist_dir))

    assert (persist_dir / FAISS_INDEX_FILE).is_file()
    assert (persist_dir / FAISS_DOCSTORE_FILE).is_file()


def test_build_faiss_index_rejects_empty_chunk_list(
    tmp_path: Path,
    embedding_model: KeywordEmbeddings,
):
    with pytest.raises(ValueError, match="empty chunk list"):
        build_faiss_index([], embedding_model, str(tmp_path / "faiss_index"))


def test_load_and_query_returns_matching_section(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
    embedding_model: KeywordEmbeddings,
):
    persist_dir = tmp_path / "faiss_index"
    build_faiss_index(fixture_chunks, embedding_model, str(persist_dir))

    index = load_faiss_index(str(persist_dir), embedding_model)
    results = query_faiss_index(
        index,
        "What is Section 304A punishment for death by negligence?",
        k=3,
    )

    assert results
    assert results[0].section_number == "304A"
    assert results[0].domain == "criminal"
    assert "negligence" in results[0].text.lower()


def test_query_with_domain_filter_excludes_other_domains(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
    embedding_model: KeywordEmbeddings,
):
    persist_dir = tmp_path / "faiss_index"
    build_faiss_index(fixture_chunks, embedding_model, str(persist_dir))
    index = load_faiss_index(str(persist_dir), embedding_model)

    property_results = query_faiss_index(
        index,
        "transfer of property ownership sale",
        k=5,
        domain="property",
    )
    criminal_results = query_faiss_index(
        index,
        "Section 154 cognizable offence information",
        k=5,
        domain="criminal",
    )

    assert property_results
    assert all(result.domain == "property" for result in property_results)
    assert property_results[0].section_number == "54"

    assert criminal_results
    assert all(result.domain == "criminal" for result in criminal_results)
    assert criminal_results[0].section_number == "154"


def test_load_faiss_index_missing_dir_raises(
    tmp_path: Path,
    embedding_model: KeywordEmbeddings,
):
    with pytest.raises(RetrievalIndexNotFoundError, match="FAISS index not found") as exc_info:
        load_faiss_index(str(tmp_path / "missing"), embedding_model)

    assert "build_index.py" in str(exc_info.value)
    assert isinstance(exc_info.value, FileNotFoundError)


def test_query_faiss_index_rejects_invalid_k(
    tmp_path: Path,
    fixture_chunks: list[LegalChunk],
    embedding_model: KeywordEmbeddings,
):
    persist_dir = tmp_path / "faiss_index"
    build_faiss_index(fixture_chunks, embedding_model, str(persist_dir))
    index = load_faiss_index(str(persist_dir), embedding_model)

    with pytest.raises(ValueError, match="k must be at least 1"):
        query_faiss_index(index, "test query", k=0)


def test_faiss_query_result_round_trip_from_document(fixture_chunks: list[LegalChunk]):
    document = chunk_to_document(fixture_chunks[1])
    result = FaissQueryResult.from_document(document, score=0.42)

    assert result.section_number == "154"
    assert result.domain == "criminal"
    assert result.chapter == "CHAPTER XII"
    assert result.score == 0.42
