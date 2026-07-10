"""
Consent-aware audit logging to the `query_logs` table.

See PLAN.md Section 10 and TASKS.md T36.
"""


def log_query(
    token_hash: str,
    query: str,
    consent_to_log: bool,
    retrieved_chunk_ids: list[str],
    confidence_score: float,
    latency_ms: float,
    model_used: str,
) -> None:
    """Persist a query log entry.

    Stores the raw `query` text only if `consent_to_log` is True; otherwise
    only a hash is stored. Must catch and swallow its own failures so
    logging never fails the parent request (see database.mdc).

    TODO: implement using the same SQLite database as app.services.session_store.
    """
    raise NotImplementedError
