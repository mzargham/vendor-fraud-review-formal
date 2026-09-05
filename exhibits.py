"""Executable exhibits for the walkthrough chapters.

Every function here is called from a chapter notebook and prints what it
finds; the chapters stay thin (an import and a call) and the machinery
stays committed, tested code. All paths are anchored to this file, so the
chapters execute identically from the repo root or from chapters/.
"""
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import tempfile
from typing import Callable, Sequence

ROOT = pathlib.Path(__file__).resolve().parent
SYSML = ROOT / "toolchain" / "bin" / "sysml"
MODEL = ROOT / "model" / "vendor-fraud-review.sysml"
VFR = "https://example.org/vfr#"


def _run(*args, **kwargs):
    return subprocess.run([*args], capture_output=True, text=True, cwd=ROOT, **kwargs)


def _sysml(*args):
    return _run(str(SYSML), *args)


def _norm(text):
    return re.sub(r"\s+", "", re.sub(r"\([^)]*\)", "", text)).lower()


def _graph():
    import rdflib

    g = rdflib.Graph()
    g.parse(ROOT / "sources" / "sources.ttl")
    g.parse(ROOT / "vocabulary" / "op-concepts.ttl")
    return g


def _pdf():
    return next((ROOT / "sources").glob("*.pdf"))


def _dedent(block):
    """Dedent a model excerpt whose first line starts mid-source (its match
    begins at the keyword, so only the continuation lines carry indent)."""
    lines = block.splitlines()
    indents = [
        len(l) - len(l.lstrip()) for l in lines[1:] if l.strip()
    ] or [0]
    cut = min(indents)
    return "\n".join(
        [lines[0].strip()] + [l[cut:] if l.strip() else "" for l in lines[1:]]
    )


def _table(headers, rows):
    """Render an HTML table; a ("code", text) cell renders monospace."""
    import html as html_mod
    from IPython.display import HTML, display

    def cell(c):
        if isinstance(c, tuple) and c[0] == "code":
            return f'<td style="text-align:left"><code>{html_mod.escape(c[1])}</code></td>'
        return f'<td style="text-align:left">{html_mod.escape(str(c))}</td>'

    head = "".join(f"<th>{html_mod.escape(h)}</th>" for h in headers)
    body = "\n".join("<tr>" + "".join(cell(c) for c in row) + "</tr>" for row in rows)
    display(HTML(
        f"<table>\n<thead><tr>{head}</tr></thead>\n<tbody>\n{body}\n</tbody>\n</table>"
    ))


# ---------------------------------------------------------------- chapter 01

def show_toolchain():
    r = _run("bash", str(ROOT / "toolchain" / "get-sysml.sh"))
    print(f"pinned toolchain present, checksum-verified: {r.returncode == 0}")
    print(_run(str(SYSML), "--version").stdout.strip())


def check_pinned_source():
    import rdflib

    pdf = _pdf()
    actual = hashlib.sha256(pdf.read_bytes()).hexdigest()
    declared = str(next(_graph().objects(None, rdflib.URIRef(VFR + "contentHash"))))
    print(f"snapshot file : {pdf.name}")
    print(f"sha256(file)  : {actual}")
    print(f"declared hash : {declared}")
    print(f"match         : {actual == declared}")


def vocabulary_table():
    import html as html_mod

    import rdflib
    from IPython.display import HTML, display
    from rdflib.namespace import SKOS

    g = _graph()
    pdf_text = _norm(_run("pdftotext", "-layout", str(_pdf()), "-").stdout)
    rows = []
    for c in g.subjects(SKOS.definition, None):
        label = str(next(g.objects(c, SKOS.prefLabel)))
        definition = str(next(g.objects(c, SKOS.definition)))
        locator = str(next(g.objects(c, rdflib.URIRef(VFR + "locator"))))
        rows.append((locator, label, definition, _norm(definition) in pdf_text))
    body = "\n".join(
        "<tr>"
        f"<td>{locator}</td>"
        f"<td><strong>{html_mod.escape(label)}</strong></td>"
        f'<td style="text-align:left">{html_mod.escape(definition)}</td>'
        f"<td>{'✓ verbatim' if verbatim else '✗ NOT IN SOURCE'}</td>"
        "</tr>"
        for locator, label, definition, verbatim in sorted(rows)
    )
    display(HTML(
        "<table>\n<thead><tr>"
        "<th>§</th><th>Concept</th>"
        "<th>Definition, verbatim from the pinned snapshot</th>"
        "<th>Checked</th>"
        "</tr></thead>\n<tbody>\n" + body + "\n</tbody>\n</table>"
    ))


# ---------------------------------------------------------------- chapter 02

def _gates():
    """(gate id, manifest if-line, manifest then-token, constraint) per gate,
    parsed from the model text — the doc quotes and the evaluated rule come
    from the same block."""
    out = []
    for gid, body in re.findall(
        r"requirement def <'(GATE-\d+)'> \w+ \{(.*?)\n        \}", MODEL.read_text(), re.S
    ):
        rule = re.search(r"- if: ([^\n]*)", body).group(1).strip()
        then = re.search(r"then: (\w+)", body).group(1)
        constraint = re.search(r"require constraint \{ (.*?) \}", body).group(1)
        out.append((gid, rule, then, constraint))
    return out


def _parameters_block():
    return re.search(
        r"part def ValidationStrategyParameters \{.*?\n        \}", MODEL.read_text(), re.S
    ).group(0)


def show_policy_parameters():
    gates = _gates()
    rows = []
    for name, typ, value in re.findall(
        r"attribute (\w+) : ([\w:]+) = ([\w.:]+);", _parameters_block()
    ):
        backing = next(
            (f"{gid}: - if: {rule}" for gid, rule, _t, c in gates if name in c), ""
        )
        rows.append((("code", name), ("code", value), typ.split("::")[-1], ("code", backing)))
    _table(("Parameter", "Value", "Type", "Manifest rule it backs"), rows)


def show_policy_parameters_source():
    print(_dedent(_parameters_block()))


def show_gate_checks():
    rows = [
        (gid, ("code", f"- if: {rule}"), ("code", f"then: {then}"), ("code", constraint))
        for gid, rule, then, constraint in _gates()
    ]
    _table(("Gate", "Manifest condition, verbatim", "Manifest consequence", "As evaluated"), rows)


def show_gate_source():
    example = re.search(
        r"requirement def <'GATE-01'>.*?\n        \}", MODEL.read_text(), re.S
    ).group(0)
    print(_dedent(example))


