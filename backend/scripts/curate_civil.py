"""
Curate civil-domain raw bare-act text (CPC 1908).

Downloads the official India Code PDF, extracts text with pdfplumber, normalizes
section headers to `Section N.` format, and writes UTF-8 `.txt` under
`data/raw/civil/`. See PLAN.md Section 3 and TASKS.md T06.

Usage (from backend/):
    python scripts/curate_civil.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.corpus_curation import (  # noqa: E402
    CPC_SOURCE,
    curate_act_text,
    extract_pdf_text,
    render_sources_markdown,
    validate_curated_text,
)

OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "civil"


def _download_pdf(client: httpx.Client, url: str) -> bytes:
    response = client.get(
        url,
        follow_redirects=True,
        timeout=120.0,
        headers={"User-Agent": "AI-Legal-Assistant-Corpus-Curator/1.0"},
    )
    if response.status_code != 200:
        response.raise_for_status()
    if not response.content.startswith(b"%PDF"):
        raise ValueError(f"Expected PDF from {url}, got {len(response.content)} bytes without %PDF header")
    return response.content


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    retrieval_date = date.today()

    with httpx.Client() as client:
        print(f"Downloading {CPC_SOURCE.act_name} ({CPC_SOURCE.act_year}) …")
        pdf_bytes = _download_pdf(client, CPC_SOURCE.pdf_url)

        print(f"Extracting and normalizing {CPC_SOURCE.filename} …")
        raw_text = extract_pdf_text(pdf_bytes)
        curated = curate_act_text(raw_text, CPC_SOURCE)
        validate_curated_text(curated, min_sections=100)

        output_path = OUTPUT_DIR / CPC_SOURCE.filename
        output_path.write_text(curated, encoding="utf-8")
        print(f"Wrote {output_path} ({len(curated.splitlines())} lines)")

    sources_md = render_sources_markdown(
        retrieval_date=retrieval_date,
        acts=[(CPC_SOURCE, output_path)],
        domain_title="Civil domain",
        task_note="T06",
        extra_notes=[
            "Note: CPC *Orders* (Order I–LI) are excluded from this pass so rule numbers inside",
            "each Order are not mislabeled as duplicate `Section 1.` headers; only operative",
            "Sections 1–158 are retained.",
        ],
    )
    sources_path = OUTPUT_DIR / "SOURCES.md"
    sources_path.write_text(sources_md, encoding="utf-8")
    print(f"Wrote {sources_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
