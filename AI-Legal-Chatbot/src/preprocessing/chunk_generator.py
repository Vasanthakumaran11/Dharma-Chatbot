import json
import os
import re
from pathlib import Path


def load_json(file_path):
    """Load a JSON file and return its parsed content."""
    with open(file_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def is_section_start(line):
    """Return True when a line looks like the start of a legal section."""
    stripped = line.strip()
    if not stripped:
        return False
    return bool(re.match(r"^\d+\.\s*(?:\(|[A-Z\"“])", stripped)) or bool(re.match(r"^\d+\.\s*$", stripped))


def is_heading_line(line):
    """Return True for short heading-like lines such as chapter titles or section labels."""
    stripped = line.strip()
    if not stripped or stripped.startswith("(") or re.match(r"^\d+\.", stripped):
        return False
    if re.match(r"^(CHAPTER|PART)\s+([IVXLCDM]+|[A-Z0-9]+)$", stripped.upper()):
        return True
    if len(stripped) <= 80 and re.match(r"^[A-Za-z0-9][A-Za-z0-9 ,/&()'’.-]*$", stripped):
        return True
    return False


def build_chunks(document_name, source_file, pages):
    """Create section-level chunks while keeping chapter/section headings with their content."""
    if not isinstance(pages, list):
        return []

    lines = []
    for page in pages:
        text = page.get("text", "") or ""
        if isinstance(text, str):
            lines.extend(text.splitlines())

    chunks = []
    current_chunk_lines = []
    current_section_number = None
    current_context = []
    pending_heading = None
    in_section = False

    for index, line in enumerate(lines):
        stripped = line.strip()

        if not stripped:
            if in_section:
                current_chunk_lines.append("")
            continue

        if re.match(r"^(CHAPTER|PART)\s+([IVXLCDM]+|[A-Z0-9]+)$", stripped.upper()):
            current_context = [stripped]
            pending_heading = None
            continue

        if is_heading_line(stripped):
            next_line = ""
            for future in lines[index + 1:]:
                future_stripped = future.strip()
                if future_stripped:
                    next_line = future_stripped
                    break
            if next_line and is_section_start(next_line):
                pending_heading = stripped
                continue

        if is_section_start(stripped):
            if in_section and current_section_number is not None:
                chunk_text = "\n".join(current_chunk_lines).strip()
                if chunk_text:
                    chunks.append(
                        {
                            "document": document_name,
                            "source_file": source_file,
                            "section_number": current_section_number,
                            "context": "\n".join(current_context).strip(),
                            "text": chunk_text,
                        }
                    )

            current_section_number = re.match(r"^(\d+)\.", stripped)
            if current_section_number:
                current_section_number = current_section_number.group(1)
            else:
                current_section_number = None

            current_chunk_lines = []
            if current_context:
                current_chunk_lines.extend(current_context)
            if pending_heading:
                current_chunk_lines.append(pending_heading)
                pending_heading = None
            current_chunk_lines.append(stripped)
            in_section = True
            continue

        if in_section:
            current_chunk_lines.append(stripped)

    if in_section and current_section_number is not None:
        chunk_text = "\n".join(current_chunk_lines).strip()
        if chunk_text:
            chunks.append(
                {
                    "document": document_name,
                    "source_file": source_file,
                    "section_number": current_section_number,
                    "context": "\n".join(current_context).strip(),
                    "text": chunk_text,
                }
            )

    return chunks


def process_file(input_path, output_dir):
    """Create section-level chunks for one cleaned JSON file and write them to disk."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Chunking: {input_path.name}")

    try:
        data = load_json(input_path)
        if not isinstance(data, dict):
            raise ValueError("Loaded JSON is not an object")

        document_name = data.get("document", input_path.stem)
        source_file = data.get("source_file", input_path.name)
        pages = data.get("pages", [])
        chunks = build_chunks(document_name, source_file, pages)

        output_path = output_dir / f"{input_path.stem}_chunks.json"
        payload = {
            "document": document_name,
            "source_file": source_file,
            "chunk_count": len(chunks),
            "chunks": chunks,
        }
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=4)
            handle.write("\n")

        print(f"Saved chunks: {output_path}")
        return output_path
    except Exception as exc:
        print(f"Error chunking {input_path.name}: {exc}")
        return None


def process_all_files(input_dir, output_dir):
    """Process every cleaned JSON file in the input directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return []

    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        print(f"No cleaned JSON files found in {input_dir}")
        return []

    processed_files = []
    for file_path in json_files:
        result = process_file(file_path, output_dir)
        if result is not None:
            processed_files.append(result)

    print(f"Completed chunking {len(processed_files)} file(s).")
    return processed_files


def main():
    """Entry point for the chunking pipeline."""
    project_root = Path(__file__).resolve().parents[2]
    input_dir = project_root / "data" / "cleaned_text"
    output_dir = project_root / "data" / "chunks"

    os.makedirs(output_dir, exist_ok=True)
    process_all_files(input_dir, output_dir)


if __name__ == "__main__":
    main()
