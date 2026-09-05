# vendor-fraud-review-formal

The **Vendor Fraud Review Op** — the running example of *The Distributed AI
Economy: Intelligence Hubs, Frames, Cogs, Ops, and the Accountability Plane*
(Revision 9, August 2026) — implemented as an **executable specification**.

The whitepaper's section 5.6 manifest is rendered onto an RDF + SysML
substrate, using only open standards:

- **SKOS** — the paper's concepts (Op, Cog, Frame, Guard, Gate, Track, and
  more), definitions verbatim from a sha256-pinned snapshot of the PDF, each
  machine-checked against the source text.
- **OpenSysML** (pinned v0.4.3) — the Op as an assembly of abstract and
  concrete parts wired along ports, checked at three levels in one
  toolchain: component (the four gates as `implies` constraints), wiring
  (seam integrity in satisfy; structural seam conformance in code over the
  conversion), and system (obligations discharged across components; a
  stopped Op emits nothing; the aggregate outcome — executed vs noOp — must
  cohere). The assembly's lifecycle (running → stopped | completed) runs
  under trace. Counterexamples fail one per level, and a miswired seam is
  refused by the wiring rules.
- **PROV-O + EARL** — one execution Track: automatic Guard results (passed,
  failed, cantTell), fired Gates, and a named human approval (`earl:manual`).
- **SHACL** — shapes derived from the manifest's own `track.include` list,
  with counterexamples proving they have teeth.
- **SPARQL** — the section 5.3 Track purposes (auditability, governance,
  trust) computed from the run graph.

## Read it

The primary artifact is the notebook — every claim in it is the output of an
executed cell, including narrated worked examples that mock the oracles and
drive each scenario (the happy path, every gate binding with its obligation
discharged or neglected, a mislabeled category) through the committed policy
text itself:

```sh
uv sync
uv run jupyter lab demonstration.ipynb   # interactive
npx mystmd start                         # rendered MyST site
```

## Run the checks

```sh
checks/run-checks.sh
```

One script: pinned toolchain, strict validation, the satisfy sweep, the
counterexample inversion, byte-stable regeneration of `generated/`, and the
full test suite. It writes `checks/out/report.json` and ends with a single
`CHECKS: PASS|FAIL` line.

## Open questions

Where a literal parsing of the paper under-specifies what an executable
substrate requires, nothing was silently repaired: the reading in force is
marked `provisional` at its point of use and logged as a PENDING entry in
[open-questions/computability-gaps.md](open-questions/computability-gaps.md).
