"""
Offline ingestion: raw bare-act text -> processed JSONL chunks.

Walks ``data/raw/<domain>/*.txt``, runs the section parser (T11), and writes
``data/processed/<domain>.jsonl``. See PLAN.md Section 3 and TASKS.md T12.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.chunking import DEFAULT_MAX_SECTION_CHARS, LegalChunk, parse_act_text
from app.rag.corpus_curation import (
    COW_SOURCE,
    CPA_SOURCE,
    CPC_SOURCE,
    CRPC_SOURCE,
    HMA_SOURCE,
    IDA_SOURCE,
    IPC_SOURCE,
    SMA_SOURCE,
    TPA_SOURCE,
    ActSource,
)

LEGAL_DOMAINS: tuple[str, ...] = (
    "criminal",
    "civil",
    "family",
    "labour",
    "consumer",
    "property",
)

DOMAIN_ACT_SOURCES: dict[str, tuple[ActSource, ...]] = {
    "criminal": (IPC_SOURCE, CRPC_SOURCE),
    "civil": (CPC_SOURCE,),
    "family": (HMA_SOURCE, SMA_SOURCE),
    "labour": (IDA_SOURCE, COW_SOURCE),
    "consumer": (CPA_SOURCE,),
    "property": (TPA_SOURCE,),
}

ACT_BY_FILENAME: dict[str, ActSource] = {
    act.filename: act
    for acts in DOMAIN_ACT_SOURCES.values()
    for act in acts
}

ACT_DOMAIN: dict[str, str] = {
    act.filename: domain
    for domain, acts in DOMAIN_ACT_SOURCES.items()
    for act in acts
}

REQUIRED_CHUNK_FIELDS: tuple[str, ...] = (
    "domain",
    "act_name",
    "act_year",
    "chapter",
    "section_number",
    "section_title",
    "source_citation",
    "text",
)


@dataclass(frozen=True)
class IngestResult:
    """Summary of a single domain ingestion run."""

    domain: str
    output_path: Path
    chunk_count: int
    act_chunk_counts: dict[str, int]


def chunk_to_record(chunk: LegalChunk) -> dict[str, Any]:
    """Serialize a ``LegalChunk`` to a JSON-ready dict (T11 schema)."""
    return {
        "domain": chunk.domain,
        "act_name": chunk.act_name,
        "act_year": chunk.act_year,
        "chapter": chunk.chapter,
        "section_number": chunk.section_number,
        "section_title": chunk.section_title,
        "source_citation": chunk.source_citation,
        "text": chunk.text,
    }


def parse_act_file(
    path: Path,
    *,
    domain: str,
    act: ActSource,
    max_section_chars: int = DEFAULT_MAX_SECTION_CHARS,
) -> list[LegalChunk]:
    """Read a curated act file and return parsed chunks."""
    raw_text = path.read_text(encoding="utf-8")
    return parse_act_text(
        raw_text,
        domain,
        act.act_name,
        act.act_year,
        max_section_chars=max_section_chars,
    )


def write_jsonl(path: Path, chunks: list[LegalChunk]) -> None:
    """Write chunks to JSONL, overwriting any existing file (idempotent)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(chunk_to_record(chunk), ensure_ascii=False) for chunk in chunks]
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8")


def _resolve_act_for_file(domain: str, path: Path) -> ActSource:
    act = ACT_BY_FILENAME.get(path.name)
    if act is None:
        raise ValueError(
            f"Unknown act file {path.name!r} in domain {domain!r}; "
            "expected one of: "
            + ", ".join(
                filename
                for filename, file_domain in ACT_DOMAIN.items()
                if file_domain == domain
            )
        )
    if ACT_DOMAIN[path.name] != domain:
        raise ValueError(
            f"Act file {path.name!r} belongs to domain {ACT_DOMAIN[path.name]!r}, "
            f"not {domain!r}"
        )
    return act


def ingest_domain(
    raw_domain_dir: Path,
    output_path: Path,
    domain: str,
    *,
    max_section_chars: int = DEFAULT_MAX_SECTION_CHARS,
) -> IngestResult:
    """Parse all known act ``.txt`` files in a domain folder and write JSONL."""
    if domain not in DOMAIN_ACT_SOURCES:
        raise ValueError(f"Unsupported domain: {domain!r}")

    expected_files = {act.filename for act in DOMAIN_ACT_SOURCES[domain]}
    present_txt_files = sorted(
        path for path in raw_domain_dir.glob("*.txt") if path.name in expected_files
    )
    missing_files = sorted(expected_files - {path.name for path in present_txt_files})
    if missing_files:
        raise FileNotFoundError(
            f"Missing raw act file(s) for domain {domain!r} under {raw_domain_dir}: "
            + ", ".join(missing_files)
        )

    chunks: list[LegalChunk] = []
    act_chunk_counts: dict[str, int] = {}

    for path in present_txt_files:
        act = _resolve_act_for_file(domain, path)
        act_chunks = parse_act_file(
            path,
            domain=domain,
            act=act,
            max_section_chars=max_section_chars,
        )
        act_chunk_counts[path.name] = len(act_chunks)
        chunks.extend(act_chunks)

    write_jsonl(output_path, chunks)
    return IngestResult(
        domain=domain,
        output_path=output_path,
        chunk_count=len(chunks),
        act_chunk_counts=act_chunk_counts,
    )


def ingest_all(
    raw_root: Path,
    processed_root: Path,
    *,
    max_section_chars: int = DEFAULT_MAX_SECTION_CHARS,
) -> list[IngestResult]:
    """Ingest every configured legal domain under *raw_root*."""
    results: list[IngestResult] = []
    for domain in LEGAL_DOMAINS:
        raw_domain_dir = raw_root / domain
        output_path = processed_root / f"{domain}.jsonl"
        results.append(
            ingest_domain(
                raw_domain_dir,
                output_path,
                domain,
                max_section_chars=max_section_chars,
            )
        )
    return results
