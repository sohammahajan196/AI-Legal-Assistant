"""
Utilities for curating raw bare-act text from official India Code PDFs.

Used by offline curation scripts (see TASKS.md T05-T10) and unit tests that
validate section-header formatting without hitting the network.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pdfplumber

# Official India Code PDF bitstreams (central acts).
IPC_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/15289/1/ipc_act.pdf"
CRPC_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/6796/1/ccp1973.pdf"
CPC_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/2191/1/aA1908-05.pdf"
HMA_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/13814/1/the_hindu_marriage_act,_1955.pdf"
SMA_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/15480/1/special_marriage_act.pdf"
IDA_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/20352/1/the_industrial_disputes_act.pdf"
COW_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/15793/1/aA2019-29.pdf"
CPA_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/15256/1/eng201935.pdf"
TPA_PDF_URL = "https://www.indiacode.nic.in/bitstream/123456789/2338/1/A1882-04.pdf"

IPC_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/2263?locale=en"
CRPC_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/15247?locale=en"
CPC_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/2191?locale=en"
HMA_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/1560?locale=en"
SMA_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/1387?locale=en"
IDA_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/15191?locale=en"
COW_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/15793?locale=en"
CPA_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/15256?locale=en"
TPA_INDIA_CODE_HANDLE = "https://www.indiacode.nic.in/handle/123456789/2338?locale=en"

# Matches corpus section headers like "Section 304A." (TASKS.md T05 / T11).
SECTION_HEADER_RE = re.compile(r"^Section\s+(\d+[A-Z]?)\.\s", re.MULTILINE)

# IPC operative sections end their title with an em dash before the body text.
_IPC_SECTION_RE = re.compile(
    r"^(?:\d+\[)?(?:\[\s*)?(\d{1,3}[A-Z]?)\.\s+"
    r"(?!Subs\.|Ins\.|Rep\.|Added |The words|The proviso|Certain words|Now see|Illustrations?\b)"
    r"(.+?)(?:\.[\u2014\u2013\u2015]|\.--|\.-)",
    re.MULTILINE,
)

# CrPC operative sections begin a numbered subsection "(1)" immediately after the title.
_CRPC_SECTION_RE = re.compile(
    r"^\s*(\d{1,3}[A-Z]?)\.(?:\s*|\s+)"
    r"(?!Subs\.|Ins\.|Rep\.|Added |The words|The proviso|Certain words|Now see)"
    r"([A-Z][^.\n(]{1,100}?)\.\s*"
    r"(\(\d+\)|[A-Z(])",
    re.MULTILINE,
)

_CRPC_AMENDMENT_MARKER = "THE CODE OF CRIMINAL PROCEDURE (AMENDMENT) ACT, 2001"
_CPC_AMENDMENT_MARKER = "THE CODE OF CIVIL PROCEDURE (AMENDMENT"


@dataclass(frozen=True)
class ActSource:
    """Metadata for a curated bare-act file."""

    filename: str
    act_name: str
    act_year: int
    pdf_url: str
    india_code_handle_url: str


IPC_SOURCE = ActSource(
    filename="ipc_1860.txt",
    act_name="Indian Penal Code",
    act_year=1860,
    pdf_url=IPC_PDF_URL,
    india_code_handle_url=IPC_INDIA_CODE_HANDLE,
)

CRPC_SOURCE = ActSource(
    filename="crpc_1973.txt",
    act_name="Code of Criminal Procedure",
    act_year=1973,
    pdf_url=CRPC_PDF_URL,
    india_code_handle_url=CRPC_INDIA_CODE_HANDLE,
)

CPC_SOURCE = ActSource(
    filename="cpc_1908.txt",
    act_name="Code of Civil Procedure",
    act_year=1908,
    pdf_url=CPC_PDF_URL,
    india_code_handle_url=CPC_INDIA_CODE_HANDLE,
)

HMA_SOURCE = ActSource(
    filename="hma_1955.txt",
    act_name="Hindu Marriage Act",
    act_year=1955,
    pdf_url=HMA_PDF_URL,
    india_code_handle_url=HMA_INDIA_CODE_HANDLE,
)

SMA_SOURCE = ActSource(
    filename="sma_1954.txt",
    act_name="Special Marriage Act",
    act_year=1954,
    pdf_url=SMA_PDF_URL,
    india_code_handle_url=SMA_INDIA_CODE_HANDLE,
)

IDA_SOURCE = ActSource(
    filename="ida_1947.txt",
    act_name="Industrial Disputes Act",
    act_year=1947,
    pdf_url=IDA_PDF_URL,
    india_code_handle_url=IDA_INDIA_CODE_HANDLE,
)

COW_SOURCE = ActSource(
    filename="code_on_wages_2019.txt",
    act_name="Code on Wages",
    act_year=2019,
    pdf_url=COW_PDF_URL,
    india_code_handle_url=COW_INDIA_CODE_HANDLE,
)

CPA_SOURCE = ActSource(
    filename="cpa_2019.txt",
    act_name="Consumer Protection Act",
    act_year=2019,
    pdf_url=CPA_PDF_URL,
    india_code_handle_url=CPA_INDIA_CODE_HANDLE,
)

TPA_SOURCE = ActSource(
    filename="tpa_1882.txt",
    act_name="Transfer of Property Act",
    act_year=1882,
    pdf_url=TPA_PDF_URL,
    india_code_handle_url=TPA_INDIA_CODE_HANDLE,
)

# Acts whose sections use an em-dash / horizontal-bar title separator in the source PDF.
_EM_DASH_ACTS = frozenset({IPC_SOURCE, CPC_SOURCE, HMA_SOURCE, SMA_SOURCE, IDA_SOURCE, COW_SOURCE, CPA_SOURCE, TPA_SOURCE})
# Acts that may inline amendment history repeating section numbers.
_DEDUPE_ACTS = frozenset({CPC_SOURCE, HMA_SOURCE, SMA_SOURCE, IDA_SOURCE, COW_SOURCE, CPA_SOURCE, TPA_SOURCE})


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract plain text from an official bare-act PDF using pdfplumber."""
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            pages.append(page_text)
    return "\n".join(pages)


