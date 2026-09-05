"""His section 5.6 track.include list and Gate-approval rules are enforced, with teeth."""
import rdflib
from pyshacl import validate

from conftest import (
    CITATION_SHAPES,
    CX_TRACK,
    CX_VOCAB,
    SOURCES,
    TRACK,
    TRACK_SHAPES,
    VOCABULARY,
)


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
