"""
Pydantic v2 contracts for the RAG pipeline's structured output.

Two-schema separation: the LLM only produces `LLMStructuredAnswer` (what it
can honestly know); `confidence_score` on `LegalAnswerResponse` is computed
server-side (see app.rag.confidence) and must never come directly from the
LLM. See PLAN.md Section 6 and TASKS.md T21.
"""

from enum import Enum

from pydantic import BaseModel, Field


class LegalDomain(str, Enum):
    """The 6 supported legal domains, plus a fallback for out-of-scope queries."""

    CRIMINAL = "criminal"
    CIVIL = "civil"
    FAMILY = "family"
    LABOUR = "labour"
    CONSUMER = "consumer"
    PROPERTY = "property"
    OTHER = "other"


# Human-readable labels for the six source domains (excludes `other`).
# Names align with PLAN.md §1.
DOMAIN_LABELS: dict[LegalDomain, str] = {
    LegalDomain.CRIMINAL: "Criminal",
    LegalDomain.CIVIL: "Civil",
    LegalDomain.FAMILY: "Family",
    LegalDomain.LABOUR: "Labour",
    LegalDomain.CONSUMER: "Consumer Protection",
    LegalDomain.PROPERTY: "Property",
}


def supported_domains() -> list[tuple[LegalDomain, str]]:
    """Return the six configured domains with labels, excluding `other`."""
    return [(domain, DOMAIN_LABELS[domain]) for domain in LegalDomain if domain != LegalDomain.OTHER]


class LLMStructuredAnswer(BaseModel):
    """What Gemini itself must return via `.with_structured_output(...)`.

    Deliberately excludes a numeric confidence field -- see module docstring.
    """

    answer: str
    legal_domain: LegalDomain
    used_citation_ids: list[str] = Field(default_factory=list)
    is_refusal: bool = False


class SourceCitation(BaseModel):
    """A single source citation, assembled server-side from retrieved chunks
    (never fabricated by the LLM)."""

    document: str
    act_year: int | None = None
    section: str
    domain: LegalDomain
    excerpt: str
    retrieval_score: float


class LegalAnswerResponse(BaseModel):
    """Final API response contract returned to the frontend."""

    answer: str
    confidence_score: float = Field(ge=0, le=1)
    legal_domain: LegalDomain
    citations: list[SourceCitation] = Field(default_factory=list)
    is_refusal: bool = False
    disclaimer: str
