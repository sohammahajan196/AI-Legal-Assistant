"""
GET /api/v1/domains - lists the supported legal domains.

See PLAN.md Section 1 and TASKS.md T39.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import verify_bearer_token
from app.schemas.legal_answer import LegalDomain, supported_domains

router = APIRouter(tags=["domains"])


class DomainOption(BaseModel):
    """One selectable legal domain for the frontend."""

    value: LegalDomain
    label: str


class DomainsResponse(BaseModel):
    """Response payload for GET /api/v1/domains."""

    domains: list[DomainOption]


@router.get("/domains", response_model=DomainsResponse)
async def list_domains(
    _token: str = Depends(verify_bearer_token),
) -> DomainsResponse:
    """Return the six supported legal domains with human-readable labels."""
    return DomainsResponse(
        domains=[
            DomainOption(value=domain, label=label)
            for domain, label in supported_domains()
        ]
    )
