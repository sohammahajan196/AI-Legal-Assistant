"""Unit tests for eval/run_eval.py. See TASKS.md T49.

Uses a small (~6-chunk) fixture corpus and a deterministic offline embedder
(no real network/HuggingFace/Gemini calls -- see testing.mdc) to verify the
precision@k/recall@k scoring logic and the CLI's report output end-to-end.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AIMessage

from app.rag.bm25_index import build_bm25_index, load_bm25_index
from app.rag.chunking import LegalChunk
from app.rag.vectorstore import build_faiss_index, load_faiss_index
from app.schemas.legal_answer import (
    LegalAnswerResponse,
    LegalDomain,
    LLMStructuredAnswer,
    SourceCitation,
)
from eval import run_eval

_WORD_RE = re.compile(r"[a-z0-9]+")


def mock_llm(structured_result: LLMStructuredAnswer) -> MagicMock:
    """Build a mocked llm supporting the call shapes app.rag.chain relies on
    (mirrors test_chain_integration.py's helper). History is empty in these
    tests so app.rag.condense never calls `.ainvoke` directly, but the mock
    still supports it defensively."""
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content=""))

    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=structured_result)
    llm.with_structured_output.return_value = structured_llm

    return llm


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


class BagOfWordsEmbeddings(Embeddings):
    """Deterministic offline embedder (word-presence vector), mirroring the
    pattern in test_chain_integration.py. Avoids downloading a real
    HuggingFace model in tests."""

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
        return [v / norm for v in vec] if norm else vec


THEFT_CHUNK = LegalChunk(
    domain="criminal",
    act_name="Indian Penal Code",
    act_year=1860,
    chapter="CHAPTER XVII",
    section_number="379",
    section_title="Punishment for theft",
    source_citation="IPC 1860, S.379",
    text=(
        "Section 379. Punishment for theft.—Whoever commits theft shall be "
        "punished with imprisonment of either description for a term which "
        "may extend to three years, or with fine, or with both."
    ),
)

NEGLIGENCE_CHUNK = LegalChunk(
    domain="criminal",
    act_name="Indian Penal Code",
    act_year=1860,
    chapter="CHAPTER XVI",
    section_number="304A",
    section_title="Causing death by negligence",
    source_citation="IPC 1860, S.304A",
    text=(
        "Section 304A. Causing death by negligence.—Whoever causes the death "
        "of any person by doing any rash or negligent act not amounting to "
        "culpable homicide, shall be punished with imprisonment."
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
        "Section 13. Divorce.—Any marriage may, on a petition presented by "
        "either the husband or the wife, be dissolved by a decree of divorce "
        "on the ground of cruelty or desertion."
    ),
)

RES_JUDICATA_CHUNK = LegalChunk(
    domain="civil",
    act_name="Code of Civil Procedure",
    act_year=1908,
    chapter="CHAPTER I",
    section_number="11",
    section_title="Res judicata",
    source_citation="CPC 1908, S.11",
    text=(
        "Section 11. Res judicata.—No Court shall try any suit or issue in "
        "which the matter directly and substantially in issue has been "
        "directly and substantially in issue in a former suit."
    ),
)

LEASE_CHUNK = LegalChunk(
    domain="property",
    act_name="Transfer of Property Act",
    act_year=1882,
    chapter="CHAPTER V",
    section_number="105",
    section_title="Lease defined",
    source_citation="TPA 1882, S.105",
    text=(
        "Section 105. Lease defined.—A lease of immoveable property is a "
        "transfer of a right to enjoy such property, made for a certain time."
    ),
)

MINIMUM_WAGE_CHUNK = LegalChunk(
    domain="labour",
    act_name="Code on Wages",
    act_year=2019,
    chapter="CHAPTER II",
    section_number="5",
    section_title="Payment of minimum rate of wages",
    source_citation="COW 2019, S.5",
    text=(
        "Section 5. Payment of minimum rate of wages.—No employer shall pay "
        "to any employee wages less than the minimum rate of wages notified "
        "by the appropriate Government."
    ),
)

FIXTURE_CHUNKS = [
    THEFT_CHUNK,
    NEGLIGENCE_CHUNK,
    DIVORCE_CHUNK,
    RES_JUDICATA_CHUNK,
    LEASE_CHUNK,
    MINIMUM_WAGE_CHUNK,
]

FIXTURE_VOCAB = sorted({word for chunk in FIXTURE_CHUNKS for word in _tokenize(chunk.text)})


@pytest.fixture(scope="module")
def fixture_indices(tmp_path_factory: pytest.TempPathFactory):
    """Build small FAISS + BM25 indices from FIXTURE_CHUNKS in a temp dir."""
    tmp_dir = tmp_path_factory.mktemp("run_eval_indices")
    faiss_dir = tmp_dir / "faiss"
    bm25_dir = tmp_dir / "bm25"

    embedding_model = BagOfWordsEmbeddings(FIXTURE_VOCAB)
    build_faiss_index(FIXTURE_CHUNKS, embedding_model, str(faiss_dir))
    build_bm25_index(FIXTURE_CHUNKS, str(bm25_dir))

    faiss_index = load_faiss_index(str(faiss_dir), embedding_model)
    bm25_index = load_bm25_index(str(bm25_dir))
    return faiss_index, bm25_index


@pytest.fixture
def fixture_dataset_path(tmp_path: Path) -> Path:
    entries = [
        {
            "question": "What is the punishment for theft under the Indian Penal Code?",
            "expected_domain": "criminal",
            "expected_act": "Indian Penal Code",
            "expected_sections": ["379"],
        },
        {
            "question": "How does the Hindu Marriage Act define divorce grounds?",
            "expected_domain": "family",
            "expected_act": "Hindu Marriage Act",
            "expected_sections": ["13"],
        },
        {
            "question": "What section of an unrelated act about spaceship licensing applies here?",
            "expected_domain": "other",
            "expected_act": "Nonexistent Act",
            "expected_sections": ["999"],
        },
    ]
    dataset_path = tmp_path / "qa_dataset.jsonl"
    dataset_path.write_text(
        "\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8"
    )
    return dataset_path


# --- load_qa_dataset ---------------------------------------------------------


def test_load_qa_dataset_parses_all_entries(fixture_dataset_path: Path):
    questions = run_eval.load_qa_dataset(fixture_dataset_path)

    assert len(questions) == 3
    assert questions[0].expected_domain == "criminal"
    assert questions[0].expected_sections == ["379"]


def test_load_qa_dataset_raises_on_missing_field(tmp_path: Path):
    bad_path = tmp_path / "bad.jsonl"
    bad_path.write_text(json.dumps({"question": "no domain here"}) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="missing required field"):
        run_eval.load_qa_dataset(bad_path)


# --- score_question -----------------------------------------------------------


def test_score_question_full_match_gives_precision_and_recall_of_one():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["379"],
    )

    result = run_eval.score_question(question, [("Indian Penal Code", "379")])

    assert result.precision_at_k == 1.0
    assert result.recall_at_k == 1.0


def test_score_question_no_match_gives_zero_precision_and_recall():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="other",
        expected_act="Nonexistent Act",
        expected_sections=["999"],
    )

    result = run_eval.score_question(question, [("Indian Penal Code", "379")])

    assert result.precision_at_k == 0.0
    assert result.recall_at_k == 0.0


def test_score_question_partial_recall_with_multiple_expected_sections():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["378", "379"],
    )

    result = run_eval.score_question(
        question, [("Indian Penal Code", "379"), ("Hindu Marriage Act", "13")]
    )

    assert result.precision_at_k == 0.5
    assert result.recall_at_k == 0.5


# --- run_retrieval_eval against a real (fixture) hybrid index ----------------


def test_run_retrieval_eval_finds_relevant_section_via_hybrid_retrieval(fixture_indices):
    faiss_index, bm25_index = fixture_indices
    questions = [
        run_eval.EvalQuestion(
            question="What is the punishment for theft under the Indian Penal Code?",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
        )
    ]

    results = run_eval.run_retrieval_eval(questions, faiss_index, bm25_index, top_k=3)

    assert len(results) == 1
    assert results[0].recall_at_k == 1.0
    assert "379" in results[0].retrieved_sections


# --- build_report / aggregate --------------------------------------------------


def test_build_report_computes_aggregate_and_per_domain_means():
    results = [
        run_eval.QuestionResult(
            question="q1",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
            retrieved_sections=["379"],
            precision_at_k=1.0,
            recall_at_k=1.0,
        ),
        run_eval.QuestionResult(
            question="q2",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["304A"],
            retrieved_sections=["379"],
            precision_at_k=0.0,
            recall_at_k=0.0,
        ),
    ]

    report = run_eval.build_report(results, top_k=5)

    assert report["top_k"] == 5
    assert report["question_count"] == 2
    assert report["aggregate"]["mean_precision_at_k"] == 0.5
    assert report["aggregate"]["mean_recall_at_k"] == 0.5
    assert report["per_domain"]["criminal"]["question_count"] == 2
    assert report["per_domain"]["criminal"]["mean_precision_at_k"] == 0.5


# --- main() CLI end-to-end ----------------------------------------------------


def test_main_writes_report_file_and_returns_zero(
    fixture_indices, fixture_dataset_path: Path, tmp_path: Path
):
    faiss_index, bm25_index = fixture_indices
    output_path = tmp_path / "results" / "retrieval_report.json"
    markdown_path = tmp_path / "results" / "eval_report.md"
    csv_path = tmp_path / "results" / "eval_report.csv"

    with (
        patch("eval.run_eval.load_faiss_index", return_value=faiss_index),
        patch("eval.run_eval.load_bm25_index", return_value=bm25_index),
    ):
        exit_code = run_eval.main(
            [
                "--dataset",
                str(fixture_dataset_path),
                "--output",
                str(output_path),
                "--markdown-output",
                str(markdown_path),
                "--csv-output",
                str(csv_path),
                "--top-k",
                "3",
            ]
        )

    assert exit_code == 0
    assert output_path.exists()
    assert markdown_path.exists()
    assert csv_path.exists()

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert report["question_count"] == 3
    assert report["top_k"] == 3
    assert "aggregate" in report
    assert len(report["questions"]) == 3
    assert "answers" not in report

    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert "# AI Legal Assistant" in markdown_text
    assert "## Retrieval metrics" in markdown_text
    assert "## Answer-correctness metrics" not in markdown_text


def test_main_returns_nonzero_when_indices_are_missing(
    fixture_dataset_path: Path, tmp_path: Path
):
    output_path = tmp_path / "results" / "retrieval_report.json"

    with patch(
        "eval.run_eval.load_faiss_index",
        side_effect=FileNotFoundError("no index"),
    ):
        exit_code = run_eval.main(
            ["--dataset", str(fixture_dataset_path), "--output", str(output_path)]
        )

    assert exit_code == 1
    assert not output_path.exists()


# --- T50: score_answer ---------------------------------------------------------


def _legal_answer_response(
    *,
    answer: str = "An answer.",
    confidence_score: float = 0.8,
    is_refusal: bool = False,
    citations: list[SourceCitation] | None = None,
) -> LegalAnswerResponse:
    return LegalAnswerResponse(
        answer=answer,
        confidence_score=confidence_score,
        legal_domain=LegalDomain.CRIMINAL,
        citations=citations or [],
        is_refusal=is_refusal,
        disclaimer="Not legal advice.",
    )


def test_score_answer_full_citation_match_has_no_flags():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["379"],
    )
    response = _legal_answer_response(
        confidence_score=0.9,
        citations=[
            SourceCitation(
                document="Indian Penal Code",
                act_year=1860,
                section="379",
                domain=LegalDomain.CRIMINAL,
                excerpt="theft excerpt",
                retrieval_score=0.9,
            )
        ],
    )

    result = run_eval.score_answer(question, response)

    assert result.citation_precision == 1.0
    assert result.citation_recall == 1.0
    assert result.flags == []


def test_score_answer_flags_unexpected_refusal():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["379"],
    )
    response = _legal_answer_response(is_refusal=True, confidence_score=0.1)

    result = run_eval.score_answer(question, response)

    assert result.flags == [run_eval.UNEXPECTED_REFUSAL_FLAG]


def test_score_answer_flags_confident_wrong_answer():
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["379"],
    )
    response = _legal_answer_response(
        confidence_score=0.9,
        citations=[
            SourceCitation(
                document="Hindu Marriage Act",
                act_year=1955,
                section="13",
                domain=LegalDomain.FAMILY,
                excerpt="unrelated excerpt",
                retrieval_score=0.9,
            )
        ],
    )

    result = run_eval.score_answer(question, response)

    assert result.citation_recall == 0.0
    assert result.flags == [run_eval.CONFIDENT_WRONG_FLAG]


def test_score_answer_no_flag_for_low_confidence_wrong_answer():
    """A low-confidence answer with no correct citation is an expected weak
    result, not a "confidently wrong" one -- it should not be flagged."""
    question = run_eval.EvalQuestion(
        question="q",
        expected_domain="criminal",
        expected_act="Indian Penal Code",
        expected_sections=["379"],
    )
    response = _legal_answer_response(confidence_score=0.3, citations=[])

    result = run_eval.score_answer(question, response)

    assert result.flags == []


# --- T50: run_answer_eval against the real (fixture) RAG chain ----------------


def test_run_answer_eval_scores_a_grounded_answer_from_the_full_chain(fixture_indices):
    faiss_index, bm25_index = fixture_indices
    questions = [
        run_eval.EvalQuestion(
            question="What is the punishment for theft under the Indian Penal Code?",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
        )
    ]
    structured_result = LLMStructuredAnswer(
        answer="Theft is punishable with imprisonment or fine under Section 379.",
        legal_domain=LegalDomain.CRIMINAL,
        used_citation_ids=["IPC 1860, S.379"],
        is_refusal=False,
    )

    results = run_eval.run_answer_eval(
        questions,
        faiss_index,
        bm25_index,
        llm=mock_llm(structured_result),
    )

    assert len(results) == 1
    assert results[0].is_refusal is False
    assert "379" in results[0].cited_sections
    assert results[0].citation_recall == 1.0


# --- T50: build_combined_report / build_markdown_report / write_csv_report ----


def _sample_answer_results() -> list[run_eval.AnswerResult]:
    return [
        run_eval.AnswerResult(
            question="q1",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
            answer="Correct answer.",
            is_refusal=False,
            confidence_score=0.85,
            cited_sections=["379"],
            citation_precision=1.0,
            citation_recall=1.0,
            flags=[],
        ),
        run_eval.AnswerResult(
            question="q2",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["304A"],
            answer="Confidently wrong answer.",
            is_refusal=False,
            confidence_score=0.9,
            cited_sections=["379"],
            citation_precision=0.0,
            citation_recall=0.0,
            flags=[run_eval.CONFIDENT_WRONG_FLAG],
        ),
    ]


def _sample_question_results() -> list[run_eval.QuestionResult]:
    return [
        run_eval.QuestionResult(
            question="q1",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
            retrieved_sections=["379"],
            precision_at_k=1.0,
            recall_at_k=1.0,
        ),
        run_eval.QuestionResult(
            question="q2",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["304A"],
            retrieved_sections=["304A"],
            precision_at_k=1.0,
            recall_at_k=1.0,
        ),
    ]


def test_build_combined_report_adds_answers_section_with_flagged_questions():
    report = run_eval.build_combined_report(
        _sample_question_results(), _sample_answer_results(), top_k=5
    )

    assert "answers" in report
    assert report["answers"]["aggregate"]["flagged_count"] == 1
    assert report["answers"]["aggregate"]["mean_citation_recall"] == 0.5
    assert report["answers"]["per_domain"]["criminal"]["question_count"] == 2
    assert len(report["answers"]["flagged_questions"]) == 1
    assert report["answers"]["flagged_questions"][0]["question"] == "q2"
    assert report["answers"]["flagged_questions"][0]["flags"] == [run_eval.CONFIDENT_WRONG_FLAG]


def test_build_combined_report_omits_answers_section_when_not_run():
    report = run_eval.build_combined_report(_sample_question_results(), None, top_k=5)

    assert "answers" not in report


def test_build_markdown_report_lists_flagged_questions():
    report = run_eval.build_combined_report(
        _sample_question_results(), _sample_answer_results(), top_k=5
    )

    markdown_text = run_eval.build_markdown_report(report)

    assert "## Answer-correctness metrics (full RAG chain)" in markdown_text
    assert "### Flagged questions" in markdown_text
    assert run_eval.CONFIDENT_WRONG_FLAG in markdown_text
    assert "q2" in markdown_text


def test_build_markdown_report_notes_no_flags_when_all_clear():
    clean_answers = [
        run_eval.AnswerResult(
            question="q1",
            expected_domain="criminal",
            expected_act="Indian Penal Code",
            expected_sections=["379"],
            answer="Correct answer.",
            is_refusal=False,
            confidence_score=0.85,
            cited_sections=["379"],
            citation_precision=1.0,
            citation_recall=1.0,
            flags=[],
        )
    ]
    report = run_eval.build_combined_report(
        _sample_question_results()[:1], clean_answers, top_k=5
    )

    markdown_text = run_eval.build_markdown_report(report)

    assert "None -- no unexpected refusals or confidently-wrong answers." in markdown_text


def test_write_csv_report_combines_retrieval_and_answer_rows(tmp_path: Path):
    csv_path = tmp_path / "eval_report.csv"

    run_eval.write_csv_report(csv_path, _sample_question_results(), _sample_answer_results())

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 2
    assert rows[0]["question"] == "q1"
    assert rows[0]["citation_recall"] == "1.0"
    assert rows[1]["flags"] == run_eval.CONFIDENT_WRONG_FLAG


def test_write_csv_report_leaves_answer_columns_blank_when_not_run(tmp_path: Path):
    csv_path = tmp_path / "eval_report.csv"

    run_eval.write_csv_report(csv_path, _sample_question_results(), None)

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    assert rows[0]["citation_recall"] == ""
    assert rows[0]["flags"] == ""


# --- T50: main() --with-answers ------------------------------------------------


def test_main_with_answers_writes_combined_reports(
    fixture_indices, fixture_dataset_path: Path, tmp_path: Path
):
    faiss_index, bm25_index = fixture_indices
    output_path = tmp_path / "results" / "retrieval_report.json"
    markdown_path = tmp_path / "results" / "eval_report.md"
    csv_path = tmp_path / "results" / "eval_report.csv"

    canned_answers = [
        run_eval.AnswerResult(
            question=q.question,
            expected_domain=q.expected_domain,
            expected_act=q.expected_act,
            expected_sections=q.expected_sections,
            answer="An answer.",
            is_refusal=False,
            confidence_score=0.8,
            cited_sections=q.expected_sections,
            citation_precision=1.0,
            citation_recall=1.0,
            flags=[],
        )
        for q in run_eval.load_qa_dataset(fixture_dataset_path)
    ]

    with (
        patch("eval.run_eval.load_faiss_index", return_value=faiss_index),
        patch("eval.run_eval.load_bm25_index", return_value=bm25_index),
        patch("eval.run_eval.run_answer_eval", return_value=canned_answers) as run_answer_eval_mock,
    ):
        exit_code = run_eval.main(
            [
                "--dataset",
                str(fixture_dataset_path),
                "--output",
                str(output_path),
                "--markdown-output",
                str(markdown_path),
                "--csv-output",
                str(csv_path),
                "--with-answers",
                "--user-type",
                "law_student",
            ]
        )

    assert exit_code == 0
    run_answer_eval_mock.assert_called_once()
    assert run_answer_eval_mock.call_args.kwargs["user_type"] == "law_student"

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "answers" in report
    assert report["answers"]["aggregate"]["flagged_count"] == 0

    markdown_text = markdown_path.read_text(encoding="utf-8")
    assert "## Answer-correctness metrics (full RAG chain)" in markdown_text

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["citation_recall"] == "1.0"


def test_main_without_with_answers_flag_never_calls_run_answer_eval(
    fixture_indices, fixture_dataset_path: Path, tmp_path: Path
):
    faiss_index, bm25_index = fixture_indices

    with (
        patch("eval.run_eval.load_faiss_index", return_value=faiss_index),
        patch("eval.run_eval.load_bm25_index", return_value=bm25_index),
        patch("eval.run_eval.run_answer_eval") as run_answer_eval_mock,
    ):
        exit_code = run_eval.main(
            [
                "--dataset",
                str(fixture_dataset_path),
                "--output",
                str(tmp_path / "retrieval_report.json"),
                "--markdown-output",
                str(tmp_path / "eval_report.md"),
                "--csv-output",
                str(tmp_path / "eval_report.csv"),
            ]
        )

    assert exit_code == 0
    run_answer_eval_mock.assert_not_called()
