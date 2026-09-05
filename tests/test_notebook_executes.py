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


def test_notebook_shows_the_satisfy_verdicts(executed_outputs):
    assert "satisfy exit code: 0" in executed_outputs, "clean run's exit 0 not shown"
    assert "satisfy exit code: 1" in executed_outputs, "counterexample's exit 1 not shown"


def test_notebook_shows_the_shacl_inversion(executed_outputs):
    assert "conforms: True" in executed_outputs, "run-001 conformance not shown"
    assert "conforms: False" in executed_outputs, "counterexample non-conformance not shown"


def test_notebook_shows_the_outcome_vocabulary(executed_outputs):
    assert "cantTell" in executed_outputs, "the cantTell outcome is not demonstrated"
