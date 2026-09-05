"""The metric class's properties are declared in the model and proved in code.

The second external review (2026-09-05) showed that the abstract
DisagreementMetric carried its semantics only as a doc comment: three
structurally identical subclasses, distinguished by name and prose, two of
which are not disagreement measures at all (not monotone in dissent; unanimous
disagreement scores 0). The remedy has two halves, and this file checks both:

  * the model DECLARES each concrete metric's properties as attributes
    (denominator, null policy, monotone in dissent, saturates at unanimous
    dissent, ensemble-size invariant), and
  * the implementations are checked EXHAUSTIVELY over the bounded domain
    {True, False, None}^(F x C), F in 1..3, C = 3 (plus the C-varying cases
    the ensemble-size property needs), and the result must equal what the
    model declares.

Within that domain the results are proofs, not samples; a failure reports
its minimal counterexample. The reachability proposition the review
surfaced (with three checkers and no abstention, both quorum metrics are
identically zero, so GATE-02 cannot fire under them) is asserted by
enumeration for every odd ensemble size up to seven.
"""
import itertools
import re
import sys

import pytest

from conftest import MODEL, ROOT

sys.path.insert(0, str(ROOT))
import exhibits  # noqa: E402

VALUES = (True, False, None)
NAMES = tuple(exhibits.METRICS)
PROPERTIES = (
    "denominator",
    "nullPolicy",
    "monotoneInDissent",
    "saturatesAtUnanimousDissent",
    "ensembleSizeInvariant",
)


def matrices(facts, checkers):
    row_space = list(itertools.product(VALUES, repeat=checkers))
    for rows in itertools.product(row_space, repeat=facts):
        yield [list(r) for r in rows]


def small_domain(max_facts=3, checkers=3):
    for f in range(1, max_facts + 1):
        yield from matrices(f, checkers)


def render(m):
    tok = {True: "T", False: "F", None: "_"}
    return " | ".join("".join(tok[v] for v in row) for row in m)


def declared():
    """{metric id: {property: value}} parsed from the concrete definitions'
    attribute redefinitions in the model — the model's own assertions."""
    source = MODEL.read_text()

    def redefinitions(body):
        attrs = {}
        for attr, value in re.findall(r"attribute :>> (\w+) = ([\w:]+);", body):
            value = value.rsplit("::", 1)[-1]
            attrs[attr] = {"true": True, "false": False}.get(value, value)
        return attrs

    # the two branches fix the axioms; each concrete metric inherits its
    # branch's values and redefines the rest
    branches = {
        name: redefinitions(body)
        for name, body in re.findall(
            r"abstract part def (\w+Metric) :> ConsensusInadequacyMetric \{(.*?)\n        \}",
            source, re.S,
        )
    }
    out = {}
    for name, parent, body in re.findall(
        r"(?<!abstract )part def (\w+Metric) :> (\w+Metric) \{(.*?)\n        \}", source, re.S
    ):
        if parent in branches:
            out[exhibits.metric_id(name)] = {**branches[parent], **redefinitions(body)}
    return out


@pytest.fixture(scope="module")
def declared_props():
    return declared()


def test_every_concrete_metric_declares_every_property(declared_props):
    assert set(declared_props) == set(NAMES), (
        f"declared {sorted(declared_props)} vs implemented {sorted(NAMES)}"
    )
    for name, attrs in declared_props.items():
        missing = [p for p in PROPERTIES if p not in attrs]
        assert not missing, f"{name} declares no value for {missing}"


@pytest.mark.parametrize("name", NAMES)
def test_req_m_01_codomain(name):
    metric = exhibits.METRICS[name]
    for m in small_domain():
        v = metric(m)
        assert 0.0 <= v <= 1.0, f"metric({render(m)}) = {v} outside [0, 1]"


@pytest.mark.parametrize("name", NAMES)
def test_req_m_02_empty_run_scores_zero(name):
    # A run with zero facts has nothing to disagree about (ruling, 2026-09-05).
    assert exhibits.METRICS[name]([]) == 0.0


@pytest.mark.parametrize("name", NAMES)
def test_req_m_02_ragged_matrix_is_refused(name):
    # The matrix is rectangular by declaration: an absent checker is not a
    # null answer, and the two denominators would otherwise disagree about
    # what was measured.
    with pytest.raises(ValueError):
        exhibits.METRICS[name]([[True], [True, False, False]])


@pytest.mark.parametrize("name", NAMES)
def test_req_m_03_zero_at_unanimous_agreement_on_three_checkers(name):
    metric = exhibits.METRICS[name]
    for facts in (1, 2, 5):
        m = [[True] * 3 for _ in range(facts)]
        assert metric(m) == 0.0, f"metric({render(m)}) != 0"


def test_strict_quorum_admissibility_limit_is_on_record(declared_props):
    # The absolute quorum of two is deliberate (the paper's two-of-three), so
    # the metric is admissible for a three-checker ensemble only; with one
    # checker, unanimous agreement scores 1.0. The model must say so.
    sq = exhibits.METRICS["strict-quorum-undecodable"]
    assert sq([[True]] * 5) == 1.0
    assert declared_props["strict-quorum-undecodable"]["ensembleSizeInvariant"] is False
    doc = re.search(
        r"part def StrictQuorumUndecodableMetric.*?doc /\*(.*?)\*/", MODEL.read_text(), re.S
    ).group(1)
    assert "three" in doc and "admissible" in doc, (
        "the strict-quorum doc must state the three-checker admissibility limit"
    )


