#!/usr/bin/env python3
"""Ingest job listings CSV into Qdrant vector store.

Usage:
    python scripts/ingest.py [path/to/jobs.csv]

Defaults to 'LF Jobs - LF Jobs.csv' in the RAG directory.
"""
import sys
from pathlib import Path

# Allow running from the RAG directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings
from app.pipeline.ingest import run_ingestion


def main():
    settings = Settings()

    if len(sys.argv) > 1:
        csv_path = sys.argv[1]
    else:
        csv_path = str(Path(__file__).resolve().parent.parent / "LF Jobs - LF Jobs.csv")

    if not Path(csv_path).exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    count = run_ingestion(csv_path, settings)
    print(f"\nDone. {count} chunks indexed.")


if __name__ == "__main__":
    main()
