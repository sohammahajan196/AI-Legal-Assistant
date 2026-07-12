"""Unit tests for app.rag.chain.run_rag_chain. See TASKS.md T30.

Covers T30's own acceptance criteria with a fixture corpus + mocked LLM.
Comprehensive multi-domain/multi-turn/refusal-path coverage belongs in T31's
end-to-end suite; this file focuses on T30's three scenarios: single-turn
success, no-relevant-content refusal (no LLM call), and sync/async
invocability.
"""

from __future__ import annotations

import math
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.embeddings import Embeddings

from app.rag.bm25_index import build_bm25_index, load_bm25_index
from app.rag.chain import run_rag_chain, run_rag_chain_sync
from app.rag.chunking import LegalChunk
from app.rag.vectorstore import build_faiss_index, load_faiss_index
from app.schemas.legal_answer import LegalDomain, LLMStructuredAnswer

NEGLIGENCE_TEXT = (
    "Section 304A. Causing death by negligence.—Whoever causes the death of any "
    "person by doing any rash or negligent act not amounting to culpable homicide, "
    "shall be punished with imprisonment."
)


class BagOfWordsEmbeddings(Embeddings):
    """Deterministic offline embedder over a fixed vocabulary (mirrors the
    fixture pattern in test_confidence.py/test_hybrid_retriever.py) -- avoids
    any real model download/network call in tests, per testing.mdc."""

    VOCAB = [
        "whoever",
        "causes",
        "death",
        "by",
        "negligence",
        "shall",
        "be",
        "punished",
        "with",
        "imprisonment",
        "cognizable",
        "cake",
        "chocolate",
        "recipe",
    ]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * len(self.VOCAB)
        lower = text.lower()
        for i, word in enumerate(self.VOCAB):
            if word in lower:
                vec[i] = 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0:
            return vec
        return [v / norm for v in vec]


@pytest.fixture
def embedding_model() -> BagOfWordsEmbeddings:
    return BagOfWordsEmbeddings()


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
            text=NEGLIGENCE_TEXT,
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
    ]


@pytest.fixture
def built_indices(tmp_path: Path, fixture_chunks: list[LegalChunk], embedding_model: BagOfWordsEmbeddings):
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    build_faiss_index(fixture_chunks, embedding_model, str(faiss_dir))
    build_bm25_index(fixture_chunks, str(bm25_dir))

    faiss_index = load_faiss_index(str(faiss_dir), embedding_model)
    bm25_index = load_bm25_index(str(bm25_dir))
    return faiss_index, bm25_index


def _mock_llm_returning(structured_result: LLMStructuredAnswer) -> MagicMock:
    """A mocked llm whose `.with_structured_output(...).ainvoke(...)` returns
    `structured_result`, mirroring the real `.with_structured_output(schema,
    method="json_schema")` call shape used by app.rag.structured_llm."""
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=structured_result)
    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm
    return llm


# --- single-turn success: non-empty citations, is_refusal=False -------------


@pytest.mark.asyncio
async def test_well_covered_query_returns_answer_with_citations_and_no_refusal(built_indices, embedding_model):
    faiss_index, bm25_index = built_indices
    mock_llm = _mock_llm_returning(
        LLMStructuredAnswer(
            answer=NEGLIGENCE_TEXT,
            legal_domain=LegalDomain.CRIMINAL,
            used_citation_ids=["IPC 1860, S.304A"],
            is_refusal=False,
        )
    )

    response = await run_rag_chain(
        "What is the punishment for causing death by negligence?",
        session_id=None,
        user_type="layperson",
        llm=mock_llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    assert response.is_refusal is False
    assert response.citations
    assert response.citations[0].section == "304A"
    assert response.legal_domain == LegalDomain.CRIMINAL
    assert response.confidence_score > 0.4
    assert response.disclaimer


# --- no relevant content: refusal without ever calling the LLM's generation --


@pytest.mark.asyncio
async def test_no_relevant_content_refuses_without_calling_llm_generation(built_indices, embedding_model):
    faiss_index, bm25_index = built_indices
    mock_llm = _mock_llm_returning(
        LLMStructuredAnswer(answer="should never be produced", legal_domain=LegalDomain.OTHER)
    )

    with patch("app.rag.chain.query_hybrid_index", return_value=[]):
        response = await run_rag_chain(
            "What is the best chocolate cake recipe?",
            session_id=None,
            user_type="layperson",
            llm=mock_llm,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
            embedding_model=embedding_model,
        )

    assert response.is_refusal is True
    mock_llm.with_structured_output.assert_not_called()
    assert "licensed lawyer" in response.answer


# --- invocable both sync and async -------------------------------------------


@pytest.mark.asyncio
async def test_chain_is_invocable_asynchronously(built_indices, embedding_model):
    faiss_index, bm25_index = built_indices
    mock_llm = _mock_llm_returning(
        LLMStructuredAnswer(
            answer=NEGLIGENCE_TEXT,
            legal_domain=LegalDomain.CRIMINAL,
            used_citation_ids=["IPC 1860, S.304A"],
        )
    )

    response = await run_rag_chain(
        "What is the punishment for causing death by negligence?",
        session_id=None,
        user_type="lawyer",
        llm=mock_llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    assert response.is_refusal is False


def test_chain_is_invocable_synchronously(built_indices, embedding_model):
    faiss_index, bm25_index = built_indices
    mock_llm = _mock_llm_returning(
        LLMStructuredAnswer(
            answer=NEGLIGENCE_TEXT,
            legal_domain=LegalDomain.CRIMINAL,
            used_citation_ids=["IPC 1860, S.304A"],
        )
    )

    response = run_rag_chain_sync(
        "What is the punishment for causing death by negligence?",
        session_id=None,
        user_type="law_student",
        llm=mock_llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    assert response.is_refusal is False
    assert response.citations