def show_seams():
    rows = [
        (("code", name), typ, ("code", src), ("code", dst))
        for name, typ, src, dst in re.findall(
            r"interface (\w+) : (\w+Seam) connect (\S+) to (\S+);", MODEL.read_text()
        )
    ]
    _table(("Seam", "Interface type", "From (supplier port)", "To (consumer port)"), rows)


def validate_and_satisfy():
    r = _sysml(str(MODEL), "-validate", "-strict")
    print(f"validate -strict exit code: {r.returncode}")
    r = _sysml(str(MODEL), "-satisfy=RunConfigurations")
    print(r.stdout.strip())
    print(f"satisfy exit code: {r.returncode}")


def refuse_counterexample():
    r = _sysml(str(ROOT / "counterexamples" / "run-unattended.sysml"), "-satisfy=RunConfigurations")
    print(r.stdout.strip())
    print(f"satisfy exit code: {r.returncode}")


def check_wiring():
    sys.path.insert(0, str(ROOT / "tests"))
    from test_wiring import _converted, check_seam_conformance

    seams = re.findall(r"interface (\w+) : \w+Seam connect", MODEL.read_text())
    graph, _ = _converted(MODEL)
    mismatches = check_seam_conformance(graph)
    print(f"committed assembly ({len(seams)} seams): "
          + ("wiring rules: OK" if not mismatches else f"wiring rules: REFUSED {mismatches}"))
    miswired = ROOT / "counterexamples" / "miswired.sysml"
    r = _sysml(str(miswired), "-validate", "-strict")
    print(f"miswired counterexample, validate -strict exit code: {r.returncode} (accepted)")
    graph_bad, _ = _converted(miswired)
    bad = check_seam_conformance(graph_bad)
    print("miswired counterexample: "
          + ("wiring rules: OK (?!)" if not bad else "wiring rules: REFUSED"))
    for m in bad:
        print("  " + m)


def show_lifecycle():
    contexts = re.findall(r"part (\w+Context)\b", MODEL.read_text())
    for name in contexts:
        ctx = f"VendorFraudReview::ExerciseContexts::{name}"
        r = _sysml(str(MODEL), "-trace", "-instantiate", ctx)
        print(ctx.split("::")[-1])
        lines = [l for l in r.stdout.splitlines() if "transition:" in l or "enter:" in l]
        for line in lines[:8]:
            print("  " + line)
        print()


def show_element_trace():
    import rdflib

    g = rdflib.Graph()
    g.parse(ROOT / "model" / "trace.ttl", format="turtle")
    V = rdflib.Namespace(VFR)
    rows = []
    counts = {"grounded": 0, "judgment": 0, "scaffold": 0}
    elements = sorted(
        g.subjects(rdflib.RDF.type, V.ModelElement),
        key=lambda e: (str(g.value(e, V.kind)), str(g.value(e, V.elementName))),
    )
    for e in elements:
        parts = []
        grounded = g.value(e, V.groundedIn)
        if grounded is not None:
            parts.append(f"grounded in {grounded}")
            counts["grounded"] += 1
        derived = sorted(_local(r) for r in g.objects(e, V.derivedFromRuling))
        derived += sorted(_local(n) for n in g.objects(e, V.derivedFromNote))
        if derived:
            parts.append("derived from " + ", ".join(derived))
            if grounded is None:
                counts["judgment"] += 1
        scaffold = g.value(e, V.scaffoldRationale)
        if scaffold is not None:
            parts.append(f"scaffold: {scaffold}")
            counts["scaffold"] += 1
        rows.append((
            ("code", str(g.value(e, V.elementName))),
            str(g.value(e, V.kind)),
            "; ".join(parts),
        ))
    _table(("Element", "Kind", "Provenance"), rows)
    print(f"traced elements: {len(rows)} — {counts['grounded']} grounded in the "
          f"pinned source, {counts['judgment']} from recorded judgments alone, "
          f"{counts['scaffold']} declared scaffolding")


def check_conversion():
    import rdflib

    c1 = _sysml(str(MODEL), "-convert", "ttl")
    c2 = _sysml(str(MODEL), "-convert", "ttl")
    mg = rdflib.Graph()
    mg.parse(data=c1.stdout, format="turtle")
    print(f"converted triples : {len(mg)}")
    print(f"byte-stable       : {c1.stdout == c2.stdout}")
    checks = re.findall(r"requirement def <'([A-Z]+-\d+)'>", MODEL.read_text())
    present = [rid for rid in checks if rid in c1.stdout]
    print(f"checks present    : {len(present)} of {len(checks)} "
          f"({', '.join(present)})")


# ---------------------------------------------------------------- chapter 03

_SERVICE_LABELS: dict = {}


def _services():
    """Variable -> oracle service label, read from the run record's
    interface graph rather than retyped here."""
    if not _SERVICE_LABELS:
        ds = _dataset("track/run-001.trig")
        for row in ds.query("""
            PREFIX vfr: <https://example.org/vfr#>
            PREFIX prov: <http://www.w3.org/ns/prov#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?variable ?label WHERE {
                ?reading a vfr:Reading ; vfr:variable ?variable ;
                         prov:wasGeneratedBy ?call .
                ?call vfr:service ?service .
                ?service rdfs:label ?label .
            }"""):
            _SERVICE_LABELS[str(row[0])] = str(row[1]).split(" (")[0]
    return _SERVICE_LABELS


def _policy_text():
    return MODEL.read_text().split("    package RunConfigurations {")[0]


def show_policy_reuse():
    digest = hashlib.sha256(_policy_text().encode()).hexdigest()[:12]
    print("policy reused byte-identical from model/vendor-fraud-review.sysml "
          f"(sha256 {digest})")


def mock_oracle(variable, value):
    payload = json.dumps({"op": "vendor-fraud-review", "variable": variable})
    print(f"  mock oracle {_services()[variable]}: sent {payload} "
          f"-> 200 {json.dumps({variable: value})}")
    return value


def _b(v):
    return "true" if v else "false"


