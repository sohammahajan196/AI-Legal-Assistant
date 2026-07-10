"""
GET /api/v1/domains - lists the supported legal domains.

See PLAN.md Section 1 and TASKS.md T39.
"""

from fastapi import APIRouter

router = APIRouter(tags=["domains"])

# TODO: define GET /domains returning the app.schemas.legal_answer.LegalDomain
# enum values (excluding "other") with human-readable labels. Must require
# app.core.security.verify_bearer_token.
