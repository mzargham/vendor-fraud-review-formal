"""The section 5.6 track.include list and Gate-approval rules are enforced, with teeth."""
import rdflib
from pyshacl import validate

from conftest import (
    CITATION_SHAPES,
    CX_TRACK,
    CX_VOCAB,
    ROOT,
    SOURCES,
    TRACK,
    TRACK_SHAPES,
    VOCABULARY,
)

CX_READING = ROOT / "counterexamples" / "track-unsourced-reading.trig"


def _graph(*paths, fmt=None):
    g = rdflib.Dataset(default_union=True)
    for p in paths:
        g.parse(p, format=fmt or ("trig" if str(p).endswith(".trig") else "turtle"))
    return g


def test_vocabulary_conforms_to_citation_shapes():
    conforms, _, report = validate(
        _graph(VOCABULARY, SOURCES), shacl_graph=str(CITATION_SHAPES)
    )
    assert conforms, f"vocabulary fails citation shapes:\n{report}"


def test_uncited_vocabulary_counterexample_fails():
    conforms, _, report = validate(
        _graph(CX_VOCAB, SOURCES), shacl_graph=str(CITATION_SHAPES)
    )
    assert not conforms, "uncited-definition counterexample conforms: shapes are toothless"
    assert "cite" in report.lower(), f"violation message does not name the missing citation:\n{report}"


def test_track_conforms_to_track_shapes():
    conforms, _, report = validate(_graph(TRACK), shacl_graph=str(TRACK_SHAPES))
    assert conforms, f"run-001 fails track shapes:\n{report}"


def test_track_missing_approval_counterexample_fails():
    conforms, _, report = validate(_graph(CX_TRACK), shacl_graph=str(TRACK_SHAPES))
    assert not conforms, "missing-approval counterexample conforms: shapes are toothless"
    assert "approval" in report.lower(), (
        f"violation message does not name the missing human approval:\n{report}"
    )
    assert "obligation" in report.lower(), (
        f"violation message does not name the undischarged obligation (GAP-02 ruling):\n{report}"
    )


def test_execution_without_parameters_fails():
    # WP section 5.3 Track contents include "configuration parameters"; an
    # execution that does not record the parameters it ran with is refused.
    data = rdflib.Graph()
    data.parse(data="""
        @prefix vfr: <https://example.org/vfr#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        <urn:example:run-bare:execution> a vfr:OpExecution ;
            rdfs:label "an execution recording nothing" .
    """, format="turtle")
    conforms, _, report = validate(data, shacl_graph=str(TRACK_SHAPES))
    assert not conforms
    assert "configuration parameters" in report.lower(), (
        f"violation message does not name the missing configuration parameters:\n{report}"
    )


def _bare_execution(extra=""):
    data = rdflib.Graph()
    data.parse(data=f"""
        @prefix vfr: <https://example.org/vfr#> .
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        <urn:example:run-x:execution> a vfr:OpExecution ;
            rdfs:label "a minimal execution" ;
            vfr:framesApplied "f" ; vfr:cogsInvoked "c" ;
            vfr:parameters <urn:example:run-x:params> ;
            {extra}
            rdfs:comment "guard results and prov:used omitted on purpose" .
    """, format="turtle")
    return data


def test_executed_run_without_final_output_fails():
    # GAP-07 adjudication: final_output inclusion is CONDITIONAL — an
    # executed run must retain it.
    conforms, _, report = validate(
        _bare_execution('vfr:aggregateOutcome "executed" ;'),
        shacl_graph=str(TRACK_SHAPES),
    )
    assert not conforms
    assert "final_output" in report.lower(), (
        f"violation does not name the missing final_output:\n{report}"
    )


def test_stopped_run_with_final_output_fails():
    # GAP-07 adjudication, the other direction: a noOp run transmits
    # nothing, so a final_output on its Track is a violation. This reading
    # departs from the pinned draft's unconditional include list, and the
    # violation message must say so.
    conforms, _, report = validate(
        _bare_execution(
            'vfr:aggregateOutcome "noOp" ; vfr:finalOutput <urn:example:run-x:out> ;'
        ),
        shacl_graph=str(TRACK_SHAPES),
    )
    assert not conforms
    assert "departs from the pinned draft" in report, (
        f"the departure from the pinned draft is not acknowledged in the message:\n{report}"
    )


def test_execution_must_state_its_aggregate_outcome():
    conforms, _, report = validate(_bare_execution(), shacl_graph=str(TRACK_SHAPES))
    assert not conforms
    assert "aggregate outcome" in report.lower(), (
        f"violation does not name the missing aggregate outcome:\n{report}"
    )


def test_unsourced_reading_counterexample_fails():
    # Interface contract (GAP-05 ruling): a reading with no citable oracle
    # call — or an oracle call missing its response code — must be refused.
    conforms, _, report = validate(_graph(CX_READING), shacl_graph=str(TRACK_SHAPES))
    assert not conforms, "unsourced-reading counterexample conforms: shapes are toothless"
    assert "oracle" in report.lower(), (
        f"violation message does not name the missing oracle citation:\n{report}"
    )
