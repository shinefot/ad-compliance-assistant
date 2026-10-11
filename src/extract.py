"""
extract.py — STEP 1 of the pipeline. Reads every AD PDF and asks Claude to fill
in an ADRecord for it. Results are saved to data/extracted.json.

Run:  python -m src.extract

It skips PDFs it has already processed, so re-running is cheap.
To redo everything (e.g. after improving the prompt), delete data/extracted.json.
"""
import json
import sys

from . import config
from .llm import get_llm, model_name
from .pdf_utils import pages_as_marked_text, read_pages
from .schema import ADExtraction, ADRecord


def load_records() -> list[ADRecord]:
    if not config.EXTRACTED_FILE.exists():
        return []
    raw = json.loads(config.EXTRACTED_FILE.read_text(encoding="utf-8"))
    return [ADRecord(**r) for r in raw]


def save_records(records: list[ADRecord]) -> None:
    config.EXTRACTED_FILE.write_text(
        json.dumps([r.model_dump(mode="json") for r in records], indent=2), encoding="utf-8"
    )


def extract_one(llm, system_prompt: str, authority: str, pdf_path) -> ADRecord:
    pages = read_pages(pdf_path)
    if not pages:
        raise ValueError("No text found. The PDF may be a scanned image.")
    text = pages_as_marked_text(pages)
    # with_structured_output forces Claude to answer by filling in ADExtraction.
    structured = llm.with_structured_output(ADExtraction)
    result: ADExtraction = structured.invoke(
        [
            ("system", system_prompt),
            ("human", f"Issuing authority folder: {authority}\n\nAD text:\n\n{text}"),
        ]
    )
    return ADRecord(**result.model_dump(), source_file=f"{pdf_path.parent.name}/{pdf_path.name}")


def main() -> None:
    records = load_records()
    done = {r.source_file for r in records}
    system_prompt = config.load_prompt("extractor")
    llm = get_llm("extractor")
    print(f"Using model {model_name('extractor')} with prompt {config.PROMPT_VERSIONS['extractor']}")

    failures = 0
    for authority, folder in config.AD_DIRS.items():
        for pdf in sorted(folder.glob("*.pdf")):
            key = f"{folder.name}/{pdf.name}"
            if key in done:
                print(f"  skip  {key} (already extracted)")
                continue
            try:
                rec = extract_one(llm, system_prompt, authority, pdf)
                records.append(rec)
                save_records(records)  # save after each file so a crash loses nothing
                print(f"  ok    {key} -> AD {rec.ad_number} | models: {', '.join(rec.applicable_models)}")
            except Exception as e:  # keep going; report at the end
                failures += 1
                print(f"  FAIL  {key}: {e}")

    print(f"\nDone. {len(records)} ADs in {config.EXTRACTED_FILE.name}, {failures} failures.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
