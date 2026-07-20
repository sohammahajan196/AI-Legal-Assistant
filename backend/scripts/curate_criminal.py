"""
Curate criminal-domain raw bare-act texts (IPC 1860 + CrPC 1973).

Downloads official India Code PDFs, extracts text with pdfplumber, normalizes
section headers to `Section N.` format, and writes UTF-8 `.txt` files under
`data/raw/criminal/`. See PLAN.md Section 3 and TASKS.md T05.

Usage (from backend/):
    python scripts/curate_criminal.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.corpus_curation import (  # noqa: E402
    CRPC_SOURCE,
    IPC_SOURCE,
    curate_act_text,
    extract_pdf_text,
    render_sources_markdown,
    validate_curated_text,
)

OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "criminal"


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


def _curate_and_write(client: httpx.Client, act_source) -> Path:
    print(f"Downloading {act_source.act_name} ({act_source.act_year}) …")
    pdf_bytes = _download_pdf(client, act_source.pdf_url)

    print(f"Extracting and normalizing {act_source.filename} …")
    raw_text = extract_pdf_text(pdf_bytes)
    curated = curate_act_text(raw_text, act_source)
    min_sections = 450 if act_source is IPC_SOURCE else 360
    validate_curated_text(curated, min_sections=min_sections)

    output_path = OUTPUT_DIR / act_source.filename
    output_path.write_text(curated, encoding="utf-8")
    section_count = len(curated.splitlines())
    print(f"Wrote {output_path} ({section_count} lines)")
    return output_path


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    retrieval_date = date.today()

    with httpx.Client() as client:
        ipc_path = _curate_and_write(client, IPC_SOURCE)
        crpc_path = _curate_and_write(client, CRPC_SOURCE)

    sources_md = render_sources_markdown(
        retrieval_date=retrieval_date,
        acts=[(IPC_SOURCE, ipc_path), (CRPC_SOURCE, crpc_path)],
    )
    sources_path = OUTPUT_DIR / "SOURCES.md"
    sources_path.write_text(sources_md, encoding="utf-8")
    print(f"Wrote {sources_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
