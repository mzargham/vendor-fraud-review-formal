"""The readable artifact IS an execution, not prose about one.

The walkthrough is a chaptered MyST book. Every chapter notebook must
execute headlessly top-to-bottom with no errors; the contracted signals
must appear in the chapter that narrates them; and the committed outputs
must equal a fresh execution cell-for-cell, because the rendered site
shows the committed outputs.
"""
import nbformat
import pytest
from nbclient import NotebookClient

from conftest import CHAPTERS, ROOT


def _cell_text(cell):
    chunks = []
    for out in cell.get("outputs", []):
        if out.get("output_type") == "stream":
            chunks.append(out.get("text", ""))
        else:
            data = out.get("data", {})
            for mime in ("text/markdown", "text/html", "text/plain"):
                if mime in data:
                    chunks.append(data[mime])
                    break
    return "".join(chunks)


def _execute(path):
    nb = nbformat.read(path, as_version=4)
    client = NotebookClient(
        nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(ROOT)}}
    )
    client.execute()  # raises CellExecutionError on any failing cell
    return nb


@pytest.fixture(scope="module")
def executed_chapters():
    """{chapter stem: freshly executed notebook}, in TOC order."""
    return {path.stem: _execute(path) for path in CHAPTERS}


@pytest.fixture(scope="module")
def chapter_outputs(executed_chapters):
    return {
        stem: "\n".join(_cell_text(c) for c in nb.cells if c.cell_type == "code")
        for stem, nb in executed_chapters.items()
    }


@pytest.fixture(scope="module")
def combined(chapter_outputs):
    return "\n".join(chapter_outputs.values())


def test_every_chapter_exists_and_produces_output(chapter_outputs):
    for stem, text in chapter_outputs.items():
        assert text.strip(), f"chapter {stem} executed but produced no output"


def test_committed_outputs_equal_fresh_execution(executed_chapters):
    # The site renders the committed outputs; this proves the site shows
    # exactly what execution shows.
    for path in CHAPTERS:
        committed = nbformat.read(path, as_version=4)
        fresh = executed_chapters[path.stem]
        assert len(committed.cells) == len(fresh.cells)
        for i, (c, f) in enumerate(zip(committed.cells, fresh.cells)):
            if c.cell_type != "code":
                continue
            if "latest-report" in c.get("metadata", {}).get("tags", []):
                # The checks-report cell shows whatever the latest
                # checks/out/report.json says; that is the point of it.
                continue
            assert _cell_text(c) == _cell_text(f), (
                f"{path.name} cell {i}: committed output differs from fresh execution"
            )


def test_chapter_01_pins_the_source_and_the_vocabulary(chapter_outputs):
    text = chapter_outputs["01-pinned-source"]
    assert "match         : True" in text, "snapshot hash agreement not shown"
    assert text.count("✓ verbatim") >= 10, "verbatim vocabulary table not shown"
    # Definitions are full text, never truncated: the longest one must end
    # with its own final phrase.
    assert "when human review is required." in text, (
        "vocabulary definitions are truncated in the rendered table"
    )


def test_chapter_02_shows_the_satisfy_exit_codes(chapter_outputs):
    text = chapter_outputs["02-op-as-assembly"]
    assert "satisfy exit code: 0" in text, "clean run's exit 0 not shown"
    assert "satisfy exit code: 1" in text, "counterexample's exit 1 not shown"
    assert "confidenceThreshold" in text, "the factored policy parameters are not demonstrated"


def test_chapter_02_renders_model_excerpts_readably(chapter_outputs):
    # Raw part-def dumps are not readable for the ML/DS audience: the
    # parameters, gates, and seams must each render as a parsed table
    # (derived from the model text, not retyped), and the verbatim
    # source excerpts shown must be dedented to the margin.
    text = chapter_outputs["02-op-as-assembly"]
    assert text.count("<table") >= 3, "params, gates, and seams must render as tables"
    assert "- if: confidence" in text, "gate table must carry the manifest rules"
    assert "\n            attribute" not in text, "source excerpts must be dedented"


def test_chapter_02_shows_the_wiring_and_lifecycle_levels(chapter_outputs):
    text = chapter_outputs["02-op-as-assembly"]
    assert "wiring rules: OK" in text, "model wiring rules not demonstrated"
    assert "wiring rules: REFUSED" in text, (
        "the miswired counterexample's refusal is not demonstrated"
    )
    assert "running -> stopped" in text, "the stopped lifecycle trace is not demonstrated"
    assert "running -> completed" in text, "the completed lifecycle trace is not demonstrated"


def test_chapter_03_narrates_the_worked_examples(chapter_outputs):
    text = chapter_outputs["03-worked-examples"]
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
        assert marker in text, f"missing worked example: {marker}"


def test_chapter_03_invokes_the_committed_policy(chapter_outputs):
    text = chapter_outputs["03-worked-examples"]
    assert "policy reused byte-identical" in text, (
        "worked examples do not attest to reusing the committed policy text"
    )
    assert "mock oracle" in text.lower(), "the mocked oracle calls are not shown"


def test_chapter_04_shows_one_type_three_semantics(chapter_outputs):
    text = chapter_outputs["04-one-type-three-semantics"]
    for metric in ("dissent-fraction", "strict-quorum-undecodable", "erasure-aware-undecodable"):
        assert metric in text, f"metric {metric} not exhibited"
    # GAP-04 clarification: the answer type is a nullable Boolean — the
    # checker's reply to "do you agree with the datum?" — not a label set.
    assert "nullable Bool" in text, "the nullable-Boolean answer type is not stated"
    assert "cannot tell" in text, "null's cannot-tell semantics are not stated"
    assert "null" in text.replace("nullable", ""), "no null answers shown in the matrix"
    # The definitions render as a parsed table, not a monospace doc dump;
    # the only source excerpt is the unbound metric slot.
    assert "<table" in text, "metric definitions must render as a table"
    assert "part metric : DisagreementMetric;" in text, (
        "the deliberately unbound metric slot is not shown"
    )
    assert "\n            doc" not in text, "doc walls must not be dumped at source indent"
    assert "gate fires: True" in text, "no metric fires the gate"
    assert "gate fires: False" in text, "no metric leaves the gate quiet"
    assert "same answer matrix" in text, (
        "the demonstration does not state that all three ran on one matrix"
    )


def test_chapter_05_shows_the_shacl_inversion_and_the_outcomes(chapter_outputs):
    text = chapter_outputs["05-the-track"]
    assert "conforms: True" in text, "run-001 conformance not shown"
    assert "conforms: False" in text, "counterexample non-conformance not shown"
    assert "cantTell" in text, "the cantTell outcome is not demonstrated"
    assert "responseCode" in text, (
        "the oracle interface contract (service/payload/code/response) is not demonstrated"
    )


def test_chapter_06_lists_every_adjudicated_gap(chapter_outputs):
    text = chapter_outputs["06-open-questions"]
    for n in range(1, 10):
        assert f"GAP-0{n}" in text, f"GAP-0{n} not surfaced in the open-questions chapter"
