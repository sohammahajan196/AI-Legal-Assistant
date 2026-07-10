"""
CLI: runs corpus validation, then builds both the FAISS and BM25 index
artifacts in one command.

See PLAN.md Section 3 and TASKS.md T17.

Usage:
    python scripts/build_index.py
"""


def main() -> None:
    """Entry point for the combined index-build CLI.

    TODO: call scripts.validate_corpus.main(), then
    app.rag.vectorstore.build_faiss_index and
    app.rag.bm25_index.build_bm25_index. Must abort with a clear error if
    validation fails.
    """
    raise NotImplementedError


if __name__ == "__main__":
    main()
