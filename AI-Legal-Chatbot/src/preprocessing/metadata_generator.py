import json
import os
import re
from pathlib import Path


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their", "this",
    "to", "under", "was", "were", "will", "with", "without", "which", "shall", "may",
    "such", "any", "all", "other", "than", "thereof", "therein", "where", "when", "who",
    "whom", "his", "her", "him", "them", "these", "those", "not", "no", "if", "been",
    "being", "because", "between", "both", "can", "court", "courts", "case", "cases",
    "law", "laws", "act", "acts", "section", "sections", "provision", "provisions"
}


def load_json(file_path):
    """Load a JSON file and return its parsed content."""
    with open(file_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(text):
    """Return a normalized text string for keyword extraction."""
    if not isinstance(text, str):
        return ""
    text = text.replace("\n", " ")
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def infer_chapter_number(context, text):
    """Infer chapter number from the chapter heading context."""
    if context:
        match = re.search(r"CHAPTER\s+([IVXLCDM]+|[A-Z0-9]+)", context, flags=re.IGNORECASE)
        if match:
            return match.group(1)
    match = re.search(r"CHAPTER\s+([IVXLCDM]+|[A-Z0-9]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return "I"


def infer_chapter_title(context, text):
    """Infer chapter title from chapter context or section content."""
    for source in [context, text]:
        if not source:
            continue
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        for line in lines:
            if re.match(r"^(CHAPTER|PART)\b", line, flags=re.IGNORECASE):
                continue
            if re.match(r"^\d+\.", line):
                continue
            if line.upper().startswith("PRELIMINARY") or line.upper().startswith("POWER OF"):
                return line.upper()
            if len(line) <= 80 and re.search(r"[A-Za-z]", line):
                return line.upper()
    return ""


def infer_section_title(text, chunk):
    """Infer a readable section title from the chunk text."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if re.match(r"^\d+\.", line):
            continue
        if re.match(r"^(CHAPTER|PART)\b", line, flags=re.IGNORECASE):
            continue
        if line.startswith("(") or line.startswith('"'):
            continue
        if len(line) <= 80 and re.search(r"[A-Za-z]", line):
            return line
    context = chunk.get("context", "") or ""
    if context:
        return context.strip()
    return "Untitled Section"


def infer_law_name(document_name):
    """Map a document name to a human-readable law name."""
    name = (document_name or "").lower()
    if "nagarik" in name or "suraksha" in name:
        return "Bharatiya Nagarik Suraksha Sanhita"
    if "nyaya" in name:
        return "Bharatiya Nyaya Sanhita"
    if "sakshya" in name:
        return "Bharatiya Sakshya Adhiniyam"
    if "technology" in name:
        return "Information Technology Act"
    if "motor" in name:
        return "Motor Vehicles Act"
    if "consumer" in name:
        return "Consumer Protection Act"
    if "right" in name and "information" in name:
        return "Right to Information Act"
    if "domestic" in name:
        return "Domestic Violence Act"
    if "juvenile" in name:
        return "Juvenile Justice Act"
    return document_name or "Unknown Law"


def infer_law_short(law_name):
    """Return a short law identifier."""
    if "Nagarik Suraksha" in law_name:
        return "BNSS"
    if "Nyaya" in law_name:
        return "BNS"
    if "Sakshya" in law_name:
        return "BSA"
    if "Technology" in law_name:
        return "ITA"
    if "Motor Vehicles" in law_name:
        return "MVA"
    if "Consumer Protection" in law_name:
        return "CPA"
    if "Right to Information" in law_name:
        return "RTI"
    return law_name[:4].upper()


def infer_year(document_name):
    """Infer the law year from the document name if present."""
    match = re.search(r"(\d{4})", document_name or "")
    if match:
        return int(match.group(1))
    return 2023


def infer_legal_domain(document_name, text):
    """Infer the legal domain."""
    document_name = (document_name or "").lower()
    text_lower = (text or "").lower()
    if "nagarik" in document_name or "suraksha" in document_name or "bnss" in document_name:
        return "Criminal Procedure"
    if "nyaya" in document_name or "bns" in document_name:
        return "Criminal Law"
    if "sakshya" in document_name or "bsa" in document_name or "evidence" in text_lower:
        return "Evidence Law"
    if "technology" in document_name or "cyber" in text_lower or "electronic" in text_lower:
        return "Cyber Law"
    if "motor" in document_name or "vehicle" in text_lower:
        return "Transport and Road Safety"
    if "consumer" in document_name or "consumer" in text_lower:
        return "Consumer Protection"
    if "information" in document_name and "right" in document_name:
        return "Transparency and Governance"
    if "domestic" in document_name or "violence" in text_lower:
        return "Domestic Violence / Family Law"
    if "juvenile" in document_name or "child" in text_lower:
        return "Juvenile Justice"
    return "General Legal Matter"


def extract_keywords(text, section_title, context):
    """Extract a concise list of keywords from chunk content."""
    combined = " ".join([section_title or "", context or "", text or ""])
    normalized = normalize_text(combined).lower()
    words = re.findall(r"\b[a-zA-Z]{3,}\b", normalized)
    freq = {}
    for word in words:
        if word in STOPWORDS:
            continue
        freq[word] = freq.get(word, 0) + 1
    ranked = sorted(freq.items(), key=lambda item: (-item[1], item[0]))
    keywords = [word for word, _ in ranked[:10]]
    if not keywords and section_title:
        keywords = [section_title.strip()]
    return keywords


def extract_entities(text):
    """Extract likely named entities from the chunk text."""
    patterns = [
        r"\bHigh Court\b",
        r"\bSupreme Court\b",
        r"\bCourt of Session\b",
        r"\bJudicial Magistrate\b",
        r"\bExecutive Magistrate\b",
        r"\bChief Judicial Magistrate\b",
        r"\bAdditional Chief Judicial Magistrate\b",
        r"\bSessions Judge\b",
        r"\bPublic Prosecutor\b",
        r"\bSpecial Public Prosecutor\b",
        r"\bAssistant Public Prosecutor\b",
        r"\bDirector of Prosecution\b",
        r"\bCommissioner of Police\b",
        r"\bState Government\b",
        r"\bCentral Government\b",
        r"\bParliament\b",
        r"\bUnion\b",
        r"\bMagistrate\b",
        r"\bpolice officer\b",
        r"\bNagaland\b",
        r"\bShillong\b",
        r"\bConstitution\b",
    ]
    entities = []
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            entity = match.strip()
            if entity not in entities:
                entities.append(entity)
    return entities


def infer_topics(text, section_title):
    """Infer a small list of topics based on common legal concepts."""
    combined = f"{section_title} {text}".lower()
    topics = []
    if "application" in combined or "apply" in combined or "applicable" in combined:
        topics.append("Applicability")
    if "jurisdiction" in combined or "local area" in combined or "district" in combined:
        topics.append("Jurisdiction")
    if "commencement" in combined or "come into force" in combined:
        topics.append("Commencement")
    if "definition" in combined or "means" in combined:
        topics.append("Definitions")
    if "proviso" in combined or "provided" in combined:
        topics.append("Provisos")
    if "exception" in combined:
        topics.append("Exceptions")
    if "explanation" in combined:
        topics.append("Explanation")
    if "bail" in combined or "arrest" in combined:
        topics.append("Arrest and Bail")
    if not topics:
        topics = ["General Provision"]
    return topics


def infer_cross_references(text):
    """Extract obvious cross-reference phrases from the chunk."""
    cross_refs = []
    patterns = [
        r"Chapter\s+[IXVLCDM]+",
        r"Section\s+\d+",
        r"Sixth Schedule",
        r"First Schedule",
        r"Constitution",
        r"Bharatiya Nyaya Sanhita",
        r"Information Technology Act",
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, flags=re.IGNORECASE)
        for match in matches:
            normalized = match.strip()
            if normalized not in cross_refs:
                cross_refs.append(normalized)
    return cross_refs


def infer_page_range(chunk, page_number):
    """Infer a simple page range from the chunk metadata."""
    page_start = int(page_number or 1)
    return page_start, page_start + 1


def enrich_chunk(chunk, document_name, source_file, page_number):
    """Return a chunk enriched with the requested metadata structure."""
    text = chunk.get("text", "") or ""
    context = chunk.get("context", "") or ""
    section_title = infer_section_title(text, chunk)
    law_name = infer_law_name(document_name)
    law_short = infer_law_short(law_name)
    year = infer_year(document_name)
    chapter_number = infer_chapter_number(context, text)
    chapter_title = infer_chapter_title(context, text)
    section_number = chunk.get("section_number") or ""

    keywords = extract_keywords(text, section_title, context)
    entities = extract_entities(text)
    topics = infer_topics(text, section_title)
    cross_refs = infer_cross_references(text)
    page_start, page_end = infer_page_range(chunk, page_number)

    contains_explanation = "explanation" in text.lower()
    contains_proviso = "proviso" in text.lower()
    contains_exception = "exception" in text.lower()
    contains_definition = "definition" in text.lower() or '"' in text and "means" in text.lower()

    return {
        "chunk_id": f"{law_short}_{section_number.zfill(3)}",
        "law_name": law_name,
        "law_short": law_short,
        "year": year,
        "chapter_number": chapter_number,
        "chapter_title": chapter_title or "General",
        "section_number": section_number,
        "section_title": section_title if section_title else f"Section {section_number}",
        "legal_domain": infer_legal_domain(document_name, text),
        "document_type": "Act",
        "language": "English",
        "keywords": keywords,
        "entities": entities,
        "topics": topics,
        "contains_explanation": contains_explanation,
        "contains_proviso": contains_proviso,
        "contains_exception": contains_exception,
        "contains_definition": contains_definition,
        "cross_references": cross_refs,
        "page_start": page_start,
        "page_end": page_end,
    }


def process_file(input_path, output_dir):
    """Generate flat metadata records for one chunk JSON file and write them to disk."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating metadata: {input_path.name}")

    try:
        payload = load_json(input_path)
        if not isinstance(payload, dict):
            raise ValueError("Loaded JSON is not an object")

        document_name = payload.get("document", input_path.stem)
        source_file = payload.get("source_file", input_path.name)
        chunks = payload.get("chunks", [])

        metadata_records = []
        for index, chunk in enumerate(chunks, start=1):
            page_number = 1 + index
            metadata_records.append(enrich_chunk(chunk, document_name, source_file, page_number))

        output_path = output_dir / f"{input_path.stem}_metadata.json"
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(metadata_records, handle, ensure_ascii=False, indent=4)
            handle.write("\n")

        print(f"Saved metadata: {output_path}")
        return output_path
    except Exception as exc:
        print(f"Error processing {input_path.name}: {exc}")
        return None


def process_all_files(input_dir, output_dir):
    """Process every chunk JSON file in the input directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return []

    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        print(f"No chunk JSON files found in {input_dir}")
        return []

    processed_files = []
    for file_path in json_files:
        result = process_file(file_path, output_dir)
        if result is not None:
            processed_files.append(result)

    print(f"Completed metadata generation for {len(processed_files)} file(s).")
    return processed_files


def main():
    """Entry point for the metadata generation pipeline."""
    project_root = Path(__file__).resolve().parents[2]
    input_dir = project_root / "data" / "chunks"
    output_dir = project_root / "data" / "metadata"

    os.makedirs(output_dir, exist_ok=True)
    process_all_files(input_dir, output_dir)


if __name__ == "__main__":
    main()
