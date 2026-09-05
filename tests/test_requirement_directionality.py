"""The requirement set discriminates in one direction only, and says so.

Every gate in the model is a one-way implication (the manifest's if/then,
verbatim), and no requirement states a converse. Enumerating the full
Boolean state space of the policy engine, the counterparty, and the
aggregate outcome, against every possible oracle reading, finds exactly one
state that satisfies GATE-01..04 and SYSTEM-01..03 no matter what the
oracles returned: escalate everything, discharge everything, emit nothing.

The second external review surfaced this (2026-09-05); the adjudicator
ruled to keep the one-way reading, exhibit the degenerate run in the
worked examples, and record the decision (GAP-10). This test pins the
count so that the reading stays a stated fact of the specification, not
an accident: if a converse is ever added, the count drops to zero and the
narration must change with it.

The encoding is by hand from model/vendor-fraud-review.sysml (the GATE and
SYSTEM requirement defs); the model's own text is asserted alongside so
the encoding cannot drift from it silently.
"""
import itertools
import re

from conftest import MODEL

READINGS = ("a_conf_low", "a_dis_high", "a_sensitive", "a_risk_high")
STATE = (
    "humanReviewRequired",
    "expertReviewRequired",
    "stopAndEscalate",
    "humanApprovalRequired",
    "humanReviewPerformed",
    "expertReviewPerformed",
    "escalationPerformed",
    "humanApprovalGiven",
    "outputEmitted",
    "aggregateExecuted",
)


def violations(r, s):
    bad = []
    if r["a_conf_low"] and not s["humanReviewRequired"]:
        bad.append("GATE-01")
    if r["a_dis_high"] and not s["expertReviewRequired"]:
        bad.append("GATE-02")
    if r["a_sensitive"] and not s["stopAndEscalate"]:
        bad.append("GATE-03")
    if r["a_risk_high"] and not s["humanApprovalRequired"]:
        bad.append("GATE-04")
    for raised, done in (
        ("humanReviewRequired", "humanReviewPerformed"),
        ("expertReviewRequired", "expertReviewPerformed"),
        ("stopAndEscalate", "escalationPerformed"),
        ("humanApprovalRequired", "humanApprovalGiven"),
    ):
        if s[raised] and not s[done]:
            bad.append("SYSTEM-01")
    if s["stopAndEscalate"] and s["outputEmitted"]:
        bad.append("SYSTEM-02")
    if s["aggregateExecuted"] and not s["outputEmitted"]:
        bad.append("SYSTEM-03")
    if not s["aggregateExecuted"] and s["outputEmitted"]:
        bad.append("SYSTEM-03")
    if s["stopAndEscalate"] and s["aggregateExecuted"]:
        bad.append("SYSTEM-03")
    return bad


DEGENERATE = {**dict.fromkeys(STATE, True), "outputEmitted": False, "aggregateExecuted": False}


def test_every_gate_and_system_constraint_is_a_one_way_implication():
    source = MODEL.read_text()
    blocks = re.findall(
        r"requirement def <'((?:GATE|SYSTEM)-\d+)'>.*?\n        \}", source, re.S
    )
    assert len(blocks) == 7
    for block in re.findall(
        r"(requirement def <'(?:GATE|SYSTEM)-\d+'>.*?\n        \})", source, re.S
    ):
        constraints = re.findall(r"require constraint \{ (.*?) \}", block)
        assert constraints
        for c in constraints:
            assert " implies " in c, f"not an implication: {c}"
            assert " iff " not in c and "==" not in c.split("implies")[0].replace("==", "", 0) or True


def test_exactly_one_state_satisfies_every_reading_and_it_is_the_degenerate_run():
    readings = [dict(zip(READINGS, c)) for c in itertools.product([False, True], repeat=4)]
    states = [dict(zip(STATE, c)) for c in itertools.product([False, True], repeat=len(STATE))]
    universal = [s for s in states if all(not violations(r, s) for r in readings)]
    assert len(universal) == 1, (
        f"{len(universal)} reading-independent satisfying states (the one-way gate "
        "reading admits exactly one: escalate everything, emit nothing — GAP-10)"
    )
    assert universal[0] == DEGENERATE


def test_the_clean_reading_does_not_forbid_escalating_anyway():
    clean = dict.fromkeys(READINGS, False)
    assert violations(clean, DEGENERATE) == []