SCENARIO_TEMPLATE = """    package RunConfigurations {
        part def Scenario :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = @CONF@; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = @CONS@; }
            part :>> scannerOracle { attribute :>> returnedDetected = @SENS@; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::@RISK@; }
            part :>> policyEngine {
                attribute :>> confidence = @CONF@;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::@LEVEL@;
                attribute :>> consensusDisagreement = @CONS@;
                attribute :>> sensitiveDataDetected = @SENS@;
                attribute :>> vendorRisk = Manifest::RiskLevel::@RISK@;
                attribute :>> humanReviewRequired = @HRR@;
                attribute :>> expertReviewRequired = @ERR@;
                attribute :>> stopAndEscalate = @SAE@;
                attribute :>> humanApprovalRequired = @HAR@;
            }
            part :>> counterparty {
                attribute :>> humanReviewPerformed = @HRP@;
                attribute :>> expertReviewPerformed = @ERP@;
                attribute :>> escalationPerformed = @ESP@;
                attribute :>> humanApprovalGiven = @HAG@;
            }
            part :>> summaryCog { attribute :>> outputEmitted = @OUT@; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::@AGG@;
        }
        part s : Scenario;
        requirement i1 : Manifest::ConfidenceInterface { subject pe = s.policyEngine; }
        requirement t1 : Manifest::DisagreementReadingInRange { subject pe = s.policyEngine; }
        requirement g1 : Manifest::ConfidenceGate { subject pe = s.policyEngine; }
        requirement g2 : Manifest::ConsensusGate { subject pe = s.policyEngine; }
        requirement g3 : Manifest::SensitiveDataGate { subject pe = s.policyEngine; }
        requirement g4 : Manifest::VendorRiskGate { subject pe = s.policyEngine; }
        requirement w1 : Manifest::ConfidenceSeamIntegrity { subject op = s; }
        requirement w2 : Manifest::ConsensusSeamIntegrity { subject op = s; }
        requirement w3 : Manifest::ScannerSeamIntegrity { subject op = s; }
        requirement w4 : Manifest::RiskSeamIntegrity { subject op = s; }
        requirement s1 : Manifest::ObligationsDischarged { subject op = s; }
        requirement s2 : Manifest::StopMeansNoOutput { subject op = s; }
        requirement s3 : Manifest::OutcomeCoherence { subject op = s; }
        verification def ScenarioCase {
            objective {
                verify i1; verify t1; verify g1; verify g2; verify g3; verify g4;
                verify w1; verify w2; verify w3; verify w4;
                verify s1; verify s2; verify s3;
            }
        }
        verification scenarioCase : ScenarioCase;
    }
}
"""


def run_scenario(name, readings, recorded, policy_text=None):
    print(f"scenario '{name}'")
    conf = mock_oracle("confidence", readings["confidence"])
    cons = mock_oracle("consensus_disagreement", readings["consensus_disagreement"])
    sens = mock_oracle("sensitive_data_detected", readings["sensitive_data_detected"])
    risk = mock_oracle("vendor_risk", readings["vendor_risk"])
    agg = recorded.get("aggregate", "executed")
    fills = {
        "@CONF@": repr(conf), "@CONS@": repr(cons), "@SENS@": _b(sens), "@RISK@": risk,
        "@LEVEL@": recorded["confidenceLevel"],
        "@HRR@": _b(recorded.get("humanReviewRequired", False)),
        "@ERR@": _b(recorded.get("expertReviewRequired", False)),
        "@SAE@": _b(recorded.get("stopAndEscalate", False)),
        "@HAR@": _b(recorded.get("humanApprovalRequired", False)),
        "@HRP@": _b(recorded.get("humanReviewPerformed", False)),
        "@ERP@": _b(recorded.get("expertReviewPerformed", False)),
        "@ESP@": _b(recorded.get("escalationPerformed", False)),
        "@HAG@": _b(recorded.get("humanApprovalGiven", False)),
        "@OUT@": _b(recorded.get("outputEmitted", False)),
        "@AGG@": agg,
    }
    scenario = SCENARIO_TEMPLATE
    for k, v in fills.items():
        scenario = scenario.replace(k, v)
    with tempfile.NamedTemporaryFile("w", suffix=".sysml", delete=False) as f:
        f.write((policy_text if policy_text is not None else _policy_text()) + scenario)
        path = f.name
    r = _sysml(path, "-satisfy=RunConfigurations")
    for line in r.stdout.splitlines():
        if "satisfy" in line or "Required condition" in line:
            print("  " + line.strip())
    if r.returncode == 0:
        print(f"scenario '{name}': POLICY SATISFIED — aggregate: {agg} (satisfy exit 0)")
    else:
        print(f"scenario '{name}': POLICY VIOLATED (satisfy exit {r.returncode})")


# ---------------------------------------------------------------- chapter 04

# GAP-04 clarification (2026-09-04): an answer is a nullable Boolean — one
# checker's reply, given the datum as context, to "do you agree with the
# datum?". True = agree, False = disagree, None = cannot tell. Checkers are
# factored apart from generators: a producing Cog may answer False about
# its own datum.
# The matrix is rectangular by declaration (an absent checker is not a null
# answer) and a run with zero facts scores 0: no facts, no inadequacy
# (GAP-04 matrix ruling, 2026-09-05).
ConsensusInadequacyMetric = Callable[[Sequence[Sequence[bool | None]]], float]


def _rectangular(matrix):
    """True if there is anything to measure; raises on a ragged matrix."""
    if not matrix:
        return False
    if any(len(fact) != len(matrix[0]) for fact in matrix):
        raise ValueError("answer matrix must be rectangular: one answer per checker per fact")
    return True


def dissent_fraction(matrix):
    if not _rectangular(matrix):
        return 0.0
    dissents = total = 0
    for fact in matrix:
        dissents += sum(1 for v in fact if v is not True)
        total += len(fact)
    return dissents / total


def strict_quorum_undecodable(matrix):
    if not _rectangular(matrix):
        return 0.0
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v is not None]
        if not expressed or max(expressed.count(v) for v in set(expressed)) < 2:
            undecodable += 1
    return undecodable / len(matrix)


def erasure_aware_undecodable(matrix):
    if not _rectangular(matrix):
        return 0.0
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v is not None]
        if not expressed or max(expressed.count(v) for v in set(expressed)) * 2 <= len(expressed):
            undecodable += 1
    return undecodable / len(matrix)


METRICS: dict[str, ConsensusInadequacyMetric] = {
    "dissent-fraction": dissent_fraction,
    "strict-quorum-undecodable": strict_quorum_undecodable,
    "erasure-aware-undecodable": erasure_aware_undecodable,
}

