"""The no-silent-alteration rule is itself machine-checked.

Every `provisional: GAP-nn` or `adjudicated: GAP-nn` marker in the
substrate names a gap that exists in the judgment record
(open-questions/adjudications.ttl). A reading stays provisional until a
ruling by the named adjudicator is recorded.
"""
import re
from pathlib import Path

import rdflib

from conftest import RECORD, ROOT, VFR

SUBSTRATE_GLOBS = (
    "model/*.sysml",
    "model/*.ttl",
    "vocabulary/*.ttl",
    "track/*.trig",
    "shapes/*.ttl",
    "queries/*.rq",
    "counterexamples/*",
    "exhibits.py",
    "index.md",
    "chapters/*.ipynb",
)


def _substrate_files():
    files: list[Path] = []
    for pattern in SUBSTRATE_GLOBS:
        files.extend(ROOT.glob(pattern))
    return files


def _gap_ids():
    g = rdflib.Graph()
    g.parse(RECORD, format="turtle")
    return {
        str(gap).rsplit("#", 1)[-1]
        for gap in g.subjects(
            rdflib.RDF.type, rdflib.URIRef(VFR + "ComputabilityGap")
        )
    }


def test_the_record_holds_gaps():
    assert _gap_ids(), "the judgment record holds no gaps"


def test_every_gap_marker_names_a_recorded_gap():
    ids = _gap_ids()
    for f in _substrate_files():
        for marker in re.findall(
            r"(?:provisional|adjudicated):\s*(GAP-\d+)", f.read_text()
        ):
            assert marker in ids, (
                f"{f.name} marks {marker} but the judgment record has no such gap"
            )