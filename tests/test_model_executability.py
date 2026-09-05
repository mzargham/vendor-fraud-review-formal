"""The manifest's gate logic computes, says yes and no honestly, and survives conversion."""
import re

import rdflib

from conftest import CX_MODEL, MODEL, run_sysml


def _strip_doc_comments(source: str) -> str:
    return re.sub(r"/\*.*?\*/", "", source, flags=re.S)


def test_thresholds_are_factored_as_parameters():
    # Numerical parameters in policies are factored out as single-point
    # definitions the gates reference — what an implementation can do that a
    # whitepaper cannot. Outside verbatim doc quotes, each manifest literal
    # appears exactly once (its parameter default), and the parameters are
    # named.
    stripped = _strip_doc_comments(MODEL.read_text())
    assert stripped.count("0.80") == 1, "0.80 must appear exactly once: as a parameter default"
    assert stripped.count("0.25") == 1, "0.25 must appear exactly once: as a parameter default"
    for name in ("confidenceThreshold", "consensusDisagreementThreshold", "vendorRiskTrigger"):
        assert name in stripped, f"named parameter {name} missing from the model"
    cx_stripped = _strip_doc_comments(CX_MODEL.read_text())
    assert cx_stripped.count("0.80") == 1, "counterexample must use the same factoring"


def test_parameters_survive_conversion():
    r = run_sysml(str(MODEL), "-convert", "ttl")
    assert r.returncode == 0
    for name in ("confidenceThreshold", "consensusDisagreementThreshold"):
        assert name in r.stdout, f"parameter {name} did not survive -convert ttl"


def test_model_validates_strict():
    r = run_sysml(str(MODEL), "-validate", "-strict")
    assert r.returncode == 0, f"-validate -strict failed:\n{r.stdout}\n{r.stderr}"


def test_run_configurations_satisfy():
    r = run_sysml(str(MODEL), "-satisfy=RunConfigurations")
    assert r.returncode == 0, f"-satisfy=RunConfigurations != 0:\n{r.stdout}\n{r.stderr}"
    assert "fails" not in r.stdout.lower() or "0 fail" in r.stdout.lower(), (
        f"a bound requirement reports failing:\n{r.stdout}"
    )


def test_counterexample_run_fails_satisfy():
    r = run_sysml(str(CX_MODEL), "-satisfy=RunConfigurations")
    assert r.returncode == 1, (
        "the unattended run (Gate fired, no human step) must FAIL satisfy "
        f"with exit 1, got {r.returncode}:\n{r.stdout}\n{r.stderr}"
    )


def test_counterexample_catches_both_failure_kinds():
    # Adjudication GAP-02: an obligation is distinct from its discharge. The
    # counterexample must show BOTH ways a run can be wrong: the gate fired
    # but no obligation was raised, and an obligation was raised but never
    # discharged by a concrete action.
    r = run_sysml(str(CX_MODEL), "-satisfy=RunConfigurations")
    assert r.stdout.count("fails") >= 2, (
        f"expected a gate violation and a discharge violation:\n{r.stdout}"
    )


def test_conversion_is_deterministic_and_keeps_the_gates():
    first = run_sysml(str(MODEL), "-convert", "ttl")
    second = run_sysml(str(MODEL), "-convert", "ttl")
    assert first.returncode == 0, f"-convert ttl failed:\n{first.stderr}"
    assert first.stdout == second.stdout, "-convert ttl is not byte-stable"

    g = rdflib.Graph()
    g.parse(data=first.stdout, format="turtle")
    assert len(g) > 0, "converted graph is empty"

    serialized = first.stdout
    for gate in ("GATE-01", "GATE-02", "GATE-03", "GATE-04"):
        assert gate in serialized, (
            f"{gate} did not survive -convert ttl (silent converter drop?)"
        )
