"""The judgment layer is itself a computational record.

The executable specification's objectivity is downstream of judgment
calls: where the text corpus under-specified what an implementation
requires, gaps were flagged, characterized, and resolved by a named
adjudicator, and the implementations derive from those rulings. That
chain lives in RDF (open-questions/adjudications.ttl) and is held to the
same discipline as everything else: complete fields, verbatim ruling
text, resolvable implementation anchors, shapes with a counterexample.
"""
import re

import pytest
import rdflib
from pyshacl import validate

from conftest import ADJUDICATIONS, GAPS, ROOT, VFR, normalized

RECORD = ROOT / "open-questions" / "adjudications.ttl"
RECORD_SHAPES = ROOT / "shapes" / "adjudication.shapes.ttl"
CX_RECORD = ROOT / "counterexamples" / "adjudication-unattributed.ttl"

PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
V = rdflib.Namespace(VFR)


@pytest.fixture(scope="module")
def record():
    g = rdflib.Graph()
    g.parse(RECORD, format="turtle")
    return g


def test_every_markdown_gap_is_in_the_record_and_vice_versa(record):
    md_ids = set(re.findall(r"^##\s+(GAP-\d+)", GAPS.read_text(), flags=re.M))
    rdf_ids = {
        str(g).rsplit("#", 1)[-1]
        for g in record.subjects(rdflib.RDF.type, V.ComputabilityGap)
    }
    assert rdf_ids == md_ids, (
        f"gap ids diverge between the record and the markdown: "
        f"only in RDF {rdf_ids - md_ids}, only in markdown {md_ids - rdf_ids}"
    )


def test_every_gap_is_fully_characterized(record):
    for gap in record.subjects(rdflib.RDF.type, V.ComputabilityGap):
        for prop in (rdflib.RDFS.label, V.problem, V.locator, V.cites,
                     V.surfacedOn, V.surfacedHow, V.status):
            assert record.value(gap, prop) is not None, f"{gap} missing {prop}"
        rulings = list(record.subjects(V.resolves, gap))
        assert rulings, f"{gap} has no resolving ruling"


def test_every_ruling_is_attributed_dated_and_verbatim(record):
    log = normalized(ADJUDICATIONS.read_text())
    rulings = list(record.subjects(rdflib.RDF.type, V.Ruling))
    assert len(rulings) >= 10, "expected at least ten rulings in the record"
    for ruling in rulings:
        agent = record.value(ruling, PROV.wasAttributedTo)
        assert agent is not None, f"{ruling} names no adjudicator"
        assert "mzargham" in str(agent), f"{ruling} attributed to {agent}, not mzargham"
        assert record.value(ruling, PROV.generatedAtTime) is not None, f"{ruling} undated"
        text = record.value(ruling, V.rulingText)
        assert text is not None, f"{ruling} carries no ruling text"
        assert normalized(str(text)) in log, (
            f"{ruling} text is not verbatim from adjudication-log.md"
        )


def test_every_implementation_anchor_resolves(record):
    impls = list(record.subjects(rdflib.RDF.type, V.Implementation))
    assert len(impls) >= 12, "expected implementations for every ruling"
    for impl in impls:
        ruling = record.value(impl, PROV.wasDerivedFrom)
        assert ruling is not None, f"{impl} derives from no ruling"
        in_file = str(record.value(impl, V.inFile))
        anchor = str(record.value(impl, V.anchor))
        path = ROOT / in_file
        assert path.exists(), f"{impl}: file does not exist: {in_file}"
        assert anchor in path.read_text(), f"{impl}: anchor {anchor!r} not found in {in_file}"


def test_gaps_page_is_generated_from_the_record():
    # computability-gaps.md is a view of the record, byte-identical to a
    # fresh render — one source of truth, no drift.
    import sys

    sys.path.insert(0, str(ROOT / "checks"))
    import render_gaps

    assert render_gaps.PAGE.read_text() == render_gaps.render(), (
        "computability-gaps.md has drifted from adjudications.ttl; "
        "regenerate with checks/render_gaps.py"
    )
    assert "GENERATED from adjudications.ttl" in render_gaps.PAGE.read_text()


def test_record_conforms_and_the_unattributed_counterexample_fails(record):
    conforms, _, report = validate(record, shacl_graph=str(RECORD_SHAPES))
    assert conforms, f"the adjudication record fails its own shapes:\n{report}"
    cx = rdflib.Graph()
    cx.parse(CX_RECORD, format="turtle")
    conforms, _, report = validate(cx, shacl_graph=str(RECORD_SHAPES))
    assert not conforms, "an unattributed ruling conforms: the record's shapes are toothless"
    assert "adjudicator" in report.lower(), (
        f"the violation does not name the missing adjudicator:\n{report}"
    )
