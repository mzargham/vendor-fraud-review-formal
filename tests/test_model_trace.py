"""Every named model element is traceable.

model/trace.ttl maps each named element of the executable model to its
provenance: grounded in the pinned whitepaper (locator, with quotes
verified verbatim inside the cited section), derived from a recorded
ruling or design note of the named adjudicator, or declared scaffolding
with a rationale. The map must be complete in both directions.
"""
import re

import pytest
import rdflib
from pyshacl import validate

from conftest import MODEL, ROOT, VFR

TRACE = ROOT / "model" / "trace.ttl"
TRACE_SHAPES = ROOT / "shapes" / "trace.shapes.ttl"
CX_TRACE = ROOT / "counterexamples" / "trace-unprovenanced.ttl"
RECORD = ROOT / "open-questions" / "adjudications.ttl"

V = rdflib.Namespace(VFR)
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")


def model_elements():
    """{name: kind} for every named definition and traced usage in the
    model — the same inventory the trace must cover exactly."""
    source = MODEL.read_text()
    elements = {}

    def add(names, kind):
        for name in names:
            assert name not in elements, f"duplicate element name: {name}"
            elements[name] = kind

    add(re.findall(r"enum def (\w+)", source), "enum def")
    add(re.findall(r"item def (\w+)", source), "item def")
    add(re.findall(r"port def (\w+)", source), "port def")
    add(re.findall(r"(?:abstract )?part def (\w+)", source), "part def")
    add(re.findall(r"interface def (\w+)", source), "interface def")
    add(re.findall(r"requirement def <'([A-Z]+-\d+)'>", source), "requirement def")
    add(re.findall(r"verification def (\w+)", source), "verification def")
    add(re.findall(r"interface (\w+) : \w+Seam connect", source), "seam")
    params = re.search(r"part def ValidationStrategyParameters \{.*?\n        \}", source, re.S)
    add(re.findall(r"attribute (\w+) : [\w:]+ =", params.group(0)), "parameter")
    add(re.findall(r"part (\w+Context)\b", source), "context")
    return elements


@pytest.fixture(scope="module")
def trace():
    g = rdflib.Graph()
    g.parse(TRACE, format="turtle")
    return g


def test_trace_covers_every_model_element_exactly(trace):
    expected = model_elements()
    traced = {
        str(trace.value(e, V.elementName)): str(trace.value(e, V.kind))
        for e in trace.subjects(rdflib.RDF.type, V.ModelElement)
    }
    missing = set(expected) - set(traced)
    extra = set(traced) - set(expected)
    assert not missing, f"model elements with no trace entry: {sorted(missing)}"
    assert not extra, f"trace entries for elements not in the model: {sorted(extra)}"
    for name, kind in expected.items():
        assert traced[name] == kind, f"{name}: trace kind {traced[name]!r} != model {kind!r}"


def test_every_entry_has_a_provenance(trace):
    for e in trace.subjects(rdflib.RDF.type, V.ModelElement):
        grounded = list(trace.objects(e, V.groundedIn))
        rulings = list(trace.objects(e, V.derivedFromRuling))
        notes = list(trace.objects(e, V.derivedFromNote))
        scaffold = trace.value(e, V.scaffoldRationale)
        assert grounded or rulings or notes or scaffold is not None, (
            f"{trace.value(e, V.elementName)} traces to nothing: not the source, "
            "not a ruling, not declared scaffolding"
        )


def test_groundings_name_real_sections_and_quotes_are_in_section(trace, pdf_sections):
    from conftest import normalized

    checked = 0
    for e in trace.subjects(rdflib.RDF.type, V.ModelElement):
        for locator in trace.objects(e, V.groundedIn):
            for part in str(locator).split(","):
                sec = part.strip()
                assert sec in pdf_sections, (
                    f"{trace.value(e, V.elementName)}: locator {sec!r} names no section"
                )
        quote = trace.value(e, V.quote)
        if quote is not None:
            locator = str(trace.value(e, V.groundedIn)).split(",")[0].strip()
            assert normalized(str(quote)) in pdf_sections[locator], (
                f"{trace.value(e, V.elementName)}: quote not verbatim in {locator}: {quote}"
            )
            checked += 1
    assert checked >= 10, "the grounded entries should carry section-verified quotes"


def test_ruling_and_note_references_resolve(trace):
    record = rdflib.Graph()
    record.parse(RECORD, format="turtle")
    rulings = set(record.subjects(rdflib.RDF.type, V.Ruling))
    notes = set(record.subjects(rdflib.RDF.type, V.DesignNote))
    for e in trace.subjects(rdflib.RDF.type, V.ModelElement):
        for r in trace.objects(e, V.derivedFromRuling):
            assert r in rulings, f"{trace.value(e, V.elementName)}: unknown ruling {r}"
        for n in trace.objects(e, V.derivedFromNote):
            assert n in notes, f"{trace.value(e, V.elementName)}: unknown note {n}"


def test_trace_conforms_and_the_unprovenanced_counterexample_fails(trace):
    conforms, _, report = validate(trace, shacl_graph=str(TRACE_SHAPES))
    assert conforms, f"the trace fails its own shapes:\n{report}"
    cx = rdflib.Graph()
    cx.parse(CX_TRACE, format="turtle")
    conforms, _, report = validate(cx, shacl_graph=str(TRACE_SHAPES))
    assert not conforms, "an unprovenanced element conforms: trace shapes are toothless"
    assert "judgment" in report.lower() or "trace" in report.lower(), (
        f"the violation message does not carry the traceability requirement:\n{report}"
    )
