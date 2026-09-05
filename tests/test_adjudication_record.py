"""The judgment layer is itself a computational record.

The executable specification's objectivity is downstream of judgment
calls: where the text corpus under-specified what an implementation
requires, gaps were flagged, characterized, and resolved by a named
adjudicator, and the implementations derive from those rulings. That
chain lives in RDF (open-questions/adjudications.ttl) and is held to the
same discipline as everything else: complete fields, verbatim ruling
text, resolvable implementation anchors, shapes with a counterexample.
"""
import pytest
import rdflib
from pyshacl import validate

from conftest import ROOT, VFR

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


def test_gap_locators_name_real_sections(record, pdf_sections):
    for gap in record.subjects(rdflib.RDF.type, V.ComputabilityGap):
        for part in str(record.value(gap, V.locator)).split(","):
            sec = part.strip()
            assert sec in pdf_sections, f"{gap}: locator {sec!r} names no section"


def test_every_gap_is_fully_characterized(record):
    for gap in record.subjects(rdflib.RDF.type, V.ComputabilityGap):
        for prop in (rdflib.RDFS.label, V.problem, V.locator, V.cites,
                     V.surfacedOn, V.surfacedHow, V.status):
            assert record.value(gap, prop) is not None, f"{gap} missing {prop}"
        rulings = list(record.subjects(V.resolves, gap))
        assert rulings, f"{gap} has no resolving ruling"


def test_every_ruling_and_note_is_attributed_dated_and_ordered(record):
    rulings = set(record.subjects(rdflib.RDF.type, V.Ruling))
    notes = set(record.subjects(rdflib.RDF.type, V.DesignNote))
    reviews = set(record.subjects(rdflib.RDF.type, V.ReviewNote))
    assert len(rulings) == 17, "seventeen rulings expected in the record"
    assert len(notes) == 7, "seven design notes expected in the record"
    assert len(reviews) == 2, "two external reviews expected in the record"
    orders = []
    for entry in rulings | notes | reviews:
        agent = record.value(entry, PROV.wasAttributedTo)
        assert agent is not None, f"{entry} names no adjudicator"
        if entry in reviews:
            assert "reviewer" in str(agent), f"{entry} attributed to {agent}, not a reviewer"
        else:
            assert "mzargham" in str(agent), f"{entry} attributed to {agent}, not mzargham"
        assert record.value(entry, PROV.generatedAtTime) is not None, f"{entry} undated"
        text = record.value(entry, V.rulingText) or record.value(entry, V.noteText)
        assert text is not None, f"{entry} carries no verbatim text"
        assert record.value(entry, V.changeNote) is not None, f"{entry} has no change note"
        orders.append(int(record.value(entry, V.order)))
    assert sorted(orders) == list(range(1, len(orders) + 1)), (
        "log entry order must be a contiguous sequence"
    )


def test_every_resolving_ruling_has_an_implementation(record):
    exempt = {"ruling-gap04-deferral"}
    for ruling in record.subjects(rdflib.RDF.type, V.Ruling):
        if str(ruling).rsplit("#", 1)[-1] in exempt:
            continue
        impls = list(record.subjects(PROV.wasDerivedFrom, ruling))
        assert impls, f"{ruling} resolved a gap but derives no implementation"


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
