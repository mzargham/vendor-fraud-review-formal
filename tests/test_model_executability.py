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


def test_counterexample_catches_four_failure_kinds():
    # Three distinct ways a run can be wrong: the gate fired but no
    # obligation was raised (component level); an obligation was raised but
    # never discharged (system level, GAP-02); and the Op stopped but
    # emitted output anyway (aggregate level, GAP-06 — section 5.2: "the Op
    # stops before external transmission"); and a disagreement reading
    # outside the metric class's declared codomain [0, 1] (component
    # level, TYPE-01 — second external review, 2026-09-05).
    r = run_sysml(str(CX_MODEL), "-satisfy=RunConfigurations")
    assert r.stdout.count("fails") >= 4, (
        f"expected gate, discharge, stopped-but-emitted, and out-of-range violations:\n{r.stdout}"
    )
    for marker in ("unattendedGate01", "undischargedSystem01", "emittedSystem02",
                   "outOfRangeType01"):
        assert f"{marker} fails" in r.stdout, (
            f"missing the {marker} violation:\n{r.stdout}"
        )


def test_model_declares_three_check_levels():
    # Component (GATE-, INTERFACE-), wiring (WIRE-), and system (SYSTEM-)
    # checks all present in the model and all surviving conversion.
    source = MODEL.read_text()
    for rid in ("GATE-01", "GATE-02", "GATE-03", "GATE-04", "INTERFACE-01", "TYPE-01",
                "WIRE-01", "WIRE-02", "WIRE-03", "WIRE-04",
                "SYSTEM-01", "SYSTEM-02", "SYSTEM-03"):
        assert f"<'{rid}'>" in source, f"{rid} missing from the model"
    r = run_sysml(str(MODEL), "-convert", "ttl")
    for rid in ("WIRE-01", "SYSTEM-01", "SYSTEM-02"):
        assert rid in r.stdout, f"{rid} did not survive -convert ttl"


def test_lifecycle_traces_reach_their_terminal_states():
    # The aggregate is not just an attribute: the assembly's lifecycle runs.
    # Trace output is the only honest post-run evidence.
    stopped = run_sysml(str(MODEL), "-trace", "-instantiate",
                        "VendorFraudReview::ExerciseContexts::stoppedContext")
    assert "running -> stopped" in stopped.stdout, (
        f"stopped context never reached the stopped state:\n{stopped.stdout[-2000:]}"
    )
    assert "running -> completed" not in stopped.stdout
    completed = run_sysml(str(MODEL), "-trace", "-instantiate",
                          "VendorFraudReview::ExerciseContexts::completedContext")
    assert "running -> completed" in completed.stdout, (
        f"completed context never reached the completed state:\n{completed.stdout[-2000:]}"
    )
    assert "running -> stopped" not in completed.stdout
    again = run_sysml(str(MODEL), "-trace", "-instantiate",
                      "VendorFraudReview::ExerciseContexts::stoppedContext")
    assert again.stdout == stopped.stdout, "trace is not byte-stable"


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


def test_the_boundary_is_stated_where_the_outcome_is_defined():
    # GAP-07, refined 2026-09-05 (the adjudicator's ruling): noOp means no
    # action output over the Op's boundary; the trace evidence is internal
    # to the system of interest and is kept. The model must say so where
    # the outcome and the emitted output are defined, so a reader of the
    # model alone gets the distinction.
    source = MODEL.read_text()
    outcome = re.search(r"enum def AggregateOutcome \{.*?doc /\*(.*?)\*/", source, re.S).group(1)
    assert "boundary" in outcome and "internal" in outcome, (
        "AggregateOutcome's doc must state that noOp is about the boundary and the record is internal"
    )
    cog = re.search(r"part def AnomalySummaryCog.*?doc /\*(.*?)\*/", source, re.S).group(1)
    assert "boundary" in cog, "outputEmitted must be defined as crossing the Op's boundary"
