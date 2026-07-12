"""Integration tests for hybrid retrieval using a fixture corpus. See TASKS.md T20.

Builds a small (12-chunk, 3-domain) fixture corpus and a fixed query set
deliberately split into two halves:

- "keyword-favorable" queries embed an exact section number (a strong BM25
  signal) alongside wording that semantically points at a *different* chunk
  (a deliberate decoy for the fake embedder below) - the semantic-only leg
  is expected to be fooled, keyword-only is expected to succeed.
- "semantic-favorable" queries are lexically-disjoint paraphrases of the
  target chunk's concept with no section number and minimal literal overlap
  - keyword-only is expected to struggle, semantic-only is expected to
  succeed via the shared synonym dimensions.

Hybrid (RRF-fused) retrieval should recover the correct chunk for *both*
query types, since it only needs one leg to rank the right document highly.
This directly exercises T18 (app.rag.hybrid_retriever) and T19
(app.rag.reranker is intentionally untouched here - reranking is scored
separately in test_reranker.py) against fixture FAISS+BM25 indices built
entirely in a temp dir, with no dependency on the real corpus/models.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from langchain_core.embeddings import Embeddings

from app.rag.bm25_index import build_bm25_index, load_bm25_index, query_bm25_index
from app.rag.chunking import LegalChunk
from app.rag.hybrid_retriever import query_hybrid_index
from app.rag.vectorstore import build_faiss_index, load_faiss_index, query_faiss_index


class FixtureConceptEmbeddings(Embeddings):
    """Deterministic offline embedder mapping curated legal concepts to axes.

    Each of the 12 fixture chunks owns exactly one dimension. A chunk's own
    body text contains only its dimension's "canonical" phrasing; queries use
    either that chunk's "alternate" (paraphrase) phrasing to test the
    semantic leg in isolation, or another chunk's phrasing as a deliberate
    decoy to test that the semantic leg *fails* without keyword help. No
    network/model download is involved.
    """

    # dim -> phrases that trigger it (both "canonical", used in fixture chunk
    # bodies, and "alternate", used only in test queries as paraphrases).
    CONCEPT_DIMS: dict[str, int] = {
        # 0 - theft (IPC 378)
        "movable property": 0,
        "without that person's consent": 0,
        "secretly took away": 0,
        "without asking permission": 0,
        # 1 - cheating (IPC 415)
        "deceiving any person": 1,
        "fraudulently induces": 1,
        "told lies to trick": 1,
        "handed over their belongings": 1,
        # 2 - criminal trespass (IPC 441)
        "enters into or upon property": 2,
        "intent to commit an offence": 2,
        "unlawfully entered": 2,
        "sneaked onto the land": 2,
        # 3 - hurt by dangerous means (IPC 324)
        "shooting, stabbing or cutting": 3,
        "voluntarily causes hurt": 3,
        "attacked with a knife": 3,
        "injured using a weapon": 3,
        # 4 - sale (TPA 54)
        "transfer of ownership": 4,
        "price paid or promised": 4,
        # 5 - mortgage (TPA 58)
        "interest in specific immovable property": 5,
        "securing the payment of money advanced": 5,
        "using my house as collateral": 5,
        "loan secured against property": 5,
        # 6 - lease (TPA 105)
        "right to enjoy such property": 6,
        "for a certain time": 6,
        # 7 - gift (TPA 122)
        "voluntarily and without consideration": 7,
        # 8 - deficiency of service (CPA 17)
        "fault, imperfection, shortcoming or inadequacy": 8,
        "quality of service": 8,
        # 9 - unfair trade practice (CPA 47)
        "unfair method or deceptive practice": 9,
        "promoting the sale": 9,
        "misleading advertisement": 9,
        "deceptive marketing tactics": 9,
        # 10 - consumer complaint filing (CPA 35)
        "filed with the district commission": 10,
        "lodge a consumer complaint": 10,
        # 11 - class action complaints (CPA 83)
        "numerous consumers having the same interest": 11,
        "group of affected buyers filing together": 11,
        "many customers with a common grievance": 11,
    }
    SIZE = 12

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * self.SIZE
        lower = text.lower()
        for phrase, dim in self.CONCEPT_DIMS.items():
            if phrase in lower:
                vec[dim] = 1.0

        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]


@pytest.fixture
def embedding_model() -> FixtureConceptEmbeddings:
    return FixtureConceptEmbeddings()


@pytest.fixture
def fixture_chunks() -> list[LegalChunk]:
    return [
        LegalChunk(
            domain="criminal",
            act_name="Indian Penal Code",
            act_year=1860,
            chapter="CHAPTER XVII",
            section_number="378",
            section_title="Theft",
            source_citation="IPC 1860, S.378",
            text=(
                "Whoever, intending to take dishonestly any movable property out of the "
                "possession of any person without that person's consent, moves that "
                "property in order to such taking, is said to commit theft."
            ),
        ),
        LegalChunk(
            domain="criminal",
            act_name="Indian Penal Code",
            act_year=1860,
            chapter="CHAPTER XVII",
            section_number="415",
            section_title="Cheating",
            source_citation="IPC 1860, S.415",
            text=(
                "Whoever, by deceiving any person, fraudulently induces the person so "
                "deceived to deliver any property to any person, is said to cheat."
            ),
        ),
        LegalChunk(
            domain="criminal",
            act_name="Indian Penal Code",
            act_year=1860,
            chapter="CHAPTER XVII",
            section_number="441",
            section_title="Criminal trespass",
            source_citation="IPC 1860, S.441",
            text=(
                "Whoever enters into or upon property in the possession of another with "
                "intent to commit an offence, or to intimidate, insult or annoy any "
                "person in possession of such property, is said to commit criminal "
                "trespass."
            ),
        ),
        LegalChunk(
            domain="criminal",
            act_name="Indian Penal Code",
            act_year=1860,
            chapter="CHAPTER XVI",
            section_number="324",
            section_title="Voluntarily causing hurt by dangerous means",
            source_citation="IPC 1860, S.324",
            text=(
                "Whoever voluntarily causes hurt by means of any instrument for "
                "shooting, stabbing or cutting, or any instrument which is likely to "
                "cause death when used for causing hurt, shall be punished with "
                "imprisonment."
            ),
        ),
        LegalChunk(
            domain="property",
            act_name="Transfer of Property Act",
            act_year=1882,
            chapter="CHAPTER III",
            section_number="54",
            section_title="Sale how made",
            source_citation="TPA 1882, S.54",
            text=(
                "'Sale' is a transfer of ownership in exchange for a price paid or "
                "promised or part-paid and part-promised."
            ),
        ),
        LegalChunk(
            domain="property",
            act_name="Transfer of Property Act",
            act_year=1882,
            chapter="CHAPTER IV",
            section_number="58",
            section_title="Mortgage defined",
            source_citation="TPA 1882, S.58",
            text=(
                "A mortgage is the transfer of an interest in specific immovable "
                "property for the purpose of securing the payment of money advanced by "
                "way of loan."
            ),
        ),
        LegalChunk(
            domain="property",
            act_name="Transfer of Property Act",
            act_year=1882,
            chapter="CHAPTER V",
            section_number="105",
            section_title="Lease defined",
            source_citation="TPA 1882, S.105",
            text=(
                "A lease of immovable property is a transfer of a right to enjoy such "
                "property, made for a certain time, in consideration of a price paid or "
                "rent."
            ),
        ),
        LegalChunk(
            domain="property",
            act_name="Transfer of Property Act",
            act_year=1882,
            chapter="CHAPTER VII",
            section_number="122",
            section_title="Gift defined",
            source_citation="TPA 1882, S.122",
            text=(
                "'Gift' is the transfer of certain existing property made voluntarily "
                "and without consideration, by one person to another, and accepted by "
                "the donee."
            ),
        ),
        LegalChunk(
            domain="consumer",
            act_name="Consumer Protection Act",
            act_year=2019,
            chapter="CHAPTER I",
            section_number="17",
            section_title="Deficiency defined",
            source_citation="CPA 2019, S.17",
            text=(
                "'Deficiency' means any fault, imperfection, shortcoming or inadequacy "
                "in the quality of service which is required to be maintained under any "
                "law."
            ),
        ),
        LegalChunk(
            domain="consumer",
            act_name="Consumer Protection Act",
            act_year=2019,
            chapter="CHAPTER I",
            section_number="47",
            section_title="Unfair trade practice",
            source_citation="CPA 2019, S.47",
            text=(
                "'Unfair trade practice' means the adoption of any unfair method or "
                "deceptive practice for the purpose of promoting the sale of any goods "
                "or services."
            ),
        ),
        LegalChunk(
            domain="consumer",
            act_name="Consumer Protection Act",
            act_year=2019,
            chapter="CHAPTER III",
            section_number="35",
            section_title="Manner of filing complaint",
            source_citation="CPA 2019, S.35",
            text=(
                "A complaint may be filed with the District Commission by the consumer "
                "against whom such deficiency or unfair trade practice has occurred."
            ),
        ),
        LegalChunk(
            domain="consumer",
            act_name="Consumer Protection Act",
            act_year=2019,
            chapter="CHAPTER III",
            section_number="83",
            section_title="Class action complaints",
            source_citation="CPA 2019, S.83",
            text=(
                "Where numerous consumers having the same interest are affected, one or "
                "more of such consumers may, with the permission of the Commission, "
                "file a complaint on behalf of all consumers so interested."
            ),
        ),
    ]


@pytest.fixture
def built_indices(tmp_path: Path, fixture_chunks: list[LegalChunk], embedding_model: FixtureConceptEmbeddings):
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    build_faiss_index(fixture_chunks, embedding_model, str(faiss_dir))
    build_bm25_index(fixture_chunks, str(bm25_dir))

    faiss_index = load_faiss_index(str(faiss_dir), embedding_model)
    bm25_index = load_bm25_index(str(bm25_dir))
    return faiss_index, bm25_index


# Keyword-favorable: exact section number present (strong BM25 signal), plus
# wording that semantically decoys toward an unrelated chunk.
KEYWORD_FAVORABLE_QUERIES: list[tuple[str, str]] = [
    (
        "Section 378 - explain the process of using my house as collateral for a loan.",
        "IPC 1860, S.378",
    ),
    (
        "Section 58 - explain how someone unlawfully entered a neighbour's yard.",
        "TPA 1882, S.58",
    ),
    (
        "Section 17 - what counts as misleading advertisement in marketing?",
        "CPA 2019, S.17",
    ),
    (
        "Section 105 - how do I lodge a consumer complaint about a bad purchase?",
        "TPA 1882, S.105",
    ),
]

# Semantic-favorable: lexically-disjoint paraphrase, no section number.
SEMANTIC_FAVORABLE_QUERIES: list[tuple[str, str]] = [
    (
        "Someone unlawfully entered my property and sneaked onto the land at "
        "night, what offence is this?",
        "IPC 1860, S.441",
    ),
    (
        "A man was attacked with a knife and injured using a weapon during a "
        "fight, which law applies?",
        "IPC 1860, S.324",
    ),
    (
        "A company ran a misleading advertisement with deceptive marketing "
        "tactics to boost sales, what's this called?",
        "CPA 2019, S.47",
    ),
    (
        "Many customers with a common grievance are planning to join as a group "
        "of affected buyers filing together against the seller.",
        "CPA 2019, S.83",
    ),
]

QUERY_SET: list[tuple[str, str]] = KEYWORD_FAVORABLE_QUERIES + SEMANTIC_FAVORABLE_QUERIES

RECALL_AT_K = 5


def _recall_at_k(citations: list[str], expected_citation: str) -> float:
    """1.0 if `expected_citation` is present in the (already top-k) results, else 0.0."""
    return 1.0 if expected_citation in citations else 0.0


def _semantic_only_recall(faiss_index, query: str, expected_citation: str) -> float:
    hits = query_faiss_index(faiss_index, query, k=RECALL_AT_K)
    return _recall_at_k([hit.source_citation for hit in hits], expected_citation)


def _keyword_only_recall(bm25_index, query: str, expected_citation: str) -> float:
    hits = query_bm25_index(bm25_index, query, k=RECALL_AT_K)
    return _recall_at_k([hit.source_citation for hit in hits], expected_citation)


def _hybrid_recall(faiss_index, bm25_index, query: str, expected_citation: str) -> float:
    hits = query_hybrid_index(faiss_index, bm25_index, query, k=RECALL_AT_K)
    return _recall_at_k([hit.source_citation for hit in hits], expected_citation)


def _mean_recall(recalls: list[float]) -> float:
    return sum(recalls) / len(recalls)


def test_hybrid_recall_at_5_meets_or_exceeds_either_single_method(built_indices):
    """Core T20 acceptance criterion: hybrid recall@5 >= max(semantic, keyword)."""
    faiss_index, bm25_index = built_indices

    semantic_recalls = [
        _semantic_only_recall(faiss_index, query, expected) for query, expected in QUERY_SET
    ]
    keyword_recalls = [
        _keyword_only_recall(bm25_index, query, expected) for query, expected in QUERY_SET
    ]
    hybrid_recalls = [
        _hybrid_recall(faiss_index, bm25_index, query, expected) for query, expected in QUERY_SET
    ]

    semantic_recall_at_5 = _mean_recall(semantic_recalls)
    keyword_recall_at_5 = _mean_recall(keyword_recalls)
    hybrid_recall_at_5 = _mean_recall(hybrid_recalls)

    assert hybrid_recall_at_5 >= max(semantic_recall_at_5, keyword_recall_at_5)


def test_hybrid_recall_at_5_is_perfect_across_mixed_query_set(built_indices):
    """Hybrid fusion should recover every chunk - neither leg alone needs to win."""
    faiss_index, bm25_index = built_indices

    hybrid_recalls = [
        _hybrid_recall(faiss_index, bm25_index, query, expected) for query, expected in QUERY_SET
    ]

    assert _mean_recall(hybrid_recalls) == 1.0


def test_semantic_only_misses_at_least_one_keyword_favorable_query(built_indices):
    """Demonstrates hybrid's value: semantic-only alone is fooled by the decoy wording."""
    faiss_index, _bm25_index = built_indices

    semantic_recalls = [
        _semantic_only_recall(faiss_index, query, expected)
        for query, expected in KEYWORD_FAVORABLE_QUERIES
    ]

    assert _mean_recall(semantic_recalls) < 1.0


def test_keyword_only_misses_at_least_one_semantic_favorable_query(built_indices):
    """Demonstrates hybrid's value: keyword-only alone can't find lexically-disjoint paraphrases."""
    _faiss_index, bm25_index = built_indices

    keyword_recalls = [
        _keyword_only_recall(bm25_index, query, expected)
        for query, expected in SEMANTIC_FAVORABLE_QUERIES
    ]

    assert _mean_recall(keyword_recalls) < 1.0


def test_fixture_retrieval_suite_runs_quickly(built_indices):
    """Acceptance criterion: runs in under a few seconds as part of the standard suite."""
    faiss_index, bm25_index = built_indices

    started = time.perf_counter()
    for query, expected in QUERY_SET:
        _hybrid_recall(faiss_index, bm25_index, query, expected)
    elapsed = time.perf_counter() - started

    assert elapsed < 5.0
