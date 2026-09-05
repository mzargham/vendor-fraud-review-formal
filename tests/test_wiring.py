"""Wiring-level checks over the RDF projection.

`-validate -strict` accepts a type-mismatched connect (probed 2026-09-04),
so the wiring rules live here: the model holds the wiring, code over the
conversion holds the wiring rules. Component values and system aggregates
are checked by satisfy; THESE tests check that the seams themselves are
sound and complete.
"""
import rdflib
import pytest

from conftest import ROOT, run_sysml

MISWIRED = ROOT / "counterexamples" / "miswired.sysml"


def _converted(path):
    r = run_sysml(str(path), "-convert", "ttl")
    assert r.returncode == 0, f"-convert ttl failed for {path}:\n{r.stderr}"
    g = rdflib.Graph()
    g.parse(data=r.stdout, format="turtle")
    return g, r.stdout


def _seam_end_port_types(graph, text):
    """Map each interface usage in the assembly to the port types at its
    connected ends, discovered from the conversion. Returns
    {interface_name: [end_port_type_names]}. Implementation is filled in
    against the actual converter vocabulary."""
    raise NotImplementedError  # replaced during the build once the vocabulary is known


@pytest.fixture(scope="module")
def model_conversion():
    from conftest import MODEL

    return _converted(MODEL)


def test_every_policy_engine_input_is_wired(model_conversion):
    _, text = model_conversion
    for seam in ("confidenceSeam", "consensusSeam", "scannerSeam", "riskSeam"):
        assert seam in text, f"seam {seam} missing from the conversion"
    for inport in ("fromConfidence", "fromConsensus", "fromScanner", "fromRisk"):
        assert inport in text, f"policy-engine input {inport} missing from the conversion"


def test_obligation_and_summary_seams_are_wired(model_conversion):
    _, text = model_conversion
    for seam in ("obligationSeam", "clearanceSeam"):
        assert seam in text, f"seam {seam} missing from the conversion"


def test_boundary_result_is_bound(model_conversion):
    _, text = model_conversion
    assert "result" in text and "summaryCog" in text, (
        "boundary result bind not visible in the conversion"
    )


def test_seam_ends_conform_to_their_interface_defs(model_conversion):
    graph, text = model_conversion
    mismatches = check_seam_conformance(graph, text)
    assert mismatches == [], f"seam end type mismatches in the model: {mismatches}"


def test_miswired_counterexample_is_refused():
    # validate -strict accepts this file; the wiring rules must not.
    graph, text = _converted(MISWIRED)
    mismatches = check_seam_conformance(graph, text)
    assert mismatches, (
        "the miswired counterexample passed the wiring rules: they are toothless"
    )


def check_seam_conformance(graph, text):
    """Return a list of seam-end mismatches (empty = conformant).
    Filled in against the actual converter vocabulary during the build."""
    raise NotImplementedError
