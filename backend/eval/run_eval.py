"""
CLI: computes retrieval precision/recall@k against eval/qa_dataset.jsonl,
optionally also running each question through the full RAG chain to score
answer correctness, producing JSON/Markdown/CSV reports under eval/results/.

See PLAN.md Section 11 and TASKS.md T49-T50.

Two modes:

- Retrieval-only (default; no LLM/API calls) -- queries the already-built
  FAISS + BM25 indices (see scripts/ingest.py, scripts/build_index.py,
  TASKS.md T17) and scores each hit's (act, section) identifier against the
  dataset's `expected_sections`.
- `--with-answers` additionally runs each question through the full RAG
  chain (app.rag.chain.run_rag_chain, T30) and scores citation overlap on the
  final answer, flagging unexpected refusals and confidently-wrong answers.
  This mode makes real LLM calls and requires a configured Gemini API key.

Usage (from backend/):
    python eval/run_eval.py
    python eval/run_eval.py --top-k 10
    python eval/run_eval.py --with-answers --user-type lawyer
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import settings  # noqa: E402
from app.rag.bm25_index import load_bm25_index  # noqa: E402
from app.rag.chain import run_rag_chain_sync  # noqa: E402
from app.rag.embeddings import get_embedding_model  # noqa: E402
from app.rag.hybrid_retriever import HybridQueryResult, query_hybrid_index  # noqa: E402
from app.rag.vectorstore import load_faiss_index  # noqa: E402
from app.schemas.legal_answer import LegalAnswerResponse  # noqa: E402

DEFAULT_DATASET_PATH = Path(__file__).resolve().parent / "qa_dataset.jsonl"
RESULTS_DIR = Path(__file__).resolve().parent / "results"
DEFAULT_REPORT_PATH = RESULTS_DIR / "retrieval_report.json"
DEFAULT_MARKDOWN_REPORT_PATH = RESULTS_DIR / "eval_report.md"
DEFAULT_CSV_REPORT_PATH = RESULTS_DIR / "eval_report.csv"
DEFAULT_TOP_K = 5
DEFAULT_USER_TYPE = "lawyer"

UNEXPECTED_REFUSAL_FLAG = "unexpected_refusal"
CONFIDENT_WRONG_FLAG = "confident_wrong_answer"


@dataclass(frozen=True)
class EvalQuestion:
    """One hand-written question from qa_dataset.jsonl (T48)."""

    question: str
    expected_domain: str
    expected_act: str | None
    expected_sections: list[str]


@dataclass(frozen=True)
class QuestionResult:
    """Precision/recall@k for a single eval question."""

    question: str
    expected_domain: str
    expected_act: str | None
    expected_sections: list[str]
    retrieved_sections: list[str]
    precision_at_k: float
    recall_at_k: float


def load_qa_dataset(path: Path) -> list[EvalQuestion]:
    """Parse qa_dataset.jsonl into `EvalQuestion` records."""
    questions: list[EvalQuestion] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            try:
                questions.append(
                    EvalQuestion(
                        question=record["question"],
                        expected_domain=record["expected_domain"],
                        expected_act=record.get("expected_act"),
                        expected_sections=list(record["expected_sections"]),
                    )
                )
            except KeyError as exc:
                raise ValueError(f"{path}:{line_number}: missing required field {exc}") from exc
    return questions


def _relevant_set(question: EvalQuestion) -> set[tuple[str | None, str]]:
    """The (act, section) identifiers that count as a relevant retrieval hit."""
    return {(question.expected_act, section) for section in question.expected_sections}


def _retrieved_identifiers(results: list[HybridQueryResult]) -> list[tuple[str, str]]:
    return [(result.act_name, result.section_number) for result in results]


def score_question(question: EvalQuestion, retrieved: list[tuple[str, str]]) -> QuestionResult:
    """Compute precision@k/recall@k for one question given its top-k retrieval hits."""
    relevant = _relevant_set(question)
    true_positives = len(relevant & set(retrieved))

    precision = true_positives / len(retrieved) if retrieved else 0.0
    recall = true_positives / len(relevant) if relevant else 0.0

    return QuestionResult(
        question=question.question,
        expected_domain=question.expected_domain,
        expected_act=question.expected_act,
        expected_sections=question.expected_sections,
        retrieved_sections=[section for _, section in retrieved],
        precision_at_k=round(precision, 4),
        recall_at_k=round(recall, 4),
    )


def run_retrieval_eval(
    questions: list[EvalQuestion],
    faiss_index,
    bm25_index,
    top_k: int,
) -> list[QuestionResult]:
    """Run every question through the hybrid retrieval layer (T18) and score it."""
    results: list[QuestionResult] = []
    for question in questions:
        hits = query_hybrid_index(faiss_index, bm25_index, question.question, k=top_k)
        results.append(score_question(question, _retrieved_identifiers(hits)))
    return results


def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 4) if values else 0.0


def _per_domain_aggregate(results: list[QuestionResult]) -> dict[str, dict[str, float]]:
    domains = sorted({result.expected_domain for result in results})
    return {
        domain: {
            "mean_precision_at_k": _mean(
                [r.precision_at_k for r in results if r.expected_domain == domain]
            ),
            "mean_recall_at_k": _mean(
                [r.recall_at_k for r in results if r.expected_domain == domain]
            ),
            "question_count": sum(1 for r in results if r.expected_domain == domain),
        }
        for domain in domains
    }


def build_report(results: list[QuestionResult], top_k: int) -> dict:
    """Assemble the JSON-serializable retrieval-only report (T49)."""
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "top_k": top_k,
        "question_count": len(results),
        "aggregate": {
            "mean_precision_at_k": _mean([r.precision_at_k for r in results]),
            "mean_recall_at_k": _mean([r.recall_at_k for r in results]),
        },
        "per_domain": _per_domain_aggregate(results),
        "questions": [asdict(r) for r in results],
    }


def print_report(report: dict) -> None:
    """Print per-question and aggregate precision/recall@k to stdout."""
    top_k = report["top_k"]
    for q in report["questions"]:
        print(
            f"[{q['expected_domain']}] P@{top_k}={q['precision_at_k']:.2f} "
            f"R@{top_k}={q['recall_at_k']:.2f} - {q['question']}"
        )

    print("")
    print(f"Aggregate over {report['question_count']} questions (top_k={top_k}):")
    print(f"  mean precision@k = {report['aggregate']['mean_precision_at_k']:.4f}")
    print(f"  mean recall@k    = {report['aggregate']['mean_recall_at_k']:.4f}")
    print("")
    print("Per-domain:")
    for domain, stats in report["per_domain"].items():
        print(
            f"  {domain}: precision@k={stats['mean_precision_at_k']:.4f} "
            f"recall@k={stats['mean_recall_at_k']:.4f} (n={stats['question_count']})"
        )


# --- T50: full-RAG-chain answer-correctness scoring --------------------------


@dataclass(frozen=True)
class AnswerResult:
    """Full-RAG-chain answer correctness for a single eval question (T50)."""

    question: str
    expected_domain: str
    expected_act: str | None
    expected_sections: list[str]
    answer: str
    is_refusal: bool
    confidence_score: float
    cited_sections: list[str]
    citation_precision: float
    citation_recall: float
    flags: list[str]


def score_answer(question: EvalQuestion, response: LegalAnswerResponse) -> AnswerResult:
    """Score one full-chain answer's citations against `expected_sections`,
    and flag outcomes worth a human double-check (T50 acceptance criteria):
    an unexpected refusal, or a confident answer with no correct citation."""
    relevant = _relevant_set(question)
    cited = [(citation.document, citation.section) for citation in response.citations]
    true_positives = len(relevant & set(cited))

    citation_precision = true_positives / len(cited) if cited else 0.0
    citation_recall = true_positives / len(relevant) if relevant else 0.0

    flags: list[str] = []
    if response.is_refusal:
        flags.append(UNEXPECTED_REFUSAL_FLAG)
    elif (
        response.confidence_score >= settings.confidence_caution_threshold
        and citation_recall == 0.0
    ):
        flags.append(CONFIDENT_WRONG_FLAG)

    return AnswerResult(
        question=question.question,
        expected_domain=question.expected_domain,
        expected_act=question.expected_act,
        expected_sections=question.expected_sections,
        answer=response.answer,
        is_refusal=response.is_refusal,
        confidence_score=round(response.confidence_score, 4),
        cited_sections=[section for _, section in cited],
        citation_precision=round(citation_precision, 4),
        citation_recall=round(citation_recall, 4),
        flags=flags,
    )


def run_answer_eval(
    questions: list[EvalQuestion],
    faiss_index,
    bm25_index,
    *,
    user_type: str = DEFAULT_USER_TYPE,
    llm: object | None = None,
) -> list[AnswerResult]:
    """Run every question through the full RAG chain (T30) and score the answer.

    Makes a real LLM call per question via `run_rag_chain_sync` unless a test
    injects `llm` (mirrors the override hooks `app.rag.chain` exposes for
    tests). Only reached when the caller opts into `--with-answers`; T49's
    retrieval-only mode never calls this function.
    """
    results: list[AnswerResult] = []
    for question in questions:
        response = run_rag_chain_sync(
            question.question,
            session_id=None,
            user_type=user_type,
            history=[],
            llm=llm,
            faiss_index=faiss_index,
            bm25_index=bm25_index,
        )
        results.append(score_answer(question, response))
    return results


def _answer_per_domain_aggregate(results: list[AnswerResult]) -> dict[str, dict[str, float]]:
    domains = sorted({result.expected_domain for result in results})
    return {
        domain: {
            "mean_citation_precision": _mean(
                [r.citation_precision for r in results if r.expected_domain == domain]
            ),
            "mean_citation_recall": _mean(
                [r.citation_recall for r in results if r.expected_domain == domain]
            ),
            "refusal_count": sum(
                1 for r in results if r.expected_domain == domain and r.is_refusal
            ),
            "question_count": sum(1 for r in results if r.expected_domain == domain),
        }
        for domain in domains
    }


def build_combined_report(
    retrieval_results: list[QuestionResult],
    answer_results: list[AnswerResult] | None,
    top_k: int,
) -> dict:
    """Extend the T49 retrieval-only report with T50's answer-correctness
    section, keyed under `answers`, when full-chain scoring was run."""
    report = build_report(retrieval_results, top_k)
    if answer_results is None:
        return report

    flagged = [
        {"question": r.question, "expected_domain": r.expected_domain, "flags": r.flags}
        for r in answer_results
        if r.flags
    ]
    report["answers"] = {
        "aggregate": {
            "mean_citation_precision": _mean([r.citation_precision for r in answer_results]),
            "mean_citation_recall": _mean([r.citation_recall for r in answer_results]),
            "refusal_count": sum(1 for r in answer_results if r.is_refusal),
            "flagged_count": len(flagged),
        },
        "per_domain": _answer_per_domain_aggregate(answer_results),
        "flagged_questions": flagged,
        "questions": [asdict(r) for r in answer_results],
    }
    return report


def print_answer_summary(report: dict) -> None:
    """Print the T50 answer-correctness aggregate and any flagged questions."""
    answers = report.get("answers")
    if not answers:
        return

    print("")
    print("Answer-correctness (full RAG chain):")
    print(f"  mean citation precision = {answers['aggregate']['mean_citation_precision']:.4f}")
    print(f"  mean citation recall    = {answers['aggregate']['mean_citation_recall']:.4f}")
    print(f"  refusals = {answers['aggregate']['refusal_count']} / {report['question_count']}")

    if answers["flagged_questions"]:
        print("")
        print(f"Flagged questions ({answers['aggregate']['flagged_count']}):")
        for item in answers["flagged_questions"]:
            print(f"  [{', '.join(item['flags'])}] ({item['expected_domain']}) {item['question']}")
    else:
        print("  No flagged questions.")


def build_markdown_report(report: dict) -> str:
    """Render the combined report as a human-readable Markdown summary."""
    lines = [
        "# AI Legal Assistant -- Evaluation Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Questions: {report['question_count']}",
        f"- top_k: {report['top_k']}",
        "",
        "## Retrieval metrics",
        "",
        f"- Mean precision@k: **{report['aggregate']['mean_precision_at_k']:.4f}**",
        f"- Mean recall@k: **{report['aggregate']['mean_recall_at_k']:.4f}**",
        "",
        "| Domain | Precision@k | Recall@k | Questions |",
        "|---|---|---|---|",
    ]
    for domain, stats in report["per_domain"].items():
        lines.append(
            f"| {domain} | {stats['mean_precision_at_k']:.4f} | "
            f"{stats['mean_recall_at_k']:.4f} | {stats['question_count']} |"
        )

    answers = report.get("answers")
    if answers:
        lines += [
            "",
            "## Answer-correctness metrics (full RAG chain)",
            "",
            f"- Mean citation precision: **{answers['aggregate']['mean_citation_precision']:.4f}**",
            f"- Mean citation recall: **{answers['aggregate']['mean_citation_recall']:.4f}**",
            f"- Refusals: **{answers['aggregate']['refusal_count']}** / {report['question_count']}",
            f"- Flagged questions: **{answers['aggregate']['flagged_count']}**",
            "",
            "| Domain | Citation precision | Citation recall | Refusals | Questions |",
            "|---|---|---|---|---|",
        ]
        for domain, stats in answers["per_domain"].items():
            lines.append(
                f"| {domain} | {stats['mean_citation_precision']:.4f} | "
                f"{stats['mean_citation_recall']:.4f} | {stats['refusal_count']} | "
                f"{stats['question_count']} |"
            )

        lines += ["", "### Flagged questions", ""]
        if answers["flagged_questions"]:
            lines += ["| Domain | Flags | Question |", "|---|---|---|"]
            for item in answers["flagged_questions"]:
                lines.append(
                    f"| {item['expected_domain']} | {', '.join(item['flags'])} | {item['question']} |"
                )
        else:
            lines.append("None -- no unexpected refusals or confidently-wrong answers.")

    return "\n".join(lines) + "\n"


def write_csv_report(
    path: Path,
    retrieval_results: list[QuestionResult],
    answer_results: list[AnswerResult] | None,
) -> None:
    """Write one row per question combining retrieval and (if run) answer metrics."""
    answers_by_question = {result.question: result for result in (answer_results or [])}
    fieldnames = [
        "question",
        "expected_domain",
        "expected_act",
        "expected_sections",
        "retrieved_sections",
        "precision_at_k",
        "recall_at_k",
        "answer_is_refusal",
        "answer_confidence_score",
        "cited_sections",
        "citation_precision",
        "citation_recall",
        "flags",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in retrieval_results:
            answer = answers_by_question.get(result.question)
            writer.writerow(
                {
                    "question": result.question,
                    "expected_domain": result.expected_domain,
                    "expected_act": result.expected_act or "",
                    "expected_sections": ";".join(result.expected_sections),
                    "retrieved_sections": ";".join(result.retrieved_sections),
                    "precision_at_k": result.precision_at_k,
                    "recall_at_k": result.recall_at_k,
                    "answer_is_refusal": answer.is_refusal if answer else "",
                    "answer_confidence_score": answer.confidence_score if answer else "",
                    "cited_sections": ";".join(answer.cited_sections) if answer else "",
                    "citation_precision": answer.citation_precision if answer else "",
                    "citation_recall": answer.citation_recall if answer else "",
                    "flags": ";".join(answer.flags) if answer else "",
                }
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-output", type=Path, default=DEFAULT_MARKDOWN_REPORT_PATH)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_REPORT_PATH)
    parser.add_argument("--top-k", type=int, default=DEFAULT_TOP_K)
    parser.add_argument(
        "--with-answers",
        action="store_true",
        help=(
            "Also run each question through the full RAG chain (T30) and score "
            "answer correctness. Makes real LLM calls -- requires a configured "
            "Gemini API key."
        ),
    )
    parser.add_argument(
        "--user-type",
        default=DEFAULT_USER_TYPE,
        choices=["layperson", "law_student", "lawyer"],
        help="user_type passed to the RAG chain when --with-answers is set.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Entry point for the evaluation CLI (T49 retrieval scoring, T50
    optional full-chain answer-correctness scoring)."""
    args = parse_args(argv)

    questions = load_qa_dataset(args.dataset)
    if not questions:
        print(f"No questions found in {args.dataset}", file=sys.stderr)
        return 1

    try:
        faiss_index = load_faiss_index(settings.faiss_index_dir, get_embedding_model())
        bm25_index = load_bm25_index(settings.bm25_index_dir)
    except FileNotFoundError as exc:
        print(
            f"{exc}\nBuild the indices first: python scripts/ingest.py && "
            "python scripts/build_index.py",
            file=sys.stderr,
        )
        return 1

    retrieval_results = run_retrieval_eval(questions, faiss_index, bm25_index, args.top_k)

    answer_results: list[AnswerResult] | None = None
    if args.with_answers:
        answer_results = run_answer_eval(
            questions, faiss_index, bm25_index, user_type=args.user_type
        )

    report = build_combined_report(retrieval_results, answer_results, args.top_k)

    print_report(report)
    print_answer_summary(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nJSON report written to {args.output}")

    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(build_markdown_report(report), encoding="utf-8")
    print(f"Markdown report written to {args.markdown_output}")

    write_csv_report(args.csv_output, retrieval_results, answer_results)
    print(f"CSV report written to {args.csv_output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