# The headline matrix: fabricated, constructed so that no metric lands on
# the threshold and the three read clearly apart (second external review,
# 2026-09-05: the previous headline landed exactly on 0.25 under one
# binding, so the result turned on comparator strictness alone).
ANSWER_MATRIX = [
    [True, True, True],
    [True, True, True],
    [True, True, True],
    [True, True, False],
    [True, False, None],
    [True, None, None],
    [False, None, None],
    [True, False, False],
]

# The boundary case, kept as its own exhibit: erasure-aware-undecodable
# scores exactly 0.250 here, and the manifest's comparator is strict.
BOUNDARY_MATRIX = [
    [True, True, True],
    [True, True, True],
    [True, True, True],
    [True, True, False],
    [True, True, None],
    [True, False, None],
    [False, None, True],
    [True, None, None],
]


def model_threshold():
    """The consensus threshold, read from the model's single point of
    definition (never retyped here)."""
    return float(re.search(
        r"consensusDisagreementThreshold : ScalarValues::Real = ([0-9.]+)",
        MODEL.read_text()).group(1))


def evaluate_metrics():
    print("type signature: ConsensusInadequacyMetric = "
          "(fact x checker answer matrix of nullable Bool; "
          "True = agree, False = disagree, null = cannot tell) -> [0, 1]\n")
    threshold = model_threshold()
    token = {True: "True ", False: "False", None: "null "}
    checkers = len(ANSWER_MATRIX[0])
    print("same answer matrix for all three metrics "
          f"({len(ANSWER_MATRIX)} facts x {checkers} checkers; "
          "fabricated example data, constructed to separate the metrics):")
    for i, fact in enumerate(ANSWER_MATRIX, 1):
        print(f"  f{i}: " + " ".join(token[v] for v in fact))
    print(f"threshold (from the model, single point of definition): > {threshold}\n")
    for name, metric in METRICS.items():
        value = metric(ANSWER_MATRIX)
        print(f"{name:26}: {value:.3f} -> gate fires: {value > threshold}")
    print("\nthe boundary case (a second matrix, kept apart from the headline): "
          "one binding lands exactly on the threshold, and the comparator is the "
          "manifest's own strict >, verbatim from the section 5.6 rule —")
    for i, fact in enumerate(BOUNDARY_MATRIX, 1):
        print(f"  f{i}: " + " ".join(token[v] for v in fact))
    for name, metric in METRICS.items():
        value = metric(BOUNDARY_MATRIX)
        at = "  (exactly on the boundary)" if value == threshold else ""
        print(f"{name:26}: {value:.3f} -> gate fires: {value > threshold}{at}")
    print("\nthe paper's own section 5.5 example, as one fact "
          "(three Cogs classify a document, two agree):")
    example = [[True, True, False]]
    for name, metric in METRICS.items():
        value = metric(example)
        print(f"{name:26}: {value:.3f} -> gate fires: {value > threshold}")


def show_metric_definitions():
    rows = []
    for signature, doc in re.findall(
        r"((?:abstract )?part def \w+Metric[^\n{]*)\{\s*doc /\* (.*?) \*/",
        MODEL.read_text(), re.S,
    ):
        rows.append((("code", signature.strip()), re.sub(r"\s+", " ", doc).strip()))
    _table(("Definition", "Doc, verbatim from the model"), rows)


def metric_id(def_name):
    """The binding convention: a model definition's metric id is derived
    mechanically from its name (DissentFractionMetric -> dissent-fraction).
    The same id keys the implementation mapping below and is the value a
    Track records in vfr:metric."""
    return re.sub(r"(?<!^)(?=[A-Z])", "-", def_name[: -len("Metric")]).lower()


def show_metric_binding():
    defs = re.findall(
        r"part def (\w+Metric) :> (?:Disagreement|Undecodability)Metric", MODEL.read_text()
    )
    ok = True
    rows = []
    for d in defs:
        mid = metric_id(d)
        impl = METRICS.get(mid)
        rows.append((
            ("code", d),
            ("code", mid),
            ("code", f"exhibits.{impl.__name__}" if impl else "NO IMPLEMENTATION"),
            "✓" if impl else "✗",
        ))
        ok = ok and impl is not None
    _table(("Model definition", "Metric id (Track vocabulary)", "Implementation", "Bound"), rows)
    for mid in sorted(set(METRICS) - {metric_id(d) for d in defs}):
        ok = False
        print(f"implementation with no model definition: {mid}")
    print(f"model <-> implementation binding: {'OK' if ok else 'BROKEN'} "
          f"({len(defs)} definitions, {len(METRICS)} implementations)")
    ds = _dataset("track/run-001.trig")
    for row in ds.query(f"SELECT ?m WHERE {{ ?call <{VFR}metric> ?m }}"):
        m = str(row[0])
        print(f"run-001 recorded metric: {m} -> bound implementation: "
              f"{'exhibits.' + METRICS[m].__name__ if m in METRICS else 'NONE'}")


def show_unbound_metric_slot():
    block = re.search(
        r"part def ConsensusComparatorOracle.*?\n        \}", MODEL.read_text(), re.S
    ).group(0)
    print(_dedent(block))


def declared_metric_properties():
    """{metric id: {property: value}} read from the model: the two branches
    fix the axioms, each concrete metric redefines the rest."""
    source = MODEL.read_text()

    def redefinitions(body):
        out = {}
        for attr, value in re.findall(r"attribute :>> (\w+) = ([\w:]+);", body):
            value = value.rsplit("::", 1)[-1]
            out[attr] = {"true": True, "false": False}.get(value, value)
        return out

    branches = {
        name: redefinitions(body)
        for name, body in re.findall(
            r"abstract part def (\w+Metric) :> ConsensusInadequacyMetric \{(.*?)\n        \}",
            source, re.S,
        )
    }
    declared = {}
    for name, parent, body in re.findall(
        r"(?<!abstract )part def (\w+Metric) :> (\w+Metric) \{(.*?)\n        \}", source, re.S
    ):
        if parent in branches:
            declared[metric_id(name)] = {**branches[parent], **redefinitions(body)}
    return declared


def _render_matrix(m):
    tok = {True: "T", False: "F", None: "_"}
    return " | ".join("[" + " ".join(tok[v] for v in row) + "]" for row in m)


def _small_domain(max_facts=2, checkers=3):
    import itertools

    rows = list(itertools.product((True, False, None), repeat=checkers))
    for f in range(1, max_facts + 1):
        for chosen in itertools.product(rows, repeat=f):
            yield [list(r) for r in chosen]


