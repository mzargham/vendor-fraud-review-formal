"""Shared paths and helpers for the executability contract."""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SYSML = ROOT / "toolchain" / "bin" / "sysml"
MODEL = ROOT / "model" / "vendor-fraud-review.sysml"
VOCABULARY = ROOT / "vocabulary" / "op-concepts.ttl"
SOURCES = ROOT / "sources" / "sources.ttl"
TRACK = ROOT / "track" / "run-001.trig"
CITATION_SHAPES = ROOT / "shapes" / "citation.shapes.ttl"
TRACK_SHAPES = ROOT / "shapes" / "track.shapes.ttl"
CX_TRACK = ROOT / "counterexamples" / "track-missing-approval.trig"
CX_VOCAB = ROOT / "counterexamples" / "vocabulary-uncited.ttl"
CX_MODEL = ROOT / "counterexamples" / "run-unattended.sysml"
QUERIES = ROOT / "queries"
GAPS = ROOT / "open-questions" / "computability-gaps.md"
ADJUDICATIONS = ROOT / "open-questions" / "adjudication-log.md"
INDEX = ROOT / "index.md"
MYST_CONFIG = ROOT / "myst.yml"
REFERENCES = ROOT / "references.bib"
CHAPTERS = [
    ROOT / "chapters" / "01-pinned-source.ipynb",
    ROOT / "chapters" / "02-op-as-assembly.ipynb",
    ROOT / "chapters" / "03-worked-examples.ipynb",
    ROOT / "chapters" / "04-one-type-three-semantics.ipynb",
    ROOT / "chapters" / "05-the-track.ipynb",
    ROOT / "chapters" / "06-open-questions.ipynb",
]

VFR = "https://example.org/vfr#"
EARL = "http://www.w3.org/ns/earl#"


def run_sysml(*args: str) -> subprocess.CompletedProcess:
    """Invoke the pinned OpenSysML binary; caller inspects returncode/stdout."""
    return subprocess.run(
        [str(SYSML), *args], capture_output=True, text=True, cwd=ROOT
    )


def normalized(text: str) -> str:
    """Normalization for the verbatim check: drop parentheticals, whitespace, case."""
    return re.sub(r"\s+", "", re.sub(r"\([^)]*\)", "", text)).lower()


def _pdf_raw() -> str:
    pdfs = sorted((ROOT / "sources").glob("*.pdf"))
    assert len(pdfs) == 1, "exactly one pinned PDF snapshot expected in sources/"
    out = subprocess.run(
        ["pdftotext", "-layout", str(pdfs[0]), "-"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


@pytest.fixture(scope="session")
def pdf_text() -> str:
    """Full text of the pinned whitepaper snapshot, normalized."""
    return normalized(_pdf_raw())


@pytest.fixture(scope="session")
def pdf_sections() -> dict:
    """{'§n.m': normalized section span} from the pinned snapshot, split on
    the numbered section headings; a citation is section-correct only if
    its text appears inside the span its locator names."""
    raw = _pdf_raw()
    headings = list(re.finditer(r"^(\d+\.\d+)\s+\S", raw, re.M))
    assert len(headings) >= 15, "section headings not found in the pinned snapshot"
    sections = {}
    for i, m in enumerate(headings):
        end = headings[i + 1].start() if i + 1 < len(headings) else len(raw)
        sections["§" + m.group(1)] = normalized(raw[m.start():end])
    return sections


@pytest.fixture(scope="session")
def vocabulary_graph():
    import rdflib

    g = rdflib.Graph()
    g.parse(VOCABULARY, format="turtle")
    g.parse(SOURCES, format="turtle")
    return g


@pytest.fixture(scope="session")
def track_dataset():
    import rdflib

    ds = rdflib.Dataset(default_union=True)
    ds.parse(TRACK, format="trig")
    return ds


@pytest.fixture(scope="session")
def cx_track_dataset():
    import rdflib

    ds = rdflib.Dataset(default_union=True)
    ds.parse(CX_TRACK, format="trig")
    return ds
