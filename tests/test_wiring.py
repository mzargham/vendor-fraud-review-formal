"""Wiring-level checks over the RDF conversion.

`-validate -strict` accepts a type-mismatched connect (probed 2026-09-04),
so the wiring rules live here: the model holds the wiring, code over the
conversion holds the wiring rules. Component values and system aggregates
are checked by satisfy; THESE tests check that the seams themselves are
sound and complete.
"""
import rdflib
import pytest

from conftest import MODEL, ROOT, run_sysml

MISWIRED = ROOT / "counterexamples" / "miswired.sysml"

SYSML = rdflib.Namespace("https://www.omg.org/spec/SysML#")
SYSX = rdflib.Namespace("urn:opensysml:sysml:")


def _converted(path):
    r = run_sysml(str(path), "-convert", "ttl")
    assert r.returncode == 0, f"-convert ttl failed for {path}:\n{r.stderr}"
    g = rdflib.Graph()
    g.parse(data=r.stdout, format="turtle")
    return g, r.stdout


def _name(graph, node):
    return str(graph.value(node, SYSML.declaredName) or "")


def _owned_by_name(graph, owner, name):
    for node in graph.subjects(SYSML.owner, owner):
        if _name(graph, node) == name:
            return node
    return None


def _seam_end_types(graph, seam_def):
    """Port-def types of a seam definition's ends, ordered by member index
    (conjugation is erased in the conversion; base types compare)."""
    ends = [
        n for n in graph.subjects(SYSML.owner, seam_def)
        if (n, rdflib.RDF.type, SYSML.PortUsage) in graph
    ]
    ends.sort(key=lambda n: int(graph.value(n, SYSX.memberIndex) or 0))
    return [graph.value(n, SYSML.type) for n in ends]


def check_seam_conformance(graph):
    """Return a list of seam-end mismatches (empty = conformant): for every
    interface usage, each connected part.port must be typed by the port def
    the seam definition declares for that end."""
    mismatches = []
    for seam in graph.subjects(rdflib.RDF.type, SYSML.InterfaceUsage):
        seam_def = graph.value(seam, SYSML.type)
        expected = _seam_end_types(graph, seam_def)
        assembly = graph.value(seam, SYSML.owner)
        for fce in graph.objects(seam, SYSX.relatedFeature):
            src = str(graph.value(fce, SYSX.sourceText) or "")
            idx = int(graph.value(fce, SYSX.endIndex) or 0)
            part_name, _, port_name = src.partition(".")
            part_usage = _owned_by_name(graph, assembly, part_name)
            if part_usage is None:
                mismatches.append(f"{_name(graph, seam)}: end '{src}' names no sibling part")
                continue
            part_def = graph.value(part_usage, SYSML.type)
            port_usage = _owned_by_name(graph, part_def, port_name)
            if port_usage is None:
                mismatches.append(f"{_name(graph, seam)}: '{src}' names no port on {_name(graph, part_def)}")
                continue
            actual = graph.value(port_usage, SYSML.type)
            if idx < len(expected) and actual != expected[idx]:
                mismatches.append(
                    f"{_name(graph, seam)}: end '{src}' is {actual} "
                    f"but the seam declares {expected[idx]}"
                )
    return mismatches


@pytest.fixture(scope="module")
def model_graph():
    graph, _ = _converted(MODEL)
    return graph


def _assembly(graph):
    for n in graph.subjects(SYSML.declaredName, rdflib.Literal("VendorFraudReviewOp")):
        if (n, rdflib.RDF.type, SYSML.PartDefinition) in graph:
            return n
    raise AssertionError("VendorFraudReviewOp definition not found in the conversion")


def test_every_policy_engine_input_is_wired(model_graph):
    # Each of the policy engine's four reading inputs is fed by exactly one
    # seam whose other end is an oracle's reading port.
    asm = _assembly(model_graph)
    wired = {}
    for seam in model_graph.subjects(rdflib.RDF.type, SYSML.InterfaceUsage):
        if model_graph.value(seam, SYSML.owner) != asm:
            continue
        for fce in model_graph.objects(seam, SYSX.relatedFeature):
            src = str(model_graph.value(fce, SYSX.sourceText) or "")
            if src.startswith("policyEngine.from"):
                wired.setdefault(src.split(".")[1], []).append(_name(model_graph, seam))
    for inport in ("fromConfidence", "fromConsensus", "fromScanner", "fromRisk"):
        assert len(wired.get(inport, [])) == 1, (
            f"policy-engine input {inport} wired {len(wired.get(inport, []))} times: {wired}"
        )


def test_obligation_and_summary_seams_are_wired(model_graph):
    asm = _assembly(model_graph)
    seams = {
        _name(model_graph, s)
        for s in model_graph.subjects(rdflib.RDF.type, SYSML.InterfaceUsage)
        if model_graph.value(s, SYSML.owner) == asm
    }
    assert "obligationSeam" in seams, "obligations do not reach the humans"
    assert "clearanceSeam" in seams, "clearance does not reach the output producer"


def test_boundary_result_is_bound(model_graph):
    # The assembly's result port is bound to the summary cog's output.
    asm = _assembly(model_graph)
    _, text = _converted(MODEL)
    assert "bind result = summaryCog.summary" in text, (
        "boundary result bind missing from the conversion"
    )
    assert _owned_by_name(model_graph, asm, "result") is not None, (
        "assembly has no result port"
    )


def test_seam_ends_conform_to_their_interface_defs(model_graph):
    mismatches = check_seam_conformance(model_graph)
    assert mismatches == [], f"seam end type mismatches in the model: {mismatches}"


def test_miswired_counterexample_is_refused():
    # validate -strict accepts this file; the wiring rules must not.
    graph, _ = _converted(MISWIRED)
    mismatches = check_seam_conformance(graph)
    assert mismatches, (
        "the miswired counterexample passed the wiring rules: they are toothless"
    )
    assert any("summaryCog.summaryIn" in m for m in mismatches), (
        f"the mismatch report does not name the miswired end: {mismatches}"
    )