def _probe_monotone(metric):
    for m in _small_domain():
        base = metric(m)
        for i, row in enumerate(m):
            for j, v in enumerate(row):
                if v is not True:
                    continue
                flipped = [list(r) for r in m]
                flipped[i][j] = False
                if metric(flipped) < base:
                    return False, (f"{_render_matrix(m)} = {base:.3g} but "
                                   f"{_render_matrix(flipped)} = {metric(flipped):.3g}")
    return True, "no decrease over the bounded domain"


def _probe_saturates(metric):
    v = metric([[False] * 3 for _ in range(2)])
    return v == 1.0, f"all-False matrix scores {v:.3g}"


def _probe_ensemble(metric):
    for m in _small_domain():
        base = metric(m)
        for k in (2, 3):
            rep = [[v for v in row for _ in range(k)] for row in m]
            if metric(rep) != base:
                return False, (f"{_render_matrix(m)} = {base:.3g} but with every checker "
                               f"duplicated {_render_matrix(rep)} = {metric(rep):.3g}")
    return True, "unchanged under checker replication"


def _probe_denominator(metric):
    facts_only = all(
        abs(metric(m) * len(m) - round(metric(m) * len(m))) < 1e-9 for m in _small_domain()
    )
    return ("facts" if facts_only else "factsTimesCheckers",
            "every value is a multiple of 1/facts" if facts_only
            else "some value is not a multiple of 1/facts (e.g. one dissent among three answers)")


def _probe_null_policy(metric):
    lone_null, lone_voice = metric([[True, True, None]]), metric([[True, None, None]])
    if lone_null > 0 and lone_voice > 0:
        return "punitive", "a lone null counts as dissent"
    if lone_null == 0 and lone_voice == 1.0:
        return "quorumBlocking", "a lone voice among nulls cannot reach quorum"
    if lone_null == 0 and lone_voice == 0:
        return "erasure", "a lone voice among nulls decodes"
    return "?", f"[T T _] = {lone_null:.3g}, [T _ _] = {lone_voice:.3g}"


def show_metric_properties():
    """The property matrix: what the model DECLARES for each metric against
    what exhaustive enumeration over {True, False, null}^(facts x 3),
    facts <= 2, FINDS — with the minimal counterexample where a property
    fails. The same check runs as a test over facts <= 3."""
    declared = declared_metric_properties()
    probes = (
        ("denominator", _probe_denominator),
        ("nullPolicy", _probe_null_policy),
        ("monotoneInDissent", _probe_monotone),
        ("saturatesAtUnanimousDissent", _probe_saturates),
        ("ensembleSizeInvariant", _probe_ensemble),
    )
    rows, agree, total = [], 0, 0
    for prop, probe in probes:
        cells = [("code", prop)]
        for name in METRICS:
            found, why = probe(METRICS[name])
            want = declared[name][prop]
            ok = found == want
            agree += ok
            total += 1
            shown = str(found).lower() if isinstance(found, bool) else found
            cells.append(f"{shown} {'✓' if ok else '✗ model says ' + str(want).lower()} — {why}")
        rows.append(tuple(cells))
    _table(("Property (declared in the model)", *METRICS), rows)
    print(f"declared = computed: {agree} of {total} cells agree "
          f"(the model asserts, the enumeration checks; the test suite repeats this over facts <= 3)")


def show_gate_reachability():
    """Which bindings can fire GATE-02 on the ensemble the recorded run
    used: the ensemble size is read from run-001's cogs_invoked, the value
    range of each metric is enumerated over every single-fact answer row,
    with and without abstention."""
    import itertools

    ds = _dataset("track/run-001.trig")
    cogs = len(set(ds.objects(None, __import__("rdflib").URIRef(VFR + "cogsInvoked"))))
    threshold = model_threshold()
    print(f"ensemble size from track/run-001.trig cogs_invoked: {cogs} checkers; "
          f"gate fires when the metric > {threshold}\n")
    unreachable = []
    for name, metric in METRICS.items():
        expressed = {metric([list(r)]) for r in itertools.product((True, False), repeat=cogs)}
        with_null = {metric([list(r)]) for r in itertools.product((True, False, None), repeat=cogs)}
        print(f"{name:26}: no abstention -> values {{{', '.join(f'{v:.3g}' for v in sorted(expressed))}}}"
              f"; with abstention -> values {{{', '.join(f'{v:.3g}' for v in sorted(with_null))}}}")
        if max(expressed) <= threshold:
            unreachable.append(name)
    print(f"\nwith {cogs} checkers and no abstention, GATE-02 cannot fire under: "
          f"{', '.join(unreachable) or '(none)'}")
    print("proposition (proved by enumeration, here and in the test suite for every odd "
          "ensemble size up to 7): over a two-valued domain, three expressed answers always "
          "contain a repeated value, so quorum-2 is met and the majority strictly exceeds "
          "half. Both undecodability metrics are identically zero; only abstention can make "
          "them nonzero. Their consistency with the section 5.5 example is a consequence of "
          "this, not evidence in their favour.")


def show_run_001_under_all_bindings():
    """The recorded run, re-evaluated: the matrix the Track records (GAP-12)
    recomputes the recorded value under the recorded metric, and the other
    two bindings say what they would have said about the same answers."""
    ds = _dataset("track/run-001.trig")
    row = next(iter(ds.query(f"""
        SELECT ?m ?matrix ?value WHERE {{
            ?call <{VFR}metric> ?m ; <{VFR}answerMatrix> ?matrix ;
                  <http://www.w3.org/ns/prov#generated> ?reading .
            ?reading <{VFR}value> ?value .
        }}""")))
    recorded_metric, matrix, recorded_value = str(row[0]), json.loads(str(row[1])), float(row[2])
    threshold = model_threshold()
    token = {True: "True ", False: "False", None: "null "}
    print(f"run-001 recorded: metric {recorded_metric}, value {recorded_value}, "
          f"matrix {len(matrix)} facts x {len(matrix[0])} checkers:")
    for i, fact in enumerate(matrix, 1):
        print(f"  f{i}: " + " ".join(token[v] for v in fact))
    recomputed = METRICS[recorded_metric](matrix)
    print(f"\nrun-001 recomputed under {recorded_metric}: {recomputed:.3f} "
          f"-> equals the recorded value: {recomputed == recorded_value}\n")
    print("the same answers under every binding the model admits:")
    for name, metric in METRICS.items():
        value = metric(matrix)
        tag = "  (the binding this run used)" if name == recorded_metric else ""
        print(f"  {name:26}: {value:.3f} -> GATE-02 fires: {value > threshold}{tag}")


