"""
Section-boundary parser and metadata extractor.

Splits raw bare-act text into per-section chunks (not fixed token windows),
attaching domain/act/chapter/section metadata for citation purposes.
See PLAN.md Section 3 and TASKS.md T11.
"""

from dataclasses import dataclass


@dataclass
class LegalChunk:
    """A single citable chunk of legal text with its source metadata."""

    domain: str
    act_name: str
    act_year: int | None
    chapter: str | None
    section_number: str
    section_title: str | None
    source_citation: str
    text: str


def parse_act_text(raw_text: str, domain: str, act_name: str) -> list[LegalChunk]:
    """Parse raw act text into a list of `LegalChunk` objects.

    TODO: implement regex-based section-boundary detection (e.g. "Section N.")
    plus sub-clause splitting ("(1)", "(2)") for oversized sections, per
    TASKS.md T11 acceptance criteria.
    """
    raise NotImplementedError
