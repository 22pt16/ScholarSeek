
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

INPUT_FILE = Path("search_engine/corpus.json")
OUTPUT_FILE = Path("search_engine/scholarseek_corpus.jsonl")

MAX_PAPERS = 20_000  # Set to None to keep every matching paper


def clean_text(value):
    """Normalize whitespace and safely handle missing values."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split()).strip()


def extract_year(record):
    """Prefer the first version's creation date."""
    versions = record.get("versions") or []

    if isinstance(versions, list) and versions:
        first_version = versions[0]
        if isinstance(first_version, dict):
            created = first_version.get("created", "")
            if created:
                try:
                    return parsedate_to_datetime(created).year
                except (TypeError, ValueError, OverflowError):
                    pass

    # Fallback only: update_date is not necessarily the original year.
    update_date = record.get("update_date", "")
    if isinstance(update_date, str) and len(update_date) >= 4:
        try:
            return datetime.strptime(update_date[:10], "%Y-%m-%d").year
        except ValueError:
            pass

    return None


def convert_record(record):
    """Convert one arXiv record into ScholarSeek's target schema."""
    paper_id = clean_text(record.get("id"))
    title = clean_text(record.get("title"))
    abstract = clean_text(record.get("abstract"))
    authors = clean_text(record.get("authors"))

    raw_categories = clean_text(record.get("categories"))
    categories = raw_categories.split()

    # Keep only papers that have at least one Computer Science category.
    cs_categories = [
        category for category in categories
        if category.startswith("cs.")
    ]

    if not paper_id or not title or not abstract or not cs_categories:
        return None

    # Use the original identifier, not a numeric conversion.
    paper_url = f"https://arxiv.org/abs/{paper_id}"

    return {
        "id": paper_id,
        "title": title,
        "authors": authors,
        "year": extract_year(record),
        "abstract": abstract,
        "keywords": [],
        "category": " ".join(cs_categories),
        "doi": clean_text(record.get("doi")) or None,
        "url": paper_url,
        # Compatibility with the current search-engine interface.
        "content": abstract,
    }


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Cannot find {INPUT_FILE}. Run this script from the project root."
        )

    written = 0
    skipped = 0
    seen_ids = set()

    with INPUT_FILE.open("r", encoding="utf-8") as source, \
         OUTPUT_FILE.open("w", encoding="utf-8") as destination:

        for line in source:
            if not line.strip():
                continue

            try:
                # json.loads preserves quoted string IDs.
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue

            paper = convert_record(record)

            if paper is None or paper["id"] in seen_ids:
                skipped += 1
                continue

            destination.write(
                json.dumps(paper, ensure_ascii=False) + "\n"
            )
            seen_ids.add(paper["id"])
            written += 1

            if written % 1000 == 0:
                print(f"Converted {written:,} papers...")

            if MAX_PAPERS is not None and written >= MAX_PAPERS:
                break

    print("\nConversion complete!")
    print(f"Papers written: {written:,}")
    print(f"Records skipped: {skipped:,}")
    print(f"Output file: {OUTPUT_FILE.resolve()}")


if __name__ == "__main__":
    main()