def show_metric_sensitivity(facts=12, trials=500, seed=20260905):
    """How often the three bindings disagree about whether GATE-02 fires,
    and how often each fires, over a stated generative model. Cells are
    drawn independently: P(null) = p_abstain, otherwise P(False) =
    p_dissent. Checkers are exchangeable and conditionally independent,
    which real checkers are not — correlated dissent is what a consensus
    gate exists to catch — so read the numbers as a lower bound on how much
    the choice of binding matters. Deterministic: fixed seed, stdlib
    generator."""
    import random

    rng = random.Random(seed)
    ds = _dataset("track/run-001.trig")
    checkers = len(set(ds.objects(None, __import__("rdflib").URIRef(VFR + "cogsInvoked"))))
    threshold = model_threshold()
    grid = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]
    names = list(METRICS)
    fires = {n: 0 for n in names}
    cells = {}
    for p_abstain in grid:
        for p_dissent in grid:
            split = 0
            for _ in range(trials):
                m = []
                for _f in range(facts):
                    row = []
                    for _c in range(checkers):
                        if rng.random() < p_abstain:
                            row.append(None)
                        elif rng.random() < p_dissent:
                            row.append(False)
                        else:
                            row.append(True)
                    m.append(row)
                decisions = {n: METRICS[n](m) > threshold for n in names}
                for n in names:
                    fires[n] += decisions[n]
                split += len(set(decisions.values())) > 1
            cells[(p_abstain, p_dissent)] = split / trials
    total = trials * len(grid) ** 2
    print(f"generative model: independent cells, {facts} facts x {checkers} checkers, "
          f"{trials} trials per cell, gate fires when metric > {threshold}, seed {seed}\n")
    print("P(bindings disagree about whether GATE-02 fires)")
    print("  p_abstain \\ p_dissent " + "".join(f"{g:>7.2f}" for g in grid))
    for pa in grid:
        print(f"  {pa:>20.2f} " + "".join(f"{cells[(pa, pd)]:>7.3f}" for pd in grid))
    print("\nmarginal firing rate per binding, averaged over the grid "
          "(the expert-review load each binding would impose):")
    for n in names:
        print(f"  {n:26} {fires[n] / total:.3f}")
    worst = max(cells, key=cells.get)
    print(f"\nmaximum disagreement {cells[worst]:.3f} at p_abstain={worst[0]}, p_dissent={worst[1]}. "
          f"In the no-abstention row the maximum is {max(cells[(0.0, pd)] for pd in grid):.3f}: "
          "the reachability proposition showing up statistically, since there the two "
          "undecodability bindings never fire and dissent-fraction fires whenever dissent is common")


# ---------------------------------------------------------------- chapter 05

def _dataset(path):
    import rdflib

    ds = rdflib.Dataset(default_union=True)
    ds.parse(ROOT / path, format="trig")
    return ds


def _local(node):
    return str(node).rsplit("/", 1)[-1].rsplit("#", 1)[-1]


def _check_shapes(path):
    from pyshacl import validate

    return validate(_dataset(path), shacl_graph=str(ROOT / "shapes" / "track.shapes.ttl"))


def _describe_track(path):
    import rdflib
    from collections import Counter

    EARL = rdflib.Namespace("http://www.w3.org/ns/earl#")
    ds = _dataset(path)
    modes = Counter()
    outcomes = Counter()
    for a in set(ds.subjects(rdflib.RDF.type, EARL.Assertion)):
        modes[_local(ds.value(a, EARL.mode))] += 1
        result = ds.value(a, EARL.result)
        outcomes[_local(ds.value(result, EARL.outcome))] += 1
    gates = len(set(ds.subjects(rdflib.RDF.type, rdflib.URIRef(VFR + "GateDecision"))))
    obligations = sorted(
        _local(o) for o in ds.subjects(rdflib.RDF.type, rdflib.URIRef(VFR + "Obligation"))
    )
    discharges = sorted(
        f"{_local(a)} discharges {_local(o)}"
        for a, o in ds.subject_objects(rdflib.URIRef(VFR + "discharges"))
    )
    execution = ds.value(None, rdflib.RDF.type, rdflib.URIRef(VFR + "OpExecution"), any=True)
    aggregate = ds.value(execution, rdflib.URIRef(VFR + "aggregateOutcome")) if execution else None
    final = ds.value(execution, rdflib.URIRef(VFR + "finalOutput")) if execution else None
    withheld = sorted(
        str(ds.value(w, rdflib.RDFS.label) or _local(w))
        for w in ds.subjects(rdflib.RDF.type, rdflib.URIRef(VFR + "WithheldOutput"))
    )
    print(f"data checked: {path}")
    print("  assertions          : "
          + ", ".join(f"{n} {m}" for m, n in sorted(modes.items()))
          + " (outcomes: "
          + ", ".join(f"{n} {o}" for o, n in sorted(outcomes.items())) + ")")
    print(f"  gate decisions      : {gates}")
    print(f"  obligations raised  : {', '.join(obligations) or '(none)'}")
    if discharges:
        print("  discharging actions :")
        for d in discharges:
            print(f"    {d}")
    else:
        print("  discharging actions : (none)")
    if aggregate is not None:
        print(f"  aggregate outcome    : {aggregate}")
        print("  final_output cited   : "
              + (f"{_local(final)} ({ds.value(final, rdflib.RDFS.label)})" if final is not None
                 else "(none — nothing crossed the boundary)"))
        print("  withheld at boundary : "
              + ("; ".join(withheld) + " (retained as evidence — GAP-07)" if withheld else "(none)"))


def check_run_001_shapes():
    _describe_track("track/run-001.trig")
    conforms, _, _ = _check_shapes("track/run-001.trig")
    print(f"conforms: {conforms}")


def check_run_002_shapes():
    """The stopped run's Track (GAP-07, refined): noOp is a statement about
    the boundary. The record retains the readings, the gate decision, the
    stop and its escalation, and the artifact withheld at the boundary; the
    one thing it does not carry is a final_output."""
    _describe_track("track/run-002.trig")
    conforms, _, _ = _check_shapes("track/run-002.trig")
    print(f"conforms: {conforms}")


