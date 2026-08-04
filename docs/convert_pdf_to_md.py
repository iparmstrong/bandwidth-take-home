#!/usr/bin/env python3
"""
PDF to Markdown Converter script for windmill-assesment.
Uses markitdown, pymupdf4llm, and pypdf to convert PDF documents into Markdown text.
Applies post-processing sanitization to fix formatting artifacts (strikethroughs, code block spaces, etc.).
"""

from __future__ import annotations

argparse = None  # type: ignore
import argparse
from pathlib import Path
import re
import sys
from typing import Optional


def clean_markdown(md_text: str) -> str:
    """
    Sanitizes markdown output extracted from PDF conversion, repairing common formatting artifacts.
    """
    # Fix strikethrough artifacts inside identifiers like alert~~i~~d, dry~~r~~un, should<br>~~p~~age
    cleaned = re.sub(r"<br>\s*~~([a-zA-Z0-9_])~~", r"\1", md_text)
    cleaned = re.sub(r"~~([a-zA-Z0-9_])~~", r"\1", cleaned)

    # Fix broken identifiers
    replacements = {
        "alert i d": "alert_id",
        "alert id": "alert_id",
        "dry r un": "dry_run",
        "dry run": "dry_run",
        "should p age": "should_page",
        "should page": "should_page",
        "triggered a t": "triggered_at",
        "triggered at": "triggered_at",
        "probable c ause": "probable_cause",
        "probable cause": "probable_cause",
        "flow i nput.field n ame": "flow_input.field_name",
        "field n ame": "field_name",
        "parse a lert": "parse_alert",
        "test parse a lert": "test_parse_alert",
        "run s cript": "run_script",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)

    # Fix stripped spaces in standard JSON messages inside converted PDF outputs
    cleaned = cleaned.replace(
        '"message":"HTTP5xxerrorrateexceeded5%overa5-minutewindow"',
        '"message": "HTTP 5xx error rate exceeded 5% over a 5-minute window"',
    )

    return cleaned


def convert_pdf_to_markdown(
    pdf_path: str | Path,
    output_path: Optional[str | Path] = None,
    method: str = "auto",
) -> str:
    """
    Converts a PDF file into Markdown format.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Optional path to save the output Markdown file.
        method: Conversion method to use ('auto', 'markitdown', 'pymupdf', 'pypdf').

    Returns:
        The Markdown text content as a string.
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Input PDF file does not exist: {pdf_file}")

    markdown_text = ""

    if method in ("auto", "pypdf"):
        try:
            import pypdf

            reader = pypdf.PdfReader(str(pdf_file))
            pages_text = []
            for i, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text:
                    pages_text.append(f"<!-- Page {i} -->\n{text}")
            markdown_text = "\n\n".join(pages_text)
        except Exception as e:
            if method == "pypdf":
                raise RuntimeError(f"PyPDF conversion failed: {e}") from e
            markdown_text = ""

    if not markdown_text and method in ("auto", "pymupdf"):
        try:
            import pymupdf4llm

            markdown_text = pymupdf4llm.to_markdown(str(pdf_file))
        except Exception as e:
            if method == "pymupdf":
                raise RuntimeError(f"PyMuPDF4LLM conversion failed: {e}") from e
            markdown_text = ""

    if not markdown_text and method in ("auto", "markitdown"):
        try:
            from markitdown import MarkItDown

            md = MarkItDown()
            result = md.convert(str(pdf_file))
            markdown_text = result.text_content
        except Exception as e:
            if method == "markitdown":
                raise RuntimeError(f"MarkItDown conversion failed: {e}") from e

    if not markdown_text:
        raise RuntimeError(f"Failed to convert PDF '{pdf_file}' to Markdown with method '{method}'.")

    markdown_text = clean_markdown(markdown_text)

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(markdown_text, encoding="utf-8")

    return markdown_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert PDF documents into Markdown using Python."
    )
    parser.add_argument(
        "pdf_path",
        nargs="?",
        help="Path to the PDF file to convert.",
    )
    parser.add_argument(
        "-i",
        "--input",
        dest="input_pdf",
        help="Path to input PDF file (alternative to positional argument).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Path to the destination Markdown file. If omitted, saves alongside input as .md.",
    )
    parser.add_argument(
        "-m",
        "--method",
        choices=["auto", "markitdown", "pymupdf", "pypdf"],
        default="auto",
        help="Conversion engine to use (default: auto).",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print the converted Markdown to standard output instead of writing to a file.",
    )

    args = parser.parse_args()

    input_path = args.pdf_path or args.input_pdf
    if not input_path:
        parser.error("Please provide an input PDF file path.")

    pdf_file = Path(input_path)
    if not pdf_file.exists():
        print(f"Error: Input file '{pdf_file}' not found.", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if not output_path and not args.stdout:
        output_path = pdf_file.with_suffix(".md")

    try:
        md_content = convert_pdf_to_markdown(
            pdf_path=pdf_file,
            output_path=output_path if not args.stdout else None,
            method=args.method,
        )

        if args.stdout:
            print(md_content)
        else:
            print(f"Successfully converted '{pdf_file}' -> '{output_path}'")

    except Exception as err:
        print(f"Error during conversion: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
