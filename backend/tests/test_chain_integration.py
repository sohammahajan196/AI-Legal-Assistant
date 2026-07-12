"""End-to-end RAG chain tests (fixture corpus + mocked LLM). See TASKS.md T31.

Exercises app.rag.chain.run_rag_chain (T30) across multiple domains,
multi-turn conversations, and both user_type and refusal paths, using a
12-chunk fixture corpus spanning 6 legal domains (per testing.mdc's ~10-15
hand-written chunk guidance) and a fully mocked LLM. No real network calls
(no real Gemini, HuggingFace, FAISS-download, or Redis dependency).
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage

from app.rag.bm25_index import build_bm25_index, load_bm25_index
from app.rag.chain import run_rag_chain
from app.rag.chunking import LegalChunk
from app.rag.refusal import REFUSAL_TEMPLATE
from app.rag.vectorstore import build_faiss_index, chunk_to_document, load_faiss_index
from app.schemas.legal_answer import LegalDomain, LLMStructuredAnswer


def mock_llm(structured_result: LLMStructuredAnswer, condensed_content: str | None = None) -> MagicMock:
    """Build a mocked llm supporting both call shapes app.rag.chain relies on:
    top-level `.ainvoke(...)` (app.rag.condense's follow-up rewriting) and
    `.with_structured_output(schema, method="json_schema").ainvoke(...)`
    (app.rag.structured_llm's structured generation)."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content=condensed_content or ""))

    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=structured_result)
    llm.with_structured_output.return_value = structured_llm

    return llm

# --- fixture corpus: 12 hand-written chunks across 6 domains ----------------

NEGLIGENCE_CHUNK = LegalChunk(
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
)

THEFT_CHUNK = LegalChunk(
    domain="criminal",
    act_name="Indian Penal Code",
    act_year=1860,
    chapter="CHAPTER XVII",
    section_number="379",
    section_title="Punishment for theft",
    source_citation="IPC 1860, S.379",
    text=(
        "Section 379. Punishment for theft.—Whoever commits theft shall be punished "
        "with imprisonment of either description for a term which may extend to three "
        "years, or with fine, or with both."
    ),
)

FIR_CHUNK = LegalChunk(
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
)

DIVORCE_CHUNK = LegalChunk(
    domain="family",
    act_name="Hindu Marriage Act",
    act_year=1955,
    chapter="CHAPTER III",
    section_number="13",
    section_title="Divorce",
    source_citation="HMA 1955, S.13",
    text=(
        "Section 13. Divorce.—Any marriage solemnized may, on a petition presented by "
        "either the husband or the wife, be dissolved by a decree of divorce on the "
        "ground of cruelty or desertion."
    ),
)

MARRIAGE_CONDITIONS_CHUNK = LegalChunk(
    domain="family",
    act_name="Hindu Marriage Act",
    act_year=1955,
    chapter="CHAPTER I",
    section_number="5",
    section_title="Conditions for a Hindu marriage",
    source_citation="HMA 1955, S.5",
    text=(
        "Section 5. Conditions for a Hindu marriage.—A marriage may be solemnized "
        "between any two Hindus if neither party has a spouse living at the time of "
        "the marriage."
    ),
)

RETRENCHMENT_CHUNK = LegalChunk(
    domain="labour",
    act_name="Industrial Disputes Act",
    act_year=1947,
    chapter="CHAPTER VA",
    section_number="25F",
    section_title="Conditions precedent to retrenchment of workmen",
    source_citation="IDA 1947, S.25F",
    text=(
        "Section 25F. Conditions precedent to retrenchment of workmen.—No workman "
        "employed in any industry who has been in continuous service for not less than "
        "one year shall be retrenched until one month's notice has been given and "
        "compensation has been paid."
    ),
)

MINIMUM_WAGE_CHUNK = LegalChunk(
    domain="labour",
    act_name="Code on Wages",
    act_year=2019,
    chapter="CHAPTER I",
    section_number="2",
    section_title="Definitions",
    source_citation="COW 2019, S.2",
    text=(
        "Section 2. Definitions.—In this Code, 'minimum wage' means the wage fixed "
        "under section 6 payable to employees for work done."
    ),
)

CONSUMER_DEFINITION_CHUNK = LegalChunk(
    domain="consumer",
    act_name="Consumer Protection Act",
    act_year=2019,
    chapter="CHAPTER I",
    section_number="2",
    section_title="Definitions",
    source_citation="CPA 2019, S.2",
    text=(
        "Section 2. Definitions.—'Consumer' means any person who buys goods or hires "
        "services for consideration and does not include a person who obtains goods "
        "for resale."
    ),
)

CONSUMER_COMPLAINT_CHUNK = LegalChunk(
    domain="consumer",
    act_name="Consumer Protection Act",
    act_year=2019,
    chapter="CHAPTER III",
    section_number="35",
    section_title="Manner in which complaint shall be made",
    source_citation="CPA 2019, S.35",
    text=(
        "Section 35. Manner in which complaint shall be made.—A complaint may be "
        "filed with the District Commission by the consumer against whom goods sold "
        "or services rendered are alleged to be defective."
    ),
)

SALE_CHUNK = LegalChunk(
    domain="property",
    act_name="Transfer of Property Act",
    act_year=1882,
    chapter="CHAPTER II",
    section_number="54",
    section_title="Sale how made",
    source_citation="TPA 1882, S.54",
    text=(
        "Section 54. Sale how made.—'Sale' is a transfer of ownership in immovable "
        "property in exchange for a price paid or promised or part-paid and "
        "part-promised."
    ),
)

MORTGAGE_CHUNK = LegalChunk(
    domain="property",
    act_name="Transfer of Property Act",
    act_year=1882,
    chapter="CHAPTER IV",
    section_number="58",
    section_title="Mortgage defined",
    source_citation="TPA 1882, S.58",
    text=(
        "Section 58. 'Mortgage' defined.—A mortgage is the transfer of an interest in "
        "specific immovable property for the purpose of securing the payment of money "
        "advanced."
    ),
)

JURISDICTION_CHUNK = LegalChunk(
    domain="civil",
    act_name="Code of Civil Procedure",
    act_year=1908,
    chapter="CHAPTER II",
    section_number="9",
    section_title="Courts to try all civil suits unless barred",
    source_citation="CPC 1908, S.9",
    text=(
        "Section 9. Courts to try all civil suits unless barred.—The courts shall "
        "have jurisdiction to try all suits of a civil nature excepting suits of "
        "which cognizance is expressly or impliedly barred."
    ),
)

FIXTURE_CHUNKS: list[LegalChunk] = [
    NEGLIGENCE_CHUNK,
    THEFT_CHUNK,
    FIR_CHUNK,
    DIVORCE_CHUNK,
    MARRIAGE_CONDITIONS_CHUNK,
    RETRENCHMENT_CHUNK,
    MINIMUM_WAGE_CHUNK,
    CONSUMER_DEFINITION_CHUNK,
    CONSUMER_COMPLAINT_CHUNK,
    SALE_CHUNK,
    MORTGAGE_CHUNK,
    JURISDICTION_CHUNK,
]

CHUNKS_BY_CITATION: dict[str, LegalChunk] = {chunk.source_citation: chunk for chunk in FIXTURE_CHUNKS}


# --- deterministic offline embeddings (no real model download/network) ------

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> set[str]:
    return set(_WORD_RE.findall(text.lower()))


def _build_vocabulary(chunks: list[LegalChunk]) -> list[str]:
    """Derive the embedding vocabulary directly from the fixture corpus text,
    so every content word the retrieval tests rely on is guaranteed to be
    represented (no hand-typed vocab list to keep in sync)."""
    vocabulary: set[str] = set()
    for chunk in chunks:
        vocabulary |= _tokenize(chunk.text)
        vocabulary |= _tokenize(chunk.section_title or "")
    return sorted(vocabulary)


class BagOfWordsEmbeddings(Embeddings):
    """Deterministic offline embedder: an L2-normalized word-presence vector
    over a fixed vocabulary. Mirrors the pattern in test_confidence.py/
    test_hybrid_retriever.py -- cosine similarity reflects lexical overlap
    without downloading or network-calling a real HuggingFace model (see
    testing.mdc: "no test may make a real network call")."""

    def __init__(self, vocabulary: list[str]) -> None:
        self._vocab_index = {word: i for i, word in enumerate(vocabulary)}

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._vectorize(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vectorize(text)

    def _vectorize(self, text: str) -> list[float]:
        vec = [0.0] * len(self._vocab_index)
        for word in _tokenize(text):
            idx = self._vocab_index.get(word)
            if idx is not None:
                vec[idx] = 1.0
        norm = sum(v * v for v in vec) ** 0.5
        if norm == 0:
            return vec
        return [v / norm for v in vec]


@pytest.fixture(scope="module")
def embedding_model() -> BagOfWordsEmbeddings:
    return BagOfWordsEmbeddings(_build_vocabulary(FIXTURE_CHUNKS))


@pytest.fixture(scope="module")
def built_indices(tmp_path_factory: pytest.TempPathFactory, embedding_model: BagOfWordsEmbeddings):
    tmp_path: Path = tmp_path_factory.mktemp("chain_integration_indices")
    faiss_dir = tmp_path / "faiss_index"
    bm25_dir = tmp_path / "bm25_index"
    build_faiss_index(FIXTURE_CHUNKS, embedding_model, str(faiss_dir))
    build_bm25_index(FIXTURE_CHUNKS, str(bm25_dir))

    faiss_index = load_faiss_index(str(faiss_dir), embedding_model)
    bm25_index = load_bm25_index(str(bm25_dir))
    return faiss_index, bm25_index


def _assert_citation_matches_chunk(citation, chunk: LegalChunk) -> None:
    """Verify a response citation maps back to its fixture chunk's metadata
    exactly (TASKS.md T31 acceptance criterion).

    `excerpt` is compared against the exact indexed page content (built by
    `app.rag.vectorstore.chunk_to_document`, which prefixes the section
    header for BM25 keyword matching -- see T15/T16) rather than the chunk's
    raw `.text`, since that's the real text retrieval returns end-to-end.
    """
    assert citation.document == chunk.act_name
    assert citation.act_year == chunk.act_year
    assert citation.section == chunk.section_number
    assert citation.domain.value == chunk.domain
    assert citation.excerpt == chunk_to_document(chunk).page_content


# --- single-turn success, across multiple domains ----------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("query", "chunk", "domain"),
    [
        (
            "Whoever causes death by negligence, what is the punishment involved?",
            NEGLIGENCE_CHUNK,
            LegalDomain.CRIMINAL,
        ),
        (
            "What notice and compensation must be given before retrenchment of a workman?",
            RETRENCHMENT_CHUNK,
            LegalDomain.LABOUR,
        ),
        (
            "On what ground can a wife get a divorce, such as cruelty or desertion?",
            DIVORCE_CHUNK,
            LegalDomain.FAMILY,
        ),
        (
            "How is a mortgage defined as a transfer of an interest in immovable property to secure money advanced?",
            MORTGAGE_CHUNK,
            LegalDomain.PROPERTY,
        ),
        (
            "Do civil courts have jurisdiction to try all suits of a civil nature unless expressly barred?",
            JURISDICTION_CHUNK,
            LegalDomain.CIVIL,
        ),
    ],
)
async def test_single_turn_success_across_domains(built_indices, embedding_model, query, chunk, domain):
    faiss_index, bm25_index = built_indices
    llm = mock_llm(
        LLMStructuredAnswer(
            answer=chunk.text,
            legal_domain=domain,
            used_citation_ids=[chunk.source_citation],
            is_refusal=False,
        )
    )

    response = await run_rag_chain(
        query,
        session_id=None,
        user_type="layperson",
        llm=llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    assert response.is_refusal is False
    assert response.legal_domain == domain
    assert len(response.citations) == 1
    _assert_citation_matches_chunk(response.citations[0], chunk)


# --- user_type wiring ----------------------------------------------------------


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("user_type", "expected_audience_snippet"),
    [
        ("layperson", "plain, everyday language"),
        ("law_student", "legal terminology"),
        ("lawyer", "practicing lawyer"),
    ],
)
async def test_user_type_selects_the_matching_prompt_template(
    built_indices, embedding_model, user_type, expected_audience_snippet
):
    faiss_index, bm25_index = built_indices
    llm = mock_llm(
        LLMStructuredAnswer(
            answer=CONSUMER_DEFINITION_CHUNK.text,
            legal_domain=LegalDomain.CONSUMER,
            used_citation_ids=[CONSUMER_DEFINITION_CHUNK.source_citation],
        )
    )

    response = await run_rag_chain(
        "Who qualifies as a consumer that buys goods or hires services for consideration?",
        session_id=None,
        user_type=user_type,
        llm=llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    assert response.is_refusal is False
    sent_prompt = llm.with_structured_output.return_value.ainvoke.await_args.args[0]
    system_message_content = sent_prompt[0].content
    assert expected_audience_snippet in system_message_content


# --- multi-turn follow-up: condensed query drives retrieval ------------------


@pytest.mark.asyncio
async def test_multi_turn_followup_condenses_before_retrieving():
    """A follow-up like "what if it's a repeat offense?" shares no vocabulary
    with the fixture corpus on its own; only the condensed standalone query
    (built from prior history) can drive correct retrieval -- proving the
    chain actually uses the condensed query, not the raw follow-up."""
    embedding_model_ = BagOfWordsEmbeddings(_build_vocabulary(FIXTURE_CHUNKS))
    faiss_dir_chunks = FIXTURE_CHUNKS

    with tempfile.TemporaryDirectory() as tmp_dir:
        faiss_dir = Path(tmp_dir) / "faiss_index"
        bm25_dir = Path(tmp_dir) / "bm25_index"
        build_faiss_index(faiss_dir_chunks, embedding_model_, str(faiss_dir))
        build_bm25_index(faiss_dir_chunks, str(bm25_dir))
        faiss_index = load_faiss_index(str(faiss_dir), embedding_model_)
        bm25_index = load_bm25_index(str(bm25_dir))

        history = [
            {"role": "user", "content": "What is the punishment for theft under IPC?"},
            {
                "role": "assistant",
                "content": "Theft is punishable under Section 379 IPC with imprisonment up to three years, fine, or both.",
            },
        ]
        condensed_query = (
            "Whoever commits theft again as a repeat offense, what is the punishment with "
            "imprisonment involved under Section 379 IPC?"
        )
        llm = mock_llm(
            LLMStructuredAnswer(
                answer=THEFT_CHUNK.text,
                legal_domain=LegalDomain.CRIMINAL,
                used_citation_ids=[THEFT_CHUNK.source_citation],
                is_refusal=False,
            ),
            condensed_content=condensed_query,
        )

        response = await run_rag_chain(
            "What if it's a repeat offense?",
            session_id="session-123",
            user_type="layperson",
            history=history,
            llm=llm,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
            embedding_model=embedding_model_,
        )

    llm.ainvoke.assert_awaited_once()
    condense_prompt = llm.ainvoke.await_args.args[0]
    assert "theft" in str(condense_prompt).lower()

    assert response.is_refusal is False
    assert len(response.citations) == 1
    _assert_citation_matches_chunk(response.citations[0], THEFT_CHUNK)


# --- low-confidence refusal: generation attempted, then overridden ----------


@pytest.mark.asyncio
async def test_low_confidence_answer_triggers_post_generation_refusal(built_indices, embedding_model):
    """Retrieval succeeds (clears the pre-generation bar via the theft chunk),
    but the mocked LLM cites an unrelated low-relevance chunk with an
    ungrounded answer -- the computed confidence must fall below threshold
    and override the answer with the refusal template, while still retaining
    the (low-confidence) citation for transparency, per T26."""
    faiss_index, bm25_index = built_indices
    llm = mock_llm(
        LLMStructuredAnswer(
            # Deliberately unrelated to the (wrongly) cited excerpt's wording,
            # so groundedness -- not just retrieval -- is genuinely low too.
            answer="Theft is a serious offense and repeat offenders may face enhanced imprisonment terms.",
            legal_domain=LegalDomain.CIVIL,
            used_citation_ids=[JURISDICTION_CHUNK.source_citation],
            is_refusal=False,
        )
    )

    response = await run_rag_chain(
        "What happens if someone commits theft and is punished with imprisonment?",
        session_id=None,
        user_type="layperson",
        llm=llm,
        faiss_index=faiss_index,
        bm25_index=bm25_index,
        embedding_model=embedding_model,
    )

    llm.with_structured_output.assert_called_once()
    assert response.is_refusal is True
    assert response.answer == REFUSAL_TEMPLATE
    assert "licensed lawyer" in response.answer
    assert response.confidence_score < 0.4
    assert len(response.citations) == 1
    _assert_citation_matches_chunk(response.citations[0], JURISDICTION_CHUNK)


# --- no-context refusal: refuses without ever calling LLM generation --------


@pytest.mark.asyncio
async def test_no_context_refuses_without_calling_llm_generation(built_indices, embedding_model):
    faiss_index, bm25_index = built_indices
    llm = mock_llm(
        LLMStructuredAnswer(answer="should never be produced", legal_domain=LegalDomain.OTHER)
    )

    with patch("app.rag.chain.query_hybrid_index", return_value=[]):
        response = await run_rag_chain(
            "What is the best chocolate cake recipe?",
            session_id=None,
            user_type="layperson",
            llm=llm,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
            embedding_model=embedding_model,
        )

    llm.with_structured_output.assert_not_called()
    assert response.is_refusal is True
    assert response.answer == REFUSAL_TEMPLATE
    assert response.citations == []
