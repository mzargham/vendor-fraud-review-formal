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


def test_track_records_the_configuration_parameters_in_force(track_dataset):
    # WP section 5.3: a Track may include "the model versions and
    # configuration parameters". The parameters the policy ran with are
    # recorded on the execution, values matching the manifest's literals.
    rows = [r.asdict() for r in track_dataset.query("""
        PREFIX vfr: <https://example.org/vfr#>
        SELECT ?confidence ?consensus ?trigger WHERE {
            ?execution a vfr:OpExecution ;
                       vfr:parameters ?p .
            ?p vfr:confidenceThreshold ?confidence ;
               vfr:consensusDisagreementThreshold ?consensus ;
               vfr:vendorRiskTrigger ?trigger .
        }""")]
    assert len(rows) == 1, "run-001 must record exactly one parameter set"
    assert float(rows[0]["confidence"]) == 0.80
    assert float(rows[0]["consensus"]) == 0.25
    assert str(rows[0]["trigger"]) == "high"


def test_track_states_its_aggregate_outcome(track_dataset):
    # GAP-06/07: the Track says whether the Op executed or was a no-op;
    # run-001 executed and retained its final output.
    rows = list(track_dataset.query("""
        PREFIX vfr: <https://example.org/vfr#>
        SELECT ?outcome ?output WHERE {
            ?e a vfr:OpExecution ;
               vfr:aggregateOutcome ?outcome ;
               vfr:finalOutput ?output .
        }"""))
    assert len(rows) == 1
    assert str(rows[0][0]) == "executed"


def test_every_gate_variable_cites_its_oracle(track_dataset):
    # Interface contract (GAP-05 ruling): wherever the policy needs a value,
    # an oracle provides it — and the Track must cite the call: what service,
    # what payload sent, what response code, what response. The system
    # applies its policies to these values; it is not their provider.
    rows = [r.asdict() for r in _query(track_dataset, "interface.rq")]
    variables = {str(r["variable"]) for r in rows}
    assert variables == {
        "confidence", "consensus_disagreement", "sensitive_data_detected", "vendor_risk",
    }, f"gate variables without a complete oracle citation: {variables}"
    for r in rows:
        for field in ("service", "requestPayload", "responseCode", "responsePayload", "value"):
            assert r.get(field) is not None, f"{r['variable']}: missing {field}"
    confidence = next(r for r in rows if str(r["variable"]) == "confidence")
    assert "0.71" in str(confidence["responsePayload"]), (
        "the numeric value must appear in the oracle's cited response"
    )


def test_consensus_oracle_call_records_its_metric(track_dataset):
    # GAP-04: which disagreement metric produced the number is itself an
    # open policy choice, so the Track must at least RECORD which one a run
    # used — recording is not endorsing.
    rows = list(track_dataset.query("""
        PREFIX vfr: <https://example.org/vfr#>
        SELECT ?metric WHERE {
            ?call a vfr:OracleCall ;
                  vfr:service <urn:example:service:consensus-comparator> ;
                  vfr:metric ?metric .
        }"""))
    assert len(rows) == 1, "the consensus comparator call must record its metric"


def test_every_gate_decision_used_an_oracle_backed_reading(track_dataset):
    rows = list(track_dataset.query("""
        PREFIX vfr: <https://example.org/vfr#>
        PREFIX prov: <http://www.w3.org/ns/prov#>
        SELECT ?gateDecision WHERE {
            ?gateDecision a vfr:GateDecision .
            FILTER NOT EXISTS {
                ?gateDecision prov:used ?reading .
                ?reading a vfr:Reading ;
                         prov:wasGeneratedBy ?call .
                ?call vfr:responseCode ?code .
            }
        }"""))
    assert rows == [], f"gate decisions that evaluated values with no citable oracle call: {rows}"


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
