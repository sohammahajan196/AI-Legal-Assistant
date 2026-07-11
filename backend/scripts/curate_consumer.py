"""
Curate consumer-domain raw bare-act text (Consumer Protection Act 2019).

Downloads the official India Code PDF, extracts text with pdfplumber, normalizes
section headers to `Section N.` format, and writes UTF-8 `.txt` under
`data/raw/consumer/`. See PLAN.md Section 3 and TASKS.md T09.

Usage (from backend/):
    python scripts/curate_consumer.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

import httpx

from app.rag.corpus_curation import (
    CPA_SOURCE,
    curate_act_text,
    extract_pdf_text,
    render_sources_markdown,
    validate_curated_text,
)

OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "consumer"


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
        print(f"Downloading {CPA_SOURCE.act_name} ({CPA_SOURCE.act_year}) …")
        pdf_bytes = _download_pdf(client, CPA_SOURCE.pdf_url)

        print(f"Extracting and normalizing {CPA_SOURCE.filename} …")
        raw_text = extract_pdf_text(pdf_bytes)
        curated = curate_act_text(raw_text, CPA_SOURCE)
        validate_curated_text(curated, min_sections=90)

        output_path = OUTPUT_DIR / CPA_SOURCE.filename
        output_path.write_text(curated, encoding="utf-8")
        print(f"Wrote {output_path} ({len(curated.splitlines())} lines)")

    sources_md = render_sources_markdown(
        retrieval_date=retrieval_date,
        acts=[(CPA_SOURCE, output_path)],
        domain_title="Consumer domain",
        task_note="T09",
        extra_notes=[
            "Note: The canonical India Code handle links a legacy bitstream (`a2019-35.pdf`) that",
            "currently redirects; curation uses the working India Code bitstream `eng201935.pdf`.",
        ],
    )
    sources_path = OUTPUT_DIR / "SOURCES.md"
    sources_path.write_text(sources_md, encoding="utf-8")
    print(f"Wrote {sources_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
