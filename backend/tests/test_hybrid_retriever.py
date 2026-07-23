"""Unit tests for app.rag.hybrid_retriever. See TASKS.md T18."""

from __future__ import annotations

import math
from pathlib import Path

import pytest
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.embeddings import Embeddings

from app.rag.bm25_index import build_bm25_index, load_bm25_index
from app.rag.chunking import LegalChunk
from app.rag.hybrid_retriever import (
    HYBRID_ID_KEY,
    build_hybrid_retriever,
    normalize_scores,
    query_hybrid_index,
)
from app.rag.vectorstore import build_faiss_index, load_faiss_index


class SynonymAwareEmbeddings(Embeddings):
    """Deterministic offline embedder that treats chosen synonyms as identical.

    Maps "negligent"/"careless" and "death"/"killing" to the same axes so a
    lexically-disjoint paraphrase query still scores as semantically similar
    to Section 304A - without any real model download or network call.
    """

    SYNONYM_DIMS = {
        "negligent": 0,
        "negligence": 0,
        "careless": 0,
        "cognizable": 1,
        "sale": 2,
        "transfer": 2,
    }
    SIZE = 16

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * self.SIZE
        lower = text.lower()
        for keyword, dim in self.SYNONYM_DIMS.items():
            if keyword in lower:
                vec[dim] = 1.0

        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            vec[-1] = 1.0
            return vec
        return [v / norm for v in vec]


@pytest.fixture
def embedding_model() -> SynonymAwareEmbeddings:
    return SynonymAwareEmbeddings()


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


@pytest.fixture
def built_indices(tmp_path: Path, fixture_chunks: list[LegalChunk], embedding_model: SynonymAwareEmbeddings):
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    build_faiss_index(fixture_chunks, embedding_model, str(faiss_dir))
    build_bm25_index(fixture_chunks, str(bm25_dir))

    faiss_index = load_faiss_index(str(faiss_dir), embedding_model)
    bm25_index = load_bm25_index(str(bm25_dir))
    return faiss_index, bm25_index


# --- normalize_scores -------------------------------------------------------


def test_normalize_scores_empty_list_returns_empty():
    assert normalize_scores([]) == []


def test_normalize_scores_scales_range_to_unit_interval():
    result = normalize_scores([1.0, 2.0, 3.0, 4.0])

    assert result[0] == pytest.approx(0.0)
    assert result[-1] == pytest.approx(1.0)
    assert all(0.0 <= value <= 1.0 for value in result)
    assert result == sorted(result)


def test_normalize_scores_handles_negative_and_positive_range():
    result = normalize_scores([-5.0, 0.0, 5.0])

    assert result == pytest.approx([0.0, 0.5, 1.0])


def test_normalize_scores_all_equal_values_returns_ones():
    result = normalize_scores([0.42, 0.42, 0.42])

    assert result == [1.0, 1.0, 1.0]


# --- build_hybrid_retriever --------------------------------------------------


def test_build_hybrid_retriever_returns_ensemble_retriever(built_indices):
    faiss_index, bm25_index = built_indices

    retriever = build_hybrid_retriever(
        faiss_index.as_retriever(search_kwargs={"k": 3}),
        bm25_index,
    )

    assert isinstance(retriever, EnsembleRetriever)
    assert retriever.id_key == HYBRID_ID_KEY


def test_build_hybrid_retriever_fused_topk_contains_both_semantic_and_keyword_matches(
    built_indices,
):
    faiss_index, bm25_index = built_indices
    bm25_index.k = 3

    retriever = build_hybrid_retriever(
        faiss_index.as_retriever(search_kwargs={"k": 3}),
        bm25_index,
    )

    # "careless ... demise" has no lexical overlap with the 304A chunk's
    # exact wording (only the semantic leg can find it), while "154" is an
    # exact keyword only BM25 will surface.
    docs = retriever.invoke("careless conduct leading to someone's demise, also see 154")
    citations = {doc.metadata["source_citation"] for doc in docs}

    assert "IPC 1860, S.304A" in citations
    assert "CrPC 1973, S.154" in citations


def test_build_hybrid_retriever_rejects_wrong_weight_count(built_indices):
    faiss_index, bm25_index = built_indices

    with pytest.raises(ValueError, match="exactly two values"):
        build_hybrid_retriever(
            faiss_index.as_retriever(),
            bm25_index,
            weights=(0.3, 0.3, 0.4),
        )


# --- query_hybrid_index -------------------------------------------------------


def test_query_hybrid_index_fused_results_contain_both_matches(built_indices):
    faiss_index, bm25_index = built_indices

    results = query_hybrid_index(
        faiss_index,
        bm25_index,
        "careless conduct leading to someone's demise, also see 154",
        k=3,
    )
    citations = {result.source_citation for result in results}

    assert "IPC 1860, S.304A" in citations
    assert "CrPC 1973, S.154" in citations


def test_query_hybrid_index_scores_are_normalized(built_indices):
    faiss_index, bm25_index = built_indices

    results = query_hybrid_index(
        faiss_index,
        bm25_index,
        "careless conduct leading to someone's demise, also see 154",
        k=3,
    )

    assert results
    assert all(0.0 <= result.score <= 1.0 for result in results)
    assert results == sorted(results, key=lambda r: r.score, reverse=True)


def test_query_hybrid_index_domain_filter_excludes_other_domains(built_indices):
    faiss_index, bm25_index = built_indices

    results = query_hybrid_index(
        faiss_index,
        bm25_index,
        "sale transfer of property ownership",
        k=5,
        domain="property",
    )

    assert results
    assert all(result.domain == "property" for result in results)
    assert results[0].section_number == "54"


def test_query_hybrid_index_weights_shift_top_result(built_indices):
    faiss_index, bm25_index = built_indices
    query = "careless conduct leading to someone's demise, also see 154"

    keyword_heavy = query_hybrid_index(
        faiss_index, bm25_index, query, k=1, weights=(0.01, 0.99)
    )
    semantic_heavy = query_hybrid_index(
        faiss_index, bm25_index, query, k=1, weights=(0.99, 0.01)
    )

    assert keyword_heavy[0].section_number == "154"
    assert semantic_heavy[0].section_number == "304A"


def test_query_hybrid_index_rejects_invalid_k(built_indices):
    faiss_index, bm25_index = built_indices

    with pytest.raises(ValueError, match="k must be at least 1"):
        query_hybrid_index(faiss_index, bm25_index, "any query", k=0)


def test_query_hybrid_index_explicit_section_ref_ranks_exact_match_first(built_indices):
    faiss_index, bm25_index = built_indices

    results = query_hybrid_index(
        faiss_index,
        bm25_index,
        "What is Section 304A of the Indian Penal Code?",
        k=3,
    )

    assert results
    assert results[0].section_number == "304A"
    assert results[0].source_citation == "IPC 1860, S.304A"


def test_extract_section_refs_from_natural_language_query():
    from app.rag.hybrid_retriever import extract_section_refs

    assert extract_section_refs("What is Section 304A of the Indian Penal Code?") == {"304A"}
    assert extract_section_refs("see S.154 and Sec. 220") == {"154", "220"}
    assert extract_section_refs("careless conduct, also see 154") == set()
