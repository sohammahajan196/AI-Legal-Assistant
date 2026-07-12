"""Unit tests for app.schemas.legal_answer. See TASKS.md T21."""

import pytest
from pydantic import ValidationError

from app.schemas.legal_answer import (
    LLMStructuredAnswer,
    LegalAnswerResponse,
    LegalDomain,
    SourceCitation,
)

EXPECTED_DOMAINS = {
    "criminal",
    "civil",
    "family",
    "labour",
    "consumer",
    "property",
    "other",
}

DISCLAIMER = (
    "This is not a substitute for licensed legal counsel. "
    "Consult a qualified lawyer for advice on your specific situation."
)


def test_legal_domain_contains_six_domains_plus_other():
    """LegalDomain enum must expose exactly the 6 supported domains and `other`."""
    assert {member.value for member in LegalDomain} == EXPECTED_DOMAINS
    assert len(LegalDomain) == 7


@pytest.mark.parametrize("domain", list(LegalDomain))
def test_llm_structured_answer_validates_for_each_domain(domain: LegalDomain):
    """LLMStructuredAnswer accepts representative data for every domain value."""
    answer = LLMStructuredAnswer(
        answer="Section 378 defines theft as dishonestly taking movable property.",
        legal_domain=domain,
        used_citation_ids=["ipc-378-chunk-0"],
        is_refusal=False,
    )

    assert answer.legal_domain == domain
    assert answer.used_citation_ids == ["ipc-378-chunk-0"]
    assert answer.is_refusal is False


def test_llm_structured_answer_defaults():
    """Optional LLM fields default to empty citations list and non-refusal."""
    answer = LLMStructuredAnswer(
        answer="Insufficient information in the retrieved sources.",
        legal_domain=LegalDomain.OTHER,
    )

    assert answer.used_citation_ids == []
    assert answer.is_refusal is False


def test_source_citation_validates_with_representative_data():
    """SourceCitation accepts server-assembled citation metadata."""
    citation = SourceCitation(
        document="Indian Penal Code, 1860",
        act_year=1860,
        section="378",
        domain=LegalDomain.CRIMINAL,
        excerpt="Whoever, intending to take dishonestly any movable property...",
        retrieval_score=0.87,
    )

    assert citation.document == "Indian Penal Code, 1860"
    assert citation.act_year == 1860
    assert citation.section == "378"
    assert citation.domain == LegalDomain.CRIMINAL
    assert citation.retrieval_score == pytest.approx(0.87)


def test_source_citation_allows_null_act_year():
    """act_year is optional when the source document year is unknown."""
    citation = SourceCitation(
        document="Unknown Gazette Notification",
        act_year=None,
        section="N/A",
        domain=LegalDomain.OTHER,
        excerpt="...",
        retrieval_score=0.5,
    )

    assert citation.act_year is None


def test_legal_answer_response_validates_with_representative_data():
    """LegalAnswerResponse accepts a full API payload with nested citations."""
    response = LegalAnswerResponse(
        answer="Theft is defined under Section 378 of the IPC.",
        confidence_score=0.82,
        legal_domain=LegalDomain.CRIMINAL,
        citations=[
            SourceCitation(
                document="Indian Penal Code, 1860",
                act_year=1860,
                section="378",
                domain=LegalDomain.CRIMINAL,
                excerpt="Whoever, intending to take dishonestly any movable property...",
                retrieval_score=0.87,
            )
        ],
        is_refusal=False,
        disclaimer=DISCLAIMER,
    )

    assert response.confidence_score == pytest.approx(0.82)
    assert len(response.citations) == 1
    assert response.disclaimer == DISCLAIMER


def test_legal_answer_response_defaults():
    """Optional API fields default to empty citations and non-refusal."""
    response = LegalAnswerResponse(
        answer="I cannot answer based on the retrieved sources.",
        confidence_score=0.0,
        legal_domain=LegalDomain.OTHER,
        disclaimer=DISCLAIMER,
        is_refusal=True,
    )

    assert response.citations == []
    assert response.is_refusal is True


@pytest.mark.parametrize("invalid_score", [-0.01, 1.01, -1.0, 2.0])
def test_confidence_score_rejects_out_of_range(invalid_score: float):
    """confidence_score must stay within [0, 1]."""
    with pytest.raises(ValidationError) as exc_info:
        LegalAnswerResponse(
            answer="Test answer.",
            confidence_score=invalid_score,
            legal_domain=LegalDomain.CIVIL,
            disclaimer=DISCLAIMER,
        )

    assert "confidence_score" in str(exc_info.value)


@pytest.mark.parametrize("valid_score", [0.0, 1.0, 0.5])
def test_confidence_score_accepts_boundary_values(valid_score: float):
    """confidence_score accepts the inclusive 0 and 1 endpoints."""
    response = LegalAnswerResponse(
        answer="Test answer.",
        confidence_score=valid_score,
        legal_domain=LegalDomain.CIVIL,
        disclaimer=DISCLAIMER,
    )

    assert response.confidence_score == pytest.approx(valid_score)


def test_invalid_legal_domain_string_rejected():
    """Unknown domain strings must fail enum validation."""
    with pytest.raises(ValidationError) as exc_info:
        LLMStructuredAnswer(
            answer="Test.",
            legal_domain="tax",  # type: ignore[arg-type]
        )

    assert "legal_domain" in str(exc_info.value)