def _collapse_whitespace(text: str) -> str:
    """Normalize line endings and collapse runs of blank lines."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def _strip_ipc_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative act text."""
    marker = "Preamble.—WHEREAS it is expedient to provide a general Penal Code"
    idx = text.find(marker)
    if idx == -1:
        raise ValueError("IPC PDF text missing expected preamble marker")
    # Include the preceding CHAPTER I heading when present.
    chapter_idx = text.rfind("CHAPTER I", 0, idx)
    start = chapter_idx if chapter_idx != -1 else idx
    return text[start:]


def _strip_em_dash_arrangement(
    text: str,
    *,
    section_one_pattern: str,
    heading: str = "PRELIMINARY",
    amendment_marker: str | None = None,
) -> str:
    """Drop TOC blocks and keep operative text for em-dash-style acts."""
    marker_match = re.search(section_one_pattern, text, flags=re.DOTALL)
    if marker_match is None:
        raise ValueError("PDF text missing expected section 1 marker")
    heading_idx = text.rfind(heading, 0, marker_match.start())
    start = heading_idx if heading_idx != -1 else marker_match.start()
    body = text[start:]
    if amendment_marker:
        amendment_idx = body.find(amendment_marker)
        if amendment_idx != -1:
            body = body[:amendment_idx]
    return body


def _strip_hma_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative HMA act text."""
    return _strip_em_dash_arrangement(
        text,
        section_one_pattern=(
            r"1\. Short title and extent\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be called the Hindu Marriage\s+"
            r"Act, 1955\."
        ),
    )


def _strip_sma_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative SMA act text."""
    return _strip_em_dash_arrangement(
        text,
        section_one_pattern=(
            r"1\. Short title, extent and commencement\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be called the Special Marriage\s+"
            r"Act, 1954\."
        ),
    )


