"""
CLI: computes retrieval precision/recall@k and answer-correctness against
eval/qa_dataset.jsonl, producing a report under eval/results/.

See PLAN.md Section 11 and TASKS.md T49-T50.

Usage:
    python eval/run_eval.py
"""


def main() -> None:
    """Entry point for the evaluation CLI.

    TODO: implement retrieval-only precision/recall@k scoring (T49), then
    extend with full RAG-chain answer-correctness scoring and a combined
    summary report (T50).
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
