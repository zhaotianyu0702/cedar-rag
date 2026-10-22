"""Load only the six fictional Cedar Lab paragraphs, retaining metadata."""
from dataclasses import dataclass
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Chunk:
    id: str
    filename: str
    text: str


def load_chunks(docs=ROOT / "docs"):
    chunks = []
    expected = {"access.txt": {"A1", "A2"}, "training.txt": {"T1", "T2"},
                "booking.txt": {"B1", "B2"}}
    for filename, ids in expected.items():
        paragraphs = re.split(r"\n\s*\n", (docs / filename).read_text().strip())
        found = []
        for paragraph in paragraphs:
            match = re.fullmatch(r"\[([ATB][12])\] (.+)", paragraph)
            if not match:
                raise ValueError(f"Malformed paragraph in {filename}: {paragraph!r}")
            chunk_id, text = match.groups()
            found.append(chunk_id)
            chunks.append(Chunk(chunk_id, filename, text))
        if set(found) != ids or len(found) != 2:
            raise ValueError(f"Expected exactly {sorted(ids)} in {filename}")
    return sorted(chunks, key=lambda chunk: chunk.id)


QUESTIONS = {
    "Q1": "May a trained graduate student operate the laser alone at 19:00?",
    "Q2": "Can I use the laser without another person present?",
    "Q3": "How frequently must I refresh my laser qualification?",
    "Q4": "What is the laser wavelength?",
}
REQUIRED = {"Q1": {"A1", "A2"}, "Q2": {"A2"}, "Q3": {"T1"}, "Q4": set()}


def positive_k(value):
    import argparse
    try:
        k = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("k must be a positive integer")
    if k < 1:
        raise argparse.ArgumentTypeError("k must be a positive integer")
    return k