def _strip_ida_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative IDA act text."""
    return _strip_em_dash_arrangement(
        text,
        section_one_pattern=(
            r"1\. Short title, extent and commencement\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be called the Industrial Disputes\s+"
            r"Act,\s*1947\."
        ),
        heading="CHAPTER I",
    )


def _strip_cow_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative Code on Wages act text."""
    return _strip_em_dash_arrangement(
        text,
        section_one_pattern=(
            r"1\. Short title, extent and commencement\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be called the Code on Wages, 2019\."
        ),
    )


def _strip_cpa_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative CPA act text."""
    return _strip_em_dash_arrangement(
        text,
        section_one_pattern=(
            r"1\. Short title, extent, commencement and application\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be called the Consumer\s+"
            r"Protection Act, 2019\."
        ),
    )


def _strip_tpa_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative TPA act text."""
    marker_match = re.search(
        r"Preamble\.[\u2014\u2013\u2015\-\uFFFD]WHEREAS it is expedient to define and amend certain parts of the law\s+"
        r"relating to the transfer of property by act of parties",
        text,
        flags=re.DOTALL,
    )
    if marker_match is None:
        raise ValueError("TPA PDF text missing expected preamble marker")
    return text[marker_match.start() :]


def _strip_cpc_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative CPC act text."""
    marker_match = re.search(
        r"1\. Short title, commencement and extent\.[\u2014\u2013\u2015\-\uFFFD]\(1\) This Act may be cited as the Code of Civil\s+"
        r"Procedure, 1908\.",
        text,
        flags=re.DOTALL,
    )
    if marker_match is None:
        raise ValueError("CPC PDF text missing expected section 1 marker")
    preliminary_idx = text.rfind("PRELIMINARY", 0, marker_match.start())
    start = preliminary_idx if preliminary_idx != -1 else marker_match.start()
    body = text[start:]
    amendment_idx = body.find(_CPC_AMENDMENT_MARKER)
    if amendment_idx != -1:
        body = body[:amendment_idx]
    order_idx = body.find("\nORDER I\n")
    if order_idx != -1:
        body = body[:order_idx]
    return body


def _normalize_ida_inline_section_breaks(text: str) -> str:
    """Insert line breaks before section markers inlined with footnote text."""
    text = re.sub(
        r"(\d)\[(\d{1,3}[A-Z]?\. (?!Ins\.|Subs\.|Rep\.|Added |Section )[A-Z])",
        r"\1\n\2",
        text,
    )
    text = re.sub(
        r"\](\d{1,3}[A-Z]?\. (?!Ins\.|Subs\.|Rep\.|Added |Section )[A-Z])",
        r"]\n\1",
        text,
    )
    return text


def _strip_ida_state_amendments(text: str) -> str:
    """Remove inline state-adaptation blocks from consolidated India Code IDA PDFs."""
    next_section = (
        r"(?=\n\d{1,3}[A-Z]?\. (?!Ins\.|Subs\.|Rep\.|Added |Section )[A-Z])"
    )
    text = re.sub(
        rf"\nSTATE AMENDMENT\n.*?{next_section}",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\n(?:Rajasthan|Manipur|Kerala|Karnataka|Orissa|Assam|Andhra Pradesh|Meghalaya)\s*\n"
        r"(?:Amendment|Insertion).*?(?=\n(?:\d{1,3}[A-Z]?\. (?!Ins\.|Subs\.|Rep\.|Added |Section )[A-Z]|STATE AMENDMENT|CHAPTER ))",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(
        r"\nInsertion of new[^\n]*\n.*?(?=\n\d{1,3}[A-Z]?\. Conciliation officers)",
        "\n",
        text,
        flags=re.DOTALL,
    )
    text = re.sub(r"\[Vide[^\]]*\]", "", text, flags=re.DOTALL)
    return text


def _drop_premature_ida_nine_series(text: str) -> str:
    """Drop state-inserted section 9C–9J blocks that appear before central section 4."""
    parts = re.split(r"(?=^Section \d+[A-Z]?\.\s)", text, flags=re.MULTILINE)
    if len(parts) <= 1:
        return text

    preamble = parts[0]
    seen_four = False
    kept = [preamble]
    for part in parts[1:]:
        match = re.match(r"^Section (9[A-Z]+)\.", part)
        if match and not seen_four:
            continue
        if re.match(r"^Section 4\.", part):
            seen_four = True
        kept.append(part)
    return "".join(kept)


def _strip_crpc_arrangement(text: str) -> str:
    """Drop the table-of-contents block; keep the operative CrPC act text."""
    marker_match = re.search(
        r"1\. Short title extent and commencement\. \(1\) This Act may be\s+"
        r"called the Code of Criminal Procedure, 1973\.",
        text,
        flags=re.DOTALL,
    )
    if marker_match is None:
        raise ValueError("CrPC PDF text missing expected section 1 marker")
    chapter_idx = text.rfind("CHAPTER I", 0, marker_match.start())
    start = chapter_idx if chapter_idx != -1 else marker_match.start()
    body = text[start:]
    amendment_idx = body.find(_CRPC_AMENDMENT_MARKER)
    if amendment_idx != -1:
        body = body[:amendment_idx]
    return body


def _dedupe_section_blocks(text: str) -> str:
    """Keep only the first text block for each `Section N.` number.

    Consolidated India Code PDFs sometimes repeat a section number when
    amendment history is inlined; the first occurrence is the operative text.
    """
    parts = re.split(r"(?=^Section\s+\d+[A-Z]?\.\s)", text, flags=re.MULTILINE)
    if len(parts) <= 1:
        return text

    preamble = parts[0]
    seen: set[str] = set()
    kept = [preamble]
    for part in parts[1:]:
        match = re.match(r"^Section\s+(\d+[A-Z]?)\.", part)
        if match is None:
            kept.append(part)
            continue
        number = match.group(1)
        if number in seen:
            continue
        seen.add(number)
        kept.append(part)
    return "".join(kept)


def normalize_ipc_section_headers(text: str) -> str:
    """Convert IPC PDF section lines to `Section N.` headers."""

    def _replace(match: re.Match[str]) -> str:
        return f"Section {match.group(1)}. {match.group(2)}.—"

    return _IPC_SECTION_RE.sub(_replace, text)


def _join_crpc_wrapped_titles(text: str) -> str:
    """Merge PDF line wraps so section titles ending with '.' sit on one line."""
    lines = text.splitlines()
    merged: list[str] = []
    idx = 0

    while idx < len(lines):
        line = lines[idx]
        match = re.match(r"^\s*(\d{1,3}[A-Z]?)\.\s*(.+)$", line)
        if match and "." not in match.group(2):
            buffer = line.strip()
            idx += 1
            while idx < len(lines):
                next_line = lines[idx].strip()
                if not next_line:
                    idx += 1
                    continue
                buffer = f"{buffer} {next_line}"
                idx += 1
                if "." in next_line:
                    break
            merged.append(buffer)
            continue

        merged.append(line)
        idx += 1

    return "\n".join(merged)


def normalize_crpc_section_headers(text: str) -> str:
    """Convert CrPC PDF section lines to `Section N.` headers."""

    def _replace(match: re.Match[str]) -> str:
        title = re.sub(r"\s+", " ", match.group(2).strip())
        suffix = match.group(3)
        return f"Section {match.group(1)}. {title}. {suffix}"

    return _CRPC_SECTION_RE.sub(_replace, text)


def normalize_section_headers(text: str, act: ActSource) -> str:
    """Convert PDF-style section numbers to consistent `Section N.` headers."""
    if act in _EM_DASH_ACTS:
        return normalize_ipc_section_headers(text)
    if act is CRPC_SOURCE:
        return normalize_crpc_section_headers(text)
    raise ValueError(f"Unsupported act source: {act.filename}")


def curate_act_text(raw_pdf_text: str, act: ActSource) -> str:
    """Transform extracted PDF text into clean UTF-8 bare-act text."""
    if act is IPC_SOURCE:
        body = _strip_ipc_arrangement(raw_pdf_text)
    elif act is CRPC_SOURCE:
        body = _strip_crpc_arrangement(raw_pdf_text)
    elif act is CPC_SOURCE:
        body = _strip_cpc_arrangement(raw_pdf_text)
    elif act is HMA_SOURCE:
        body = _strip_hma_arrangement(raw_pdf_text)
    elif act is SMA_SOURCE:
        body = _strip_sma_arrangement(raw_pdf_text)
    elif act is IDA_SOURCE:
        body = _strip_ida_arrangement(raw_pdf_text)
    elif act is COW_SOURCE:
        body = _strip_cow_arrangement(raw_pdf_text)
    elif act is CPA_SOURCE:
        body = _strip_cpa_arrangement(raw_pdf_text)
    elif act is TPA_SOURCE:
        body = _strip_tpa_arrangement(raw_pdf_text)
    else:
        raise ValueError(f"Unsupported act source: {act.filename}")

    body = _collapse_whitespace(body)
    if act is CRPC_SOURCE:
        body = _join_crpc_wrapped_titles(body)
    if act is IDA_SOURCE:
        body = _normalize_ida_inline_section_breaks(body)
        body = _strip_ida_state_amendments(body)
    body = normalize_section_headers(body, act)
    if act in _DEDUPE_ACTS:
        body = _dedupe_section_blocks(body)
    if act is IDA_SOURCE:
        body = _drop_premature_ida_nine_series(body)
    return body


def list_section_numbers(text: str) -> list[str]:
    """Return section numbers in document order from normalized headers."""
    return SECTION_HEADER_RE.findall(text)


def validate_curated_text(text: str, *, min_sections: int = 50) -> None:
    """Raise ValueError when curated text fails basic corpus QA checks."""
    if not text.strip():
        raise ValueError("Curated text is empty")

    sections = list_section_numbers(text)
    if len(sections) < min_sections:
        raise ValueError(f"Expected at least {min_sections} sections, found {len(sections)}")

    if len(sections) != len(set(sections)):
        duplicates = sorted({s for s in sections if sections.count(s) > 1})
        raise ValueError(f"Duplicate section headers found: {duplicates[:5]}")


def render_sources_markdown(
    *,
    retrieval_date: date,
    acts: list[tuple[ActSource, Path]],
    domain_title: str = "Criminal domain",
    task_note: str = "T05",
    extra_notes: list[str] | None = None,
) -> str:
    """Build SOURCES.md content for a domain folder."""
    lines = [
        f"# {domain_title} — source provenance",
        "",
        f"Raw bare-act text curated for TASKS.md {task_note}. Each file was exported from the",
        "official India Code portal PDF, converted to UTF-8 plain text, and normalized",
        "to `Section N.` headers for the section-aware parser (T11).",
        "",
    ]
    if extra_notes:
        for note in extra_notes:
            lines.append(note)
        lines.append("")
    for act, output_path in acts:
        lines.extend(
            [
                f"## {output_path.name}",
                "",
                f"- **Act:** {act.act_name}, {act.act_year}",
                f"- **India Code handle:** {act.india_code_handle_url}",
                f"- **PDF source:** {act.pdf_url}",
                f"- **Retrieved:** {retrieval_date.isoformat()}",
                "",
            ]
        )
    return "\n".join(lines)
