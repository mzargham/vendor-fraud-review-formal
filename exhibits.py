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

def show_policy_parameters():
    source = MODEL.read_text()
    print(re.search(r"part def ValidationStrategyParameters .*?\n        }", source, re.S).group(0))


def show_gate_checks():
    source = MODEL.read_text()
    for block in re.findall(r"requirement def <'GATE-\d+'>.*?\n        }", source, re.S)[:1]:
        print(block)


def show_seams():
    source = MODEL.read_text()
    print("\n".join(
        l.strip() for l in source.splitlines() if "connect" in l and "interface" in l
    ))


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

    graph, _ = _converted(MODEL)
    mismatches = check_seam_conformance(graph)
    print("committed assembly (6 seams): "
          + ("wiring rules: OK" if not mismatches else f"wiring rules: REFUSED {mismatches}"))
    graph_bad, _ = _converted(ROOT / "counterexamples" / "miswired.sysml")
    bad = check_seam_conformance(graph_bad)
    print("miswired counterexample: "
          + ("wiring rules: OK (?!)" if not bad else "wiring rules: REFUSED"))
    for m in bad:
        print("  " + m)


def show_lifecycle():
    for ctx in ("VendorFraudReview::ExerciseContexts::stoppedContext",
                "VendorFraudReview::ExerciseContexts::completedContext"):
        r = _sysml(str(MODEL), "-trace", "-instantiate", ctx)
        print(ctx.split("::")[-1])
        lines = [l for l in r.stdout.splitlines() if "transition:" in l or "enter:" in l]
        for line in lines[:8]:
            print("  " + line)
        print()


def check_conversion():
    import rdflib

    c1 = _sysml(str(MODEL), "-convert", "ttl")
    c2 = _sysml(str(MODEL), "-convert", "ttl")
    mg = rdflib.Graph()
    mg.parse(data=c1.stdout, format="turtle")
    print(f"converted triples : {len(mg)}")
    print(f"byte-stable       : {c1.stdout == c2.stdout}")
    checks = ("GATE-01", "GATE-02", "GATE-03", "GATE-04",
              "WIRE-01", "SYSTEM-01", "SYSTEM-02", "SYSTEM-03")
    print(f"checks present    : {[rid for rid in checks if rid in c1.stdout]}")


# ---------------------------------------------------------------- chapter 03

SERVICES = {
    "confidence": "extraction-confidence service",
    "consensus_disagreement": "consensus-comparator service",
    "sensitive_data_detected": "sensitive-data-scanner service",
    "vendor_risk": "vendor-risk-cog scoring endpoint",
}


def _policy_text():
    return MODEL.read_text().split("    package RunConfigurations {")[0]


def show_policy_reuse():
    digest = hashlib.sha256(_policy_text().encode()).hexdigest()[:12]
    print("policy reused byte-identical from model/vendor-fraud-review.sysml "
          f"(sha256 {digest})")


def mock_oracle(variable, value):
    payload = json.dumps({"op": "vendor-fraud-review", "variable": variable})
    print(f"  mock oracle {SERVICES[variable]}: sent {payload} "
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
            part :>> humanAction {
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

DisagreementMetric = Callable[[Sequence[Sequence[str]]], float]


def dissent_fraction(matrix):
    dissents = total = 0
    for fact in matrix:
        expressed = [v for v in fact if v != "?"]
        modal = max(set(expressed), key=expressed.count) if expressed else None
        dissents += sum(1 for v in fact if v != modal)
        total += len(fact)
    return dissents / total


def strict_quorum_undecodable(matrix):
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v != "?"]
        if not expressed or max(expressed.count(v) for v in set(expressed)) < 2:
            undecodable += 1
    return undecodable / len(matrix)


def erasure_aware_undecodable(matrix):
    undecodable = 0
    for fact in matrix:
        expressed = [v for v in fact if v != "?"]
        if not expressed or max(expressed.count(v) for v in set(expressed)) * 2 <= len(expressed):
            undecodable += 1
    return undecodable / len(matrix)


METRICS: dict[str, DisagreementMetric] = {
    "dissent-fraction": dissent_fraction,
    "strict-quorum-undecodable": strict_quorum_undecodable,
    "erasure-aware-undecodable": erasure_aware_undecodable,
}

ANSWER_MATRIX = [
    ["A", "A", "A"],
    ["A", "A", "A"],
    ["A", "A", "A"],
    ["A", "A", "B"],
    ["A", "A", "?"],
    ["A", "B", "?"],
    ["A", "B", "C"],
    ["A", "?", "?"],
]


def evaluate_metrics():
    print("type signature: DisagreementMetric = "
          "(facts x readers answer matrix, '?' = cantTell) -> [0, 1]\n")
    threshold = float(re.search(
        r"consensusDisagreementThreshold : ScalarValues::Real = ([0-9.]+)",
        MODEL.read_text()).group(1))
    print(f"same answer matrix for all three metrics ({len(ANSWER_MATRIX)} facts x 3 readers):")
    for i, fact in enumerate(ANSWER_MATRIX, 1):
        print(f"  f{i}: " + " ".join(fact))
    print(f"threshold (from the model, single point of definition): > {threshold}\n")
    for name, metric in METRICS.items():
        value = metric(ANSWER_MATRIX)
        print(f"{name:26}: {value:.3f} -> gate fires: {value > threshold}")


def show_metric_definitions():
    source = MODEL.read_text()
    for block in re.findall(
        r"(?:abstract )?part def \w+Metric[^\n]*\{.*?\n        \}", source, re.S
    ):
        print(block)
        print()


# ---------------------------------------------------------------- chapter 05

def _dataset(path):
    import rdflib

    ds = rdflib.Dataset(default_union=True)
    ds.parse(ROOT / path, format="trig")
    return ds


def check_track_shapes():
    from pyshacl import validate

    def check(path):
        return validate(_dataset(path), shacl_graph=str(ROOT / "shapes" / "track.shapes.ttl"))

    conforms, _, _ = check("track/run-001.trig")
    print(f"run-001               conforms: {conforms}")
    conforms, _, report = check("counterexamples/track-missing-approval.trig")
    print(f"missing-approval      conforms: {conforms}")
    print("\n".join(line for line in report.splitlines() if "Message" in line))


def show_query(name):
    ds = _dataset("track/run-001.trig")
    res = ds.query((ROOT / "queries" / name).read_text())
    print(" | ".join(str(v) for v in res.vars))
    for row in res:
        print(" | ".join(str(v) for v in row))
    return res


def compare_governance():
    res = show_query("governance.rq")
    print(f"violations on run-001: {len(res)}")
    cx = _dataset("counterexamples/track-missing-approval.trig")
    cx_res = cx.query((ROOT / "queries" / "governance.rq").read_text())
    print(f"violations on the counterexample: {len(cx_res)}")
    for row in cx_res:
        print("  " + " | ".join(str(v) for v in row))


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

def list_open_questions():
    text = (ROOT / "open-questions" / "computability-gaps.md").read_text()
    for m in re.finditer(r"^## (GAP-\d+) — (.+?)$.*?\*\*Status:\*\* (.+)$", text, re.S | re.M):
        status = re.sub(r"\s*\([^)]*\)", "", m.group(3)).strip()
        print(f"{m.group(1)}  [{status}]  {m.group(2)}")


def show_checks_outcomes():
    report = ROOT / "checks" / "out" / "report.json"
    if not report.exists():
        print("no report yet — run: checks/run-checks.sh")
        return
    data = json.loads(report.read_text())
    for name, outcome in data["steps"].items():
        print(f"{outcome:5} {name}")
    print(f"result: {data['result']}")
