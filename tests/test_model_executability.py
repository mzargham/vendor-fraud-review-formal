"""The manifest's gate logic computes, says yes and no honestly, and survives projection."""
import rdflib

from conftest import CX_MODEL, MODEL, run_sysml


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
