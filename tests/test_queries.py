"""His section 5.3 Track purposes are answerable by computation."""
import rdflib

from conftest import EARL, QUERIES


def _query(dataset, name):
    return list(dataset.query((QUERIES / name).read_text()))


def test_auditability_chain_reconstructs_the_decision(track_dataset):
    rows = _query(track_dataset, "auditability.rq")
    assert rows, "auditability query returned nothing: cannot reconstruct the decision"
    row = rows[0].asdict()
    assert any("approver" in k.lower() for k in row), "no approver in the chain"
    assert any("rationale" in k.lower() for k in row), "no rationale in the chain"
    assert all(v is not None for v in row.values()), f"incomplete chain: {row}"


def test_governance_no_unapproved_gate_firings_on_run_001(track_dataset):
    rows = _query(track_dataset, "governance.rq")
    assert rows == [], (
        f"run-001 has Gate firings without a matching human approval: {rows}"
    )


def test_governance_catches_the_counterexample(cx_track_dataset):
    rows = _query(cx_track_dataset, "governance.rq")
    assert rows, "governance query missed the counterexample's undischarged obligations"


def test_obligations_are_discharged_by_state_mutating_actions(track_dataset):
    # Adjudication GAP-02: the action that discharges an obligation must also
    # mutate state. Every obligation in run-001 must have a discharging action
    # that generated a new state entity.
    rows = list(track_dataset.query("""
        PREFIX vfr: <https://example.org/vfr#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        SELECT ?obligation WHERE {
            ?obligation a vfr:Obligation .
            FILTER NOT EXISTS {
                ?action vfr:discharges ?obligation ;
                        prov:generated ?newState .
            }
        }"""))
    assert rows == [], f"obligations without a state-mutating discharge: {rows}"
    count = list(track_dataset.query(
        "PREFIX vfr: <https://example.org/vfr#> "
        "SELECT (COUNT(?o) AS ?n) WHERE { ?o a vfr:Obligation }"))
    assert int(count[0][0]) == 2, "run-001 should raise exactly two obligations"


def test_trust_outcome_distribution_is_fully_visible(track_dataset):
    rows = [r.asdict() for r in _query(track_dataset, "trust.rq")]
    assert rows, "trust query returned nothing"
    outcomes = {str(r["outcome"]) for r in rows}
    modes = {str(r["mode"]) for r in rows}
    assert EARL + "cantTell" in outcomes, "the cantTell outcome is not visible"
    assert EARL + "failed" in outcomes, "the failed outcome is not visible"
    assert {EARL + "automatic", EARL + "manual"} <= modes, (
        "the automatic/manual split is not visible in the distribution"
    )
    cant_tell = [r for r in rows if str(r["outcome"]) == EARL + "cantTell"]
    assert len(cant_tell) == 1, "exactly one cantTell expected in run-001"
