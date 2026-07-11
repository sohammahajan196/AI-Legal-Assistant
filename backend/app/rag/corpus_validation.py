"""
Corpus QA for processed JSONL chunks.

Validates ingested chunks for empty text, missing metadata, and duplicate
section numbers within an act. See PLAN.md Section 3 and TASKS.md T13.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.rag.ingestion import LEGAL_DOMAINS, REQUIRED_CHUNK_FIELDS

# Fields that must be present and non-empty on every chunk record.
REQUIRED_NON_EMPTY_FIELDS: tuple[str, ...] = (
    "domain",
    "act_name",
    "section_number",
    "source_citation",
    "text",
)

_SUBCLAUSE_START_RE = re.compile(r"^\(\d+\)")


@dataclass(frozen=True)
class ChunkIssue:
    """A single validation failure for one JSONL line."""

    domain: str
    line_number: int
    act_name: str | None
    section_number: str | None
    message: str


@dataclass(frozen=True)
class DomainValidationResult:
    """Validation outcome for one domain JSONL file."""

    domain: str
    path: Path
    chunk_count: int
    issues: tuple[ChunkIssue, ...]


@dataclass(frozen=True)
class CorpusValidationReport:
    """Validation outcome across all configured domains."""

    results: tuple[DomainValidationResult, ...]

    @property
    def ok(self) -> bool:
        return all(not result.issues for result in self.results)

    @property
    def total_chunks(self) -> int:
        return sum(result.chunk_count for result in self.results)

    @property
    def total_issues(self) -> int:
        return sum(len(result.issues) for result in self.results)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def _starts_with_subclause(text: str) -> bool:
    return bool(_SUBCLAUSE_START_RE.match(text.strip()))


def load_jsonl_records(path: Path) -> list[tuple[int, dict[str, Any]]]:
    """Load JSONL records as ``(line_number, record)`` pairs."""
    records: list[tuple[int, dict[str, Any]]] = []
    content = path.read_text(encoding="utf-8")
    for line_number, line in enumerate(content.splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_number}: expected JSON object per line")
        records.append((line_number, record))
    return records


def validate_chunk_record(
    record: dict[str, Any],
    *,
    line_number: int,
    domain: str,
) -> list[ChunkIssue]:
    """Return validation issues for a single chunk record."""
    issues: list[ChunkIssue] = []
    act_name = record.get("act_name")
    section_number = record.get("section_number")

    def _issue(message: str) -> ChunkIssue:
        return ChunkIssue(
            domain=domain,
            line_number=line_number,
            act_name=act_name if isinstance(act_name, str) else None,
            section_number=section_number if isinstance(section_number, str) else None,
            message=message,
        )

    missing_fields = [field for field in REQUIRED_CHUNK_FIELDS if field not in record]
    if missing_fields:
        issues.append(_issue(f"missing metadata field(s): {', '.join(missing_fields)}"))

    for field in REQUIRED_NON_EMPTY_FIELDS:
        if field in record and _is_empty(record[field]):
            issues.append(_issue(f"empty required field: {field}"))

    if "act_year" in record and record["act_year"] is None:
        issues.append(_issue("empty required field: act_year"))

    if "domain" in record and record["domain"] != domain:
        issues.append(
            _issue(
                f"domain mismatch: record has {record['domain']!r}, expected {domain!r}"
            )
        )

    return issues


def _find_duplicate_section_issues(
    records: list[tuple[int, dict[str, Any]]],
    *,
    domain: str,
) -> list[ChunkIssue]:
    """Detect duplicate section numbers within the same act."""
    grouped: dict[tuple[str, int, str], list[tuple[int, str]]] = {}

    for line_number, record in records:
        act_name = record.get("act_name")
        act_year = record.get("act_year")
        section_number = record.get("section_number")
        text = record.get("text")

        if (
            not isinstance(act_name, str)
            or not isinstance(act_year, int)
            or not isinstance(section_number, str)
            or not isinstance(text, str)
        ):
            continue

        key = (act_name, act_year, section_number)
        grouped.setdefault(key, []).append((line_number, text.strip()))

    issues: list[ChunkIssue] = []
    for (act_name, _act_year, section_number), chunks in sorted(grouped.items()):
        if len(chunks) <= 1:
            continue

        seen_text: dict[str, int] = {}
        for line_number, text in chunks:
            if text in seen_text:
                issues.append(
                    ChunkIssue(
                        domain=domain,
                        line_number=line_number,
                        act_name=act_name,
                        section_number=section_number,
                        message=(
                            "duplicate section within act: identical text also appears on "
                            f"line {seen_text[text]}"
                        ),
                    )
                )
            else:
                seen_text[text] = line_number

        non_subclause_lines = [
            line_number for line_number, text in chunks if not _starts_with_subclause(text)
        ]
        if len(non_subclause_lines) > 1:
            line_list = ", ".join(str(line) for line in non_subclause_lines)
            issues.append(
                ChunkIssue(
                    domain=domain,
                    line_number=non_subclause_lines[1],
                    act_name=act_name,
                    section_number=section_number,
                    message=(
                        "duplicate section number within act: multiple full-section chunks "
                        f"on lines {line_list}"
                    ),
                )
            )

    return issues


def validate_domain_file(path: Path, domain: str) -> DomainValidationResult:
    """Validate one ``<domain>.jsonl`` processed corpus file."""
    if not path.exists():
        return DomainValidationResult(
            domain=domain,
            path=path,
            chunk_count=0,
            issues=(
                ChunkIssue(
                    domain=domain,
                    line_number=0,
                    act_name=None,
                    section_number=None,
                    message=f"missing processed corpus file: {path}",
                ),
            ),
        )

    records = load_jsonl_records(path)
    issues: list[ChunkIssue] = []

    for line_number, record in records:
        issues.extend(
            validate_chunk_record(record, line_number=line_number, domain=domain)
        )

    issues.extend(_find_duplicate_section_issues(records, domain=domain))

    return DomainValidationResult(
        domain=domain,
        path=path,
        chunk_count=len(records),
        issues=tuple(issues),
    )


def validate_corpus(processed_root: Path) -> CorpusValidationReport:
    """Validate all configured domain JSONL files under *processed_root*."""
    results = [
        validate_domain_file(processed_root / f"{domain}.jsonl", domain)
        for domain in LEGAL_DOMAINS
    ]
    return CorpusValidationReport(results=tuple(results))


def format_validation_report(report: CorpusValidationReport) -> str:
    """Render a human-readable validation summary."""
    lines = ["Corpus validation report", ""]

    for result in report.results:
        status = "OK" if not result.issues else f"{len(result.issues)} issue(s)"
        lines.append(f"{result.domain}: {result.chunk_count} chunks — {status}")

    lines.append("")
    lines.append(f"Total chunks: {report.total_chunks}")

    if report.ok:
        lines.append("Result: PASS")
        return "\n".join(lines)

    lines.extend(["", "Issues:", ""])
    for result in report.results:
        for issue in result.issues:
            act_label = issue.act_name or "unknown act"
            section_label = issue.section_number or "?"
            location = (
                f"line {issue.line_number}"
                if issue.line_number
                else str(result.path)
            )
            lines.append(
                f"- {issue.domain} [{location}] {act_label} S.{section_label}: "
                f"{issue.message}"
            )

    lines.append("")
    lines.append(f"Result: FAIL ({report.total_issues} issue(s))")
    return "\n".join(lines)
