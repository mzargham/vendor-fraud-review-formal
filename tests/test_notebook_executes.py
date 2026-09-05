"""The readable artifact IS an execution, not prose about one.

demonstration.ipynb must execute headlessly top-to-bottom with no errors,
and its executed cells must produce the contracted signals.
"""
import nbformat
import pytest
from nbclient import NotebookClient

from conftest import NOTEBOOK, ROOT


@pytest.fixture(scope="module")
def executed_outputs():
    nb = nbformat.read(NOTEBOOK, as_version=4)
    client = NotebookClient(
        nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
    )
    client.execute()  # raises CellExecutionError on any failing cell
    chunks = []
    for cell in nb.cells:
        for out in cell.get("outputs", []):
            if out.get("output_type") == "stream":
                chunks.append(out.get("text", ""))
            elif "text/plain" in out.get("data", {}):
                chunks.append(out["data"]["text/plain"])
    return "\n".join(chunks)


def test_notebook_executes_without_error(executed_outputs):
    assert executed_outputs.strip(), "notebook executed but produced no output"


def test_notebook_shows_the_satisfy_exit_codes(executed_outputs):
    assert "satisfy exit code: 0" in executed_outputs, "clean run's exit 0 not shown"
    assert "satisfy exit code: 1" in executed_outputs, "counterexample's exit 1 not shown"


def test_notebook_shows_the_shacl_inversion(executed_outputs):
    assert "conforms: True" in executed_outputs, "run-001 conformance not shown"
    assert "conforms: False" in executed_outputs, "counterexample non-conformance not shown"


def test_notebook_shows_the_outcome_vocabulary(executed_outputs):
    assert "cantTell" in executed_outputs, "the cantTell outcome is not demonstrated"


def test_notebook_narrates_the_worked_examples(executed_outputs):
    # Narrated scenarios: the happy path, each gate binding (obligation
    # discharged vs neglected), and the threshold rule catching a mislabel.
    for marker in (
        "scenario 'happy-path': POLICY SATISFIED — aggregate: executed",
        "scenario 'low-confidence-reviewed': POLICY SATISFIED — aggregate: executed",
        "scenario 'low-confidence-neglected': POLICY VIOLATED",
        "scenario 'split-cogs-expert-reviewed': POLICY SATISFIED — aggregate: executed",
        "scenario 'pii-stop-and-escalate': POLICY SATISFIED — aggregate: noOp",
        "scenario 'pii-stopped-but-emitted': POLICY VIOLATED",
        "scenario 'high-risk-vendor-approved': POLICY SATISFIED — aggregate: executed",
        "scenario 'mislabeled-confidence': POLICY VIOLATED",
    ):
        assert marker in executed_outputs, f"missing worked example: {marker}"


def test_notebook_shows_one_type_three_semantics(executed_outputs):
    # GAP-04 ruling: the rule does not say what the number is. Exhibit a
    # type signature and three type-satisfying metrics with different
    # semantics, evaluated on the SAME answer matrix — the gate must fire
    # under at least one and stay quiet under at least one, showing that
    # correctly constructed is not the same as fit for purpose.
    for metric in ("dissent-fraction", "strict-quorum-undecodable", "erasure-aware-undecodable"):
        assert metric in executed_outputs, f"metric {metric} not exhibited"
    assert "gate fires: True" in executed_outputs, "no metric fires the gate"
    assert "gate fires: False" in executed_outputs, "no metric leaves the gate quiet"
    assert "same answer matrix" in executed_outputs, (
        "the demonstration does not state that all three ran on one matrix"
    )


def test_notebook_shows_the_wiring_and_lifecycle_levels(executed_outputs):
    assert "wiring rules: OK" in executed_outputs, "model wiring rules not demonstrated"
    assert "wiring rules: REFUSED" in executed_outputs, (
        "the miswired counterexample's refusal is not demonstrated"
    )
    assert "running -> stopped" in executed_outputs, (
        "the stopped lifecycle trace is not demonstrated"
    )
    assert "running -> completed" in executed_outputs, (
        "the completed lifecycle trace is not demonstrated"
    )


def test_worked_examples_invoke_the_committed_policy(executed_outputs):
    # The scenarios must run the spec itself, not a re-implementation.
    assert "policy reused byte-identical" in executed_outputs, (
        "worked examples do not attest to reusing the committed policy text"
    )
    assert "mock oracle" in executed_outputs.lower() or "oracle " in executed_outputs, (
        "the mocked oracle calls are not shown"
    )


def test_notebook_shows_the_factored_parameters(executed_outputs):
    assert "confidenceThreshold" in executed_outputs, (
        "the factored policy parameters are not demonstrated"
    )


def test_notebook_shows_the_oracle_citations(executed_outputs):
    assert "responseCode" in executed_outputs or "response code" in executed_outputs, (
        "the oracle interface contract (service/payload/code/response) is not demonstrated"
    )