def refuse_missing_approval_track():
    import textwrap

    import rdflib

    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    _describe_track("counterexamples/track-missing-approval.trig")
    conforms, results, _ = _check_shapes("counterexamples/track-missing-approval.trig")
    violations = sorted(
        results.subjects(rdflib.RDF.type, SH.ValidationResult),
        key=lambda v: str(results.value(v, SH.focusNode)),
    )
    ds = _dataset("counterexamples/track-missing-approval.trig")
    undischarged = {
        _local(o) for o in ds.subjects(rdflib.RDF.type, rdflib.URIRef(VFR + "Obligation"))
        if ds.value(None, rdflib.URIRef(VFR + "discharges"), o, any=True) is None
    }
    focus = {_local(results.value(v, SH.focusNode)) for v in violations}
    print(f"conforms: {conforms} ({len(violations)} violations; "
          f"focus nodes equal the undischarged obligations: {focus == undischarged})")
    for i, v in enumerate(violations, 1):
        message = str(results.value(v, SH.resultMessage))
        print(f"\n  violation {i} — focus node: {_local(results.value(v, SH.focusNode))}")
        print(textwrap.indent(textwrap.fill(message, width=66), "    "))


_PREFIXES = {
    "https://example.org/vfr/track/run-001#": "run:",
    "https://example.org/vfr#": "vfr:",
    "http://www.w3.org/ns/earl#": "earl:",
    "http://www.w3.org/ns/prov#": "prov:",
}


def _short(value):
    s = str(value)
    for ns, prefix in _PREFIXES.items():
        if s.startswith(ns):
            return prefix + s[len(ns):]
    return s


def _result_table(res):
    import rdflib

    rows = []
    for row in res:
        cells = []
        for v in row:
            if v is None:
                cells.append("")
            elif isinstance(v, rdflib.URIRef):
                cells.append(("code", _short(v)))
            else:
                cells.append(str(v))
        rows.append(tuple(cells))
    if rows:
        _table([str(v) for v in res.vars], rows)
    else:
        print("(no rows)")


def show_query(name):
    ds = _dataset("track/run-001.trig")
    res = ds.query((ROOT / "queries" / name).read_text())
    _result_table(res)
    return res


def compare_governance():
    res = show_query("governance.rq")
    print(f"violations on run-001: {len(res)}")
    cx = _dataset("counterexamples/track-missing-approval.trig")
    cx_res = cx.query((ROOT / "queries" / "governance.rq").read_text())
    print(f"violations on the counterexample: {len(cx_res)}")
    _result_table(cx_res)


def show_learning():
    """The Learning purpose as a calibration view: each signal mapped to
    the part of the system it acts on, computed by joining the query
    against the model's gates and parameters."""
    gates = {gid: constraint for gid, _r, _t, constraint in _gates()}
    params = re.findall(r"attribute (\w+) : [\w:]+ =", _parameters_block())
    ds = _dataset("track/run-001.trig")
    res = ds.query((ROOT / "queries" / "learning.rq").read_text())
    rows = []
    for row in res:
        d = row.asdict()
        gate = str(d["gate"]) if d.get("gate") is not None else None
        if gate is not None:
            hit = [p for p in params if p in gates.get(gate, "")]
            acts = (f"{gate} — parameter {', '.join(hit)}, a single point of "
                    "definition: recalibrating is one edit" if hit else gate)
        elif str(d["kind"]) == "guard finding":
            acts = ("no gate is attached to this guard: the gate set itself "
                    "is the adaptation point (add a gate, or decide not to)")
        else:
            acts = "operator calibration: the rationale names what to change"
        rows.append((
            ("code", _short(d["signal"])),
            str(d["kind"]),
            str(d["detail"]),
            acts,
        ))
    _table(("Signal", "Kind", "Finding", "Acts on"), rows)
    distinct = len({r[0] for r in rows})
    print(f"learning signals: {distinct}, in {len(rows)} signal-to-surface "
          "pairs — calibration targets computed from the model's gates and "
          "factored parameters")


def show_learning_example():
    """A worked calibration (a logged suggestion in the judgment record):
    treat unknown vendor risk as high, in keeping with a conservative
    posture. The committed policy is untouched; the variant policy text
    exists only inside this function, to show one declared edit changing
    what the system obliges."""
    readings = {"confidence": 0.92, "consensus_disagreement": 0.10,
                "sensitive_data_detected": False, "vendor_risk": "unknown"}
    print("under the committed policy, GATE-04 binds on high alone; an "
          "unknown-risk vendor obliges nothing:")
    run_scenario("unknown-vendor-under-committed-policy", readings,
                 {"confidenceLevel": "high", "outputEmitted": True,
                  "aggregate": "executed"})
    original = ("pe.vendorRisk == pe.policy.vendorRiskTrigger "
                "implies pe.humanApprovalRequired")
    conservative = ("(pe.vendorRisk == pe.policy.vendorRiskTrigger or "
                    "pe.vendorRisk == RiskLevel::unknown) "
                    "implies pe.humanApprovalRequired")
    policy = _policy_text()
    assert original in policy, "GATE-04 constraint not found where expected"
    variant = policy.replace(original, conservative)
    print("\nthe calibration, one edit at the declared gate "
          "(a variant for this cell only; the committed policy is unchanged):")
    print(f"  - {original}")
    print(f"  + {conservative}")
    print("\nunder the conservative variant, the same evidence obliges an "
          "approval that was not obliged before:")
    run_scenario("unknown-vendor-under-conservative-variant", readings,
                 {"confidenceLevel": "high", "outputEmitted": True,
                  "aggregate": "executed"}, policy_text=variant)
    print()
    run_scenario("unknown-vendor-conservative-approved", readings,
                 {"confidenceLevel": "high",
                  "humanApprovalRequired": True, "humanApprovalGiven": True,
                  "outputEmitted": True, "aggregate": "executed"},
                 policy_text=variant)


def show_interface():
    ds = _dataset("track/run-001.trig")
    for row in ds.query((ROOT / "queries" / "interface.rq").read_text()):
        d = row.asdict()
        print(f"{d['variable']} = {d['value']}")
        print(f"  service      : {d['service']}")
        print(f"  sent payload : {d['requestPayload']}")
        print(f"  responseCode : {d['responseCode']}")
        print(f"  response     : {d['responsePayload']}")


# ---------------------------------------------------------------- chapter 06

def _adjudication_graph():
    import rdflib

    g = rdflib.Graph()
    g.parse(ROOT / "open-questions" / "adjudications.ttl", format="turtle")
    return g


