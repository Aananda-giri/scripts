import csv
import re
from pathlib import Path

from bs4 import BeautifulSoup

SECTION_HEADINGS = [
    r"job\s*description:?",
    r"responsibilities:?",
    r"skills:?",
    r"qualifications:?",
    r"requirements:?",
    r"about\s+(the\s+)?role:?",
    r"what\s+you'?ll\s+do:?",
    r"key\s+responsibilities:?",
    r"minimum\s+education\s+requirement:?",
    r"benefits:?",
    r"pay\s+(range|transparency)",
    r"shift:?",
    r"hours\s+per\s+week:?",
    r"role\s+purpose:?",
    r"position\s+success\s+criteria:?",
    r"main\s+duties",
    r"deliver",
    r"do\b",
    r"team\s+management:?",
]
SECTION_RE = re.compile(
    r"(?i)(?:^|\n)\s*(" + "|".join(SECTION_HEADINGS) + r")",
    re.MULTILINE,
)


def load_jobs_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)


def clean_html(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    for br in soup.find_all("br"):
        br.replace_with("\n")
    text = soup.get_text()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_metadata(row: dict) -> dict:
    location = row.get("Job Location", "").strip()
    if not location:
        location = "Location Not Specified"
    tags = row.get("Tags", "").strip()
    return {
        "job_id": row["ID"].strip(),
        "job_title": row["Job Title"].strip(),
        "company_name": row["Company Name"].strip(),
        "job_category": row["Job Category"].strip(),
        "job_level": row.get("Job Level", "").strip(),
        "job_location": location,
        "publication_date": row.get("Publication Date", "").strip(),
        "tags": tags,
    }


def _split_by_headings(text: str) -> list[tuple[str, str]]:
    matches = list(SECTION_RE.finditer(text))
    if not matches:
        return [("description", text)]

    sections = []
    for i, match in enumerate(matches):
        heading = match.group(1).rstrip(":").strip().lower()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((heading, body))
    return sections


def _chunk_text(text: str, max_size: int, overlap: int, min_size: int) -> list[str]:
    if len(text) <= max_size:
        return [text] if len(text) >= min_size else []

    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if current and len(current) + len(para) + 2 > max_size:
            if len(current) >= min_size:
                chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para

    if current and len(current) >= min_size:
        chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        overlapped = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_tail = chunks[i - 1][-overlap:]
            if prev_tail and prev_tail[-1] != " ":
                prev_tail = prev_tail.rsplit(" ", 1)[-1]
            overlapped.append(prev_tail + " " + chunks[i])
        chunks = overlapped

    return chunks


def chunk_description(text: str, metadata: dict, max_size: int = 1000,
                      overlap: int = 200, min_size: int = 100) -> list[dict]:
    sections = _split_by_headings(text)
    all_chunks = []
    chunk_index = 0

    for section_type, section_text in sections:
        text_chunks = _chunk_text(section_text, max_size, overlap, min_size)
        for text_chunk in text_chunks:
            chunk = {
                "chunk_id": f"{metadata['job_id']}__{section_type}_{chunk_index}",
                "job_id": metadata["job_id"],
                "job_title": metadata["job_title"],
                "company_name": metadata["company_name"],
                "job_category": metadata["job_category"],
                "job_level": metadata["job_level"],
                "job_location": metadata["job_location"],
                "publication_date": metadata["publication_date"],
                "tags": metadata["tags"],
                "section_type": section_type,
                "chunk_index": chunk_index,
                "text": text_chunk,
            }
            all_chunks.append(chunk)
            chunk_index += 1

    return all_chunks


def load_and_chunk(csv_path: str, max_size: int = 1000, overlap: int = 200,
                   min_size: int = 100) -> list[dict]:
    rows = load_jobs_csv(csv_path)
    all_chunks = []
    for row in rows:
        metadata = extract_metadata(row)
        clean_text = clean_html(row.get("Job Description", ""))
        if not clean_text:
            continue
        chunks = chunk_description(clean_text, metadata, max_size, overlap, min_size)
        all_chunks.extend(chunks)
    return all_chunks