@pytest.mark.parametrize("name", NAMES)
def test_req_m_04_checker_exchangeability(name):
    metric = exhibits.METRICS[name]
    for m in small_domain(max_facts=2):
        base = metric(m)
        for perm in itertools.permutations(range(3)):
            p = [[row[i] for i in perm] for row in m]
            assert metric(p) == base, f"{render(m)} = {base} but {render(p)} = {metric(p)}"


@pytest.mark.parametrize("name", NAMES)
def test_req_m_05_fact_exchangeability(name):
    metric = exhibits.METRICS[name]
    for m in small_domain(max_facts=3):
        base = metric(m)
        for perm in itertools.permutations(range(len(m))):
            p = [m[i] for i in perm]
            assert metric(p) == base, f"{render(m)} = {base} but {render(p)} = {metric(p)}"


def _monotone_in_dissent(metric):
    """None if flipping any True to False never decreases the metric over
    the bounded domain; else the minimal counterexample."""
    for m in small_domain(max_facts=2):
        base = metric(m)
        for i, row in enumerate(m):
            for j, v in enumerate(row):
                if v is not True:
                    continue
                flipped = [list(r) for r in m]
                flipped[i][j] = False
                after = metric(flipped)
                if after < base:
                    return f"{render(m)} = {base:.4g} -> {render(flipped)} = {after:.4g}"
    return None


def _saturates_at_unanimous_dissent(metric):
    for facts in (1, 2, 5):
        m = [[False] * 3 for _ in range(facts)]
        if metric(m) != 1.0:
            return f"metric({render(m)}) = {metric(m)}, not 1.0"
    return None


def _ensemble_size_invariant(metric):
    for m in small_domain(max_facts=2):
        base = metric(m)
        for k in (2, 3):
            rep = [[v for v in row for _ in range(k)] for row in m]
            after = metric(rep)
            if after != base:
                return f"{k}-fold replication: {render(m)} = {base:.4g} -> {after:.4g}"
    return None


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("prop,probe", [
    ("monotoneInDissent", _monotone_in_dissent),
    ("saturatesAtUnanimousDissent", _saturates_at_unanimous_dissent),
    ("ensembleSizeInvariant", _ensemble_size_invariant),
])
def test_declared_property_equals_exhaustive_result(name, prop, probe, declared_props):
    """REQ-M-06 / REQ-M-07 / REQ-M-08: the model asserts, the suite checks."""
    counterexample = probe(exhibits.METRICS[name])
    holds = counterexample is None
    assert declared_props[name][prop] is holds, (
        f"{name}: model declares {prop} = {declared_props[name][prop]} but exhaustive "
        f"check finds {holds}" + (f" (counterexample: {counterexample})" if counterexample else "")
    )


@pytest.mark.parametrize("name", NAMES)
def test_declared_denominator_matches_behavior(name, declared_props):
    """A facts denominator yields only multiples of 1/F; facts x checkers
    yields some value that is not."""
    metric = exhibits.METRICS[name]
    multiples_of_one_over_f = all(
        abs(metric(m) * len(m) - round(metric(m) * len(m))) < 1e-9
        for m in small_domain(max_facts=2)
    )
    expected = "facts" if multiples_of_one_over_f else "factsTimesCheckers"
    assert declared_props[name]["denominator"] == expected, (
        f"{name}: declared denominator {declared_props[name]['denominator']} but the "
        f"values are {'all' if multiples_of_one_over_f else 'not all'} multiples of 1/facts"
    )


NULL_POLICY_PROBES = {
    # a lone null among agreement; a lone voice among nulls
    "punitive": (lambda f: f([[True, True, None]]) > 0.0 and f([[True, None, None]]) > 0.0),
    "quorumBlocking": (lambda f: f([[True, True, None]]) == 0.0 and f([[True, None, None]]) == 1.0),
    "erasure": (lambda f: f([[True, True, None]]) == 0.0 and f([[True, None, None]]) == 0.0),
}


@pytest.mark.parametrize("name", NAMES)
def test_declared_null_policy_matches_behavior(name, declared_props):
    policy = declared_props[name]["nullPolicy"]
    assert policy in NULL_POLICY_PROBES, f"{name}: unknown null policy {policy}"
    assert NULL_POLICY_PROBES[policy](exhibits.METRICS[name]), (
        f"{name}: declared nullPolicy {policy} but the probes disagree"
    )


@pytest.mark.parametrize("checkers", (3, 5, 7))
def test_quorum_metrics_are_identically_zero_without_abstention(checkers):
    """The reachability proposition: over {True, False}^C for odd C, some
    value occurs at least twice (pigeonhole) so quorum-2 is met, and the
    majority strictly exceeds half so the erasure-aware rule decodes.
    GATE-02 cannot fire under either binding unless a checker abstains."""
    sq = exhibits.METRICS["strict-quorum-undecodable"]
    ea = exhibits.METRICS["erasure-aware-undecodable"]
    for row in itertools.product((True, False), repeat=checkers):
        assert sq([list(row)]) == 0.0, f"strict-quorum nonzero on {row}"
        assert ea([list(row)]) == 0.0, f"erasure-aware nonzero on {row}"


def test_dissent_fraction_can_fire_without_abstention():
    df = exhibits.METRICS["dissent-fraction"]
    assert df([[True, True, False]]) > exhibits.model_threshold()


def test_quorum_metrics_become_reachable_with_abstention():
    sq = exhibits.METRICS["strict-quorum-undecodable"]
    ea = exhibits.METRICS["erasure-aware-undecodable"]
    assert sq([[True, False, None]]) == 1.0
    assert ea([[True, False, None]]) == 1.0
