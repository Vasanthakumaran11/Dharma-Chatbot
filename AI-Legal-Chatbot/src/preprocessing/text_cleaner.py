import json
import os
import re
from pathlib import Path


def load_json(file_path):
    """Load a JSON file and return its parsed content."""
    with open(file_path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def clean_text(text):
    """Clean OCR/PDF extraction noise while preserving legal content and formatting."""
    if not isinstance(text, str):
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", " ")

    # Remove invisible unicode characters.
    text = re.sub(r"[\u200b\ufeff\xa0]", " ", text)

    # Normalize repeated whitespace except line breaks.
    text = re.sub(r"[ ]{2,}", " ", text)

    # Split into lines so we can remove noisy lines individually.
    lines = text.split("\n")
    cleaned_lines = []
    blank_run = 0

    for raw_line in lines:
        line = raw_line.strip()

        # Remove corrupted font extraction artifacts.
        line = re.sub(
            r"\b(?:vlk[/\s]*kkj(?:\.k)?|Hkkx|izkf[/\s]*kdkj|fnYyh|lañ)\b",
            "",
            line,
            flags=re.IGNORECASE,
        )
        line = re.sub(r"\s+", " ", line).strip()

        # Remove page number lines such as "10", "-10-", "Page 10", "— 10 —".
        if re.fullmatch(r"(?:page\s*)?\d+", line, flags=re.IGNORECASE):
            continue
        if re.fullmatch(r"[-–—\s]*\d+[-–—\s]*", line):
            continue
        if re.fullmatch(r"[—\-\s]*\d+[—\-\s]*", line):
            continue

        # Remove common Gazette/publication header lines.
        if re.fullmatch(r"(?:EXTRAORDINARY|PUBLISHED BY AUTHORITY|THE GAZETTE OF INDIA|भारत का राजपत्र|MINISTRY OF LAW AND JUSTICE|GOVERNMENT OF INDIA|LEGISLATIVE DEPARTMENT|NEW DELHI|REGISTERED NO\.|REGISTERED NO|NO\.[\s\d]+|PART II|SECTION 1|CG-DL(?:-E)?|DL-\(N\)|xxxGIDHxxx|xxxGIDExxx)", line, flags=re.IGNORECASE):
            continue

        # Remove lines that are clearly publication metadata.
        if re.match(r"^(?:[A-Z0-9\-\s]+)$", line) and any(
            token in line.upper()
            for token in [
                "EXTRAORDINARY",
                "PUBLISHED",
                "AUTHORITY",
                "GAZETTE",
                "MINISTRY",
                "JUSTICE",
                "LEGISLATIVE",
                "REGISTERED",
                "CG-DL",
                "DL-(N)",
            ]
        ):
            continue

        # Remove lines that are just publication dates or numbering references.
        if re.fullmatch(r"(?:[A-Z][a-z]+,\s*)?(?:the\s+)?\d+(?:st|nd|rd|th)?\s+\w+\s+\d{4}.*", line):
            continue
        if re.fullmatch(r"\d{4}.*", line):
            continue

        # Remove empty lines but collapse repeated blank lines into a single blank line.
        if not line:
            blank_run += 1
            if blank_run <= 1:
                cleaned_lines.append("")
            continue

        blank_run = 0
        cleaned_lines.append(line)

    # Remove leading/trailing blank lines and normalize final whitespace.
    cleaned_text = "\n".join(cleaned_lines).strip()
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    return cleaned_text


def clean_page(page):
    """Clean a single page dictionary and return a new page dictionary."""
    if not isinstance(page, dict):
        return page

    cleaned_page = dict(page)
    if "text" in cleaned_page:
        cleaned_page["text"] = clean_text(cleaned_page.get("text", ""))
    return cleaned_page


def process_file(input_path, output_dir):
    """Clean one extracted JSON file and write the cleaned JSON to the output directory."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Processing: {input_path.name}")

    try:
        data = load_json(input_path)
        if not isinstance(data, dict):
            raise ValueError("Loaded JSON is not an object")

        pages = data.get("pages", [])
        cleaned_pages = [clean_page(page) for page in pages]
        cleaned_data = dict(data)
        cleaned_data["pages"] = cleaned_pages

        output_path = output_dir / input_path.name
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(cleaned_data, handle, ensure_ascii=False, indent=4)
            handle.write("\n")

        print(f"Saved: {output_path}")
        return output_path
    except Exception as exc:
        print(f"Error processing {input_path.name}: {exc}")
        return None


def process_all_files(input_dir, output_dir):
    """Process every JSON file in the input directory."""
    input_dir = Path(input_dir)
    output_dir = Path(output_dir)

    if not input_dir.exists():
        print(f"Input directory not found: {input_dir}")
        return []

    json_files = sorted(input_dir.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return []

    processed_files = []
    for file_path in json_files:
        result = process_file(file_path, output_dir)
        if result is not None:
            processed_files.append(result)

    print(f"Completed processing {len(processed_files)} file(s).")
    return processed_files


def main():
    """Entry point for the cleaner pipeline."""
    project_root = Path(__file__).resolve().parents[2]
    input_dir = project_root / "data" / "extracted_text"
    output_dir = project_root / "data" / "cleaned_text"

    os.makedirs(output_dir, exist_ok=True)
    process_all_files(input_dir, output_dir)


if __name__ == "__main__":
    main()
