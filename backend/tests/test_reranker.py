"""Unit tests for app.rag.reranker. See TASKS.md T19."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_core.cross_encoders import BaseCrossEncoder
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from app.core.config import Settings
from app.rag.reranker import (
    build_reranking_retriever,
    get_cross_encoder_model,
    reset_cross_encoder_model_cache,
)


class StubRetriever(BaseRetriever):
    """A fixed-document retriever standing in for the fused hybrid retriever."""

    documents: list[Document] = []

    def _get_relevant_documents(self, query: str, *, run_manager: Any) -> list[Document]:
        return list(self.documents)


class ScriptedCrossEncoder(BaseCrossEncoder):
    """Deterministic cross-encoder returning caller-supplied scores.

    Keyed by page_content so tests can assert exactly which candidate should
    be ranked to the top after reranking, without loading a real model.
    """

    def __init__(self, scores_by_content: dict[str, float]):
        self._scores_by_content = scores_by_content

    def score(self, text_pairs: list[tuple[str, str]]) -> list[float]:
        return [self._scores_by_content[content] for _, content in text_pairs]


@pytest.fixture
def candidate_documents() -> list[Document]:
    return [
        Document(
            page_content="Section 154 CrPC - police must register cognizable offences.",
            metadata={"source_citation": "CrPC 1973, S.154"},
        ),
        Document(
            page_content="Section 304A IPC - punishment for causing death by negligence.",
            metadata={"source_citation": "IPC 1860, S.304A"},
        ),
        Document(
            page_content="Section 54 TPA - definition of a sale of immovable property.",
            metadata={"source_citation": "TPA 1882, S.54"},
        ),
    ]


@pytest.fixture(autouse=True)
def _clear_cross_encoder_cache():
    reset_cross_encoder_model_cache()
    yield
    reset_cross_encoder_model_cache()


# --- Gating on settings.enable_reranker -------------------------------------


def test_disabled_flag_returns_base_retriever_unchanged(candidate_documents: list[Document]):
    """Acceptance criterion: disabled flag -> hybrid output passes through unchanged."""
    base_retriever = StubRetriever(documents=candidate_documents)

    with patch("app.rag.reranker.settings.enable_reranker", False):
        result = build_reranking_retriever(base_retriever)

    assert result is base_retriever
    assert result.invoke("any query") == candidate_documents


def test_enabled_flag_wraps_in_contextual_compression_retriever(
    candidate_documents: list[Document],
):
    base_retriever = StubRetriever(documents=candidate_documents)
    fake_encoder = ScriptedCrossEncoder({doc.page_content: 0.0 for doc in candidate_documents})

    with patch("app.rag.reranker.settings.enable_reranker", True):
        result = build_reranking_retriever(base_retriever, cross_encoder=fake_encoder)

    assert isinstance(result, ContextualCompressionRetriever)
    assert result.base_retriever is base_retriever


# --- Reranking behaviour ------------------------------------------------------


def test_reranking_promotes_most_relevant_candidate_to_first(
    candidate_documents: list[Document],
):
    """Acceptance criterion: reranking reorders results, most relevant first."""
    base_retriever = StubRetriever(documents=candidate_documents)
    # The 304A negligence chunk is the true best match for the query below;
    # scripted scores make that explicit and deterministic.
    scores_by_content = {
        candidate_documents[0].page_content: 0.12,  # CrPC 154 - low relevance
        candidate_documents[1].page_content: 0.97,  # IPC 304A - best match
        candidate_documents[2].page_content: 0.05,  # TPA 54 - irrelevant
    }
    fake_encoder = ScriptedCrossEncoder(scores_by_content)

    with patch("app.rag.reranker.settings.enable_reranker", True):
        retriever = build_reranking_retriever(
            base_retriever, top_n=3, cross_encoder=fake_encoder
        )
        results = retriever.invoke("What is the punishment for death by negligence?")

    assert results[0].metadata["source_citation"] == "IPC 1860, S.304A"


def test_reranking_returns_configured_top_n(candidate_documents: list[Document]):
    base_retriever = StubRetriever(documents=candidate_documents)
    fake_encoder = ScriptedCrossEncoder(
        {
            candidate_documents[0].page_content: 0.5,
            candidate_documents[1].page_content: 0.9,
            candidate_documents[2].page_content: 0.1,
        }
    )

    with patch("app.rag.reranker.settings.enable_reranker", True):
        retriever = build_reranking_retriever(base_retriever, top_n=2, cross_encoder=fake_encoder)
        results = retriever.invoke("any query")

    assert len(results) == 2
    assert [doc.metadata["source_citation"] for doc in results] == [
        "IPC 1860, S.304A",
        "CrPC 1973, S.154",
    ]


def test_reranking_defaults_top_n_from_settings(candidate_documents: list[Document]):
    base_retriever = StubRetriever(documents=candidate_documents)
    fake_encoder = ScriptedCrossEncoder({doc.page_content: 0.5 for doc in candidate_documents})

    with (
        patch("app.rag.reranker.settings.enable_reranker", True),
        patch("app.rag.reranker.settings.rerank_top_n", 1),
    ):
        retriever = build_reranking_retriever(base_retriever, cross_encoder=fake_encoder)
        results = retriever.invoke("any query")

    assert len(results) == 1


# --- get_cross_encoder_model --------------------------------------------------


def test_get_cross_encoder_model_uses_settings_model_name(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-google-api-key")
    monkeypatch.setenv("RERANKER_MODEL", "custom/cross-encoder-model")

    with patch("app.rag.reranker.settings", Settings(_env_file=None)):  # type: ignore[call-arg]
        with patch("app.rag.reranker.HuggingFaceCrossEncoder") as mock_cls:
            mock_cls.return_value = MagicMock()
            get_cross_encoder_model()

    mock_cls.assert_called_once_with(
        model_name="custom/cross-encoder-model",
        model_kwargs={"device": "cpu"},
    )


def test_get_cross_encoder_model_caches_per_model_name():
    with patch("app.rag.reranker.HuggingFaceCrossEncoder") as mock_cls:
        sentinel = MagicMock()
        mock_cls.return_value = sentinel

        first = get_cross_encoder_model("cross-encoder/ms-marco-MiniLM-L-6-v2")
        second = get_cross_encoder_model("cross-encoder/ms-marco-MiniLM-L-6-v2")

    assert first is second
    mock_cls.assert_called_once()