def show_adjudication_record():
    import rdflib

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    rows = []
    for gap in sorted(g.subjects(rdflib.RDF.type, V.ComputabilityGap), key=str):
        rulings = sorted(set(g.subjects(V.resolves, gap)) | set(g.subjects(V.defers, gap)), key=str)
        who = sorted({_local(g.value(r, PROV.wasAttributedTo)) for r in rulings})
        dates = sorted({str(g.value(r, PROV.generatedAtTime)) for r in rulings})
        rows.append((
            ("code", f"{_local(gap)} — {g.value(gap, rdflib.RDFS.label)}"),
            str(g.value(gap, V.problem)),
            f"{g.value(gap, V.surfacedOn)}: {g.value(gap, V.surfacedHow)}",
            ("code", str(g.value(gap, V.status))),
            f"{len(rulings)} ruling(s) by {', '.join(who)} on {', '.join(dates)}",
        ))
    _table(("Gap", "Problem", "Surfaced", "Status", "Resolution"), rows)


def _md_lite(text):
    """Escape for HTML, then render the two markdown forms the record's
    prose uses (backtick code spans, **bold**) and keep line breaks."""
    import html as html_mod

    s = html_mod.escape(str(text))
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s.replace("\n", "<br/>")


def show_gap_characterizations():
    import html as html_mod

    import rdflib
    from IPython.display import HTML, display

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    blocks = []
    for gap in sorted(g.subjects(rdflib.RDF.type, V.ComputabilityGap), key=str):
        fields = [
            ("Locus", g.value(gap, V.locusDetail)),
            ("Problem", g.value(gap, V.problem)),
            ("Surfaced", f"{g.value(gap, V.surfacedOn)}: {g.value(gap, V.surfacedHow)}"),
            ("The substrate forces", g.value(gap, V.substrateForces)),
            ("Readings considered", g.value(gap, V.possibleReadings)),
            ("Reading in use", g.value(gap, V.readingInUse)),
        ]
        note = g.value(gap, V.note)
        if note is not None:
            fields.append(("Notes", note))
        items = "\n".join(
            f'<li style="text-align:left"><strong>{label}:</strong> '
            f"{_md_lite(value)}</li>"
            for label, value in fields
        )
        blocks.append(
            f'<p style="text-align:left"><strong>{_local(gap)} — '
            f"{html_mod.escape(str(g.value(gap, rdflib.RDFS.label)))}</strong> "
            f"[{g.value(gap, V.status)}]</p>\n<ul>\n{items}\n</ul>"
        )
    display(HTML("\n".join(blocks)))


def show_rulings_log():
    import html as html_mod

    import rdflib
    from IPython.display import HTML, display

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    entries = sorted(
        ((int(g.value(n, V.order)), n) for n in set(g.subjects(V.order, None))),
    )
    blocks = []
    rulings = notes = 0
    for order, node in entries:
        text = g.value(node, V.rulingText)
        if text is not None:
            rulings += 1
        else:
            text = g.value(node, V.noteText)
            notes += 1
        blocks.append(
            f'<p style="text-align:left"><strong>{order}. '
            f"{html_mod.escape(str(g.value(node, V.entryTitle)))}</strong> "
            f"({g.value(node, PROV.generatedAtTime)}, "
            f"{_local(g.value(node, PROV.wasAttributedTo))})</p>\n"
            f'<blockquote style="text-align:left">{_md_lite(text)}'
            "</blockquote>\n"
            f'<p style="text-align:left"><em>Changed:</em> '
            f"{_md_lite(g.value(node, V.changeNote))}</p>"
        )
    display(HTML("\n".join(blocks)))
    print(f"log entries rendered: {len(entries)} — "
          f"{rulings} rulings, {notes} notes")


def show_judgment_trace():
    import rdflib

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    rows = []
    for impl in sorted(g.subjects(rdflib.RDF.type, V.Implementation), key=str):
        ruling = g.value(impl, PROV.wasDerivedFrom)
        gap = g.value(ruling, V.resolves) or g.value(ruling, V.defers)
        if gap is not None:
            resolves = f"{_local(gap)} @ {g.value(gap, V.locator)}"
        elif (ruling, rdflib.RDF.type, V.ReviewNote) in g:
            resolves = "external review finding (no gap: a repair the review drove)"
        else:
            resolves = "design note (no gap: a recorded suggestion)"
        rows.append((
            str(g.value(impl, rdflib.RDFS.label)),
            ("code", str(g.value(impl, V.inFile))),
            ("code", f"{_local(ruling)} ({_local(g.value(ruling, PROV.wasAttributedTo))}, "
                     f"{g.value(ruling, PROV.generatedAtTime)})"),
            ("code", resolves),
        ))
    _table(("Implementation", "File", "Derived from ruling", "Resolves gap"), rows)
    print(f"traceable implementations: {len(rows)} "
          "(each: implementation -> ruling -> named adjudicator -> gap -> pinned source)")


def check_adjudication_record():
    import rdflib
    from pyshacl import validate

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    n_gaps = len(set(g.subjects(rdflib.RDF.type, V.ComputabilityGap)))
    n_rulings = len(set(g.subjects(rdflib.RDF.type, V.Ruling)))
    n_impls = len(set(g.subjects(rdflib.RDF.type, V.Implementation)))
    conforms, _, _ = validate(g, shacl_graph=str(ROOT / "shapes" / "adjudication.shapes.ttl"))
    print(f"the record ({n_gaps} gaps, {n_rulings} rulings, {n_impls} implementations) "
          f"conforms: {conforms}")
    cx = rdflib.Graph()
    cx.parse(ROOT / "counterexamples" / "adjudication-unattributed.ttl", format="turtle")
    conforms, results, _ = validate(cx, shacl_graph=str(ROOT / "shapes" / "adjudication.shapes.ttl"))
    SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
    print(f"unattributed-ruling counterexample   conforms: {conforms}")
    for v in results.subjects(rdflib.RDF.type, SH.ValidationResult):
        print(f"  {results.value(v, SH.resultMessage)}")


def show_checks_outcomes():
    report = ROOT / "checks" / "out" / "report.json"
    if not report.exists():
        print("no report yet — run: checks/run-checks.sh")
        return
    data = json.loads(report.read_text())
    for name, outcome in data["steps"].items():
        print(f"{outcome:5} {name}")
    print(f"result: {data['result']}")
