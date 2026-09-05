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
                verify i1; verify g1; verify g2; verify g3; verify g4;
                verify w1; verify w2; verify w3; verify w4;
                verify s1; verify s2; verify s3;
            }
        }
        verification scenarioCase : ScenarioCase;
    }
}
"""


def run_scenario(name, readings, recorded):
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
        f.write(_policy_text() + scenario)
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
DisagreementMetric = Callable[[Sequence[Sequence[bool | None]]], float]


def dissent_fraction(matrix):
    dissents = total = 0
    for fact in matrix:
        dissents += sum(1 for v in fact if v is not True)
        total += len(fact)
    return dissents / total


def strict_quorum_undecodable(matrix):
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v is not None]
        if not expressed or max(expressed.count(v) for v in set(expressed)) < 2:
            undecodable += 1
    return undecodable / len(matrix)


def erasure_aware_undecodable(matrix):
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v is not None]
        if not expressed or max(expressed.count(v) for v in set(expressed)) * 2 <= len(expressed):
            undecodable += 1
    return undecodable / len(matrix)


METRICS: dict[str, DisagreementMetric] = {
    "dissent-fraction": dissent_fraction,
    "strict-quorum-undecodable": strict_quorum_undecodable,
    "erasure-aware-undecodable": erasure_aware_undecodable,
}

ANSWER_MATRIX = [
    [True, True, True],
    [True, True, True],
    [True, True, True],
    [True, True, False],
    [True, True, None],
    [True, False, None],
    [False, None, True],
    [True, None, None],
]


def evaluate_metrics():
    print("type signature: DisagreementMetric = "
          "(fact x checker answer matrix of nullable Bool; "
          "True = agree, False = disagree, null = cannot tell) -> [0, 1]\n")
    threshold = float(re.search(
        r"consensusDisagreementThreshold : ScalarValues::Real = ([0-9.]+)",
        MODEL.read_text()).group(1))
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
    defs = re.findall(r"part def (\w+Metric) :> DisagreementMetric", MODEL.read_text())
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


def check_run_001_shapes():
    _describe_track("track/run-001.trig")
    conforms, _, _ = _check_shapes("track/run-001.trig")
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


def show_judgment_trace():
    import rdflib

    g = _adjudication_graph()
    V = rdflib.Namespace(VFR)
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    rows = []
    for impl in sorted(g.subjects(rdflib.RDF.type, V.Implementation), key=str):
        ruling = g.value(impl, PROV.wasDerivedFrom)
        gap = g.value(ruling, V.resolves) or g.value(ruling, V.defers)
        rows.append((
            str(g.value(impl, rdflib.RDFS.label)),
            ("code", str(g.value(impl, V.inFile))),
            ("code", f"{_local(ruling)} ({_local(g.value(ruling, PROV.wasAttributedTo))}, "
                     f"{g.value(ruling, PROV.generatedAtTime)})"),
            ("code", f"{_local(gap)} @ {g.value(gap, V.locator)}"),
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
