"""
Curate property-domain raw bare-act text (Transfer of Property Act 1882).

Downloads the official India Code PDF, extracts text with pdfplumber, normalizes
section headers to `Section N.` format, and writes UTF-8 `.txt` under
`data/raw/property/`. See PLAN.md Section 3 and TASKS.md T10.

Usage (from backend/):
    python scripts/curate_property.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.rag.corpus_curation import (
    TPA_SOURCE,
    curate_act_text,
    extract_pdf_text,
    render_sources_markdown,
    validate_curated_text,
)

OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "property"


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
        print(f"Downloading {TPA_SOURCE.act_name} ({TPA_SOURCE.act_year}) …")
        pdf_bytes = _download_pdf(client, TPA_SOURCE.pdf_url)

        print(f"Extracting and normalizing {TPA_SOURCE.filename} …")
        raw_text = extract_pdf_text(pdf_bytes)
        curated = curate_act_text(raw_text, TPA_SOURCE)
        validate_curated_text(curated, min_sections=100)

        output_path = OUTPUT_DIR / TPA_SOURCE.filename
        output_path.write_text(curated, encoding="utf-8")
        print(f"Wrote {output_path} ({len(curated.splitlines())} lines)")

    sources_md = render_sources_markdown(
        retrieval_date=retrieval_date,
        acts=[(TPA_SOURCE, output_path)],
        domain_title="Property domain",
        task_note="T10",
    )
    sources_path = OUTPUT_DIR / "SOURCES.md"
    sources_path.write_text(sources_md, encoding="utf-8")
    print(f"Wrote {sources_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
