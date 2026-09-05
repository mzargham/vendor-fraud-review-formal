# vendor-fraud-review-formal

The **Vendor Fraud Review Op** — the running example of *The Distributed AI
Economy: Intelligence Hubs, Frames, Cogs, Ops, and the Accountability Plane*
(Revision 9, August 2026) — implemented as an **executable specification**.

The whitepaper's section 5.6 manifest is rendered onto an RDF + SysML
substrate, using only open standards:

- **SKOS** — the paper's concepts (Op, Cog, Frame, Guard, Gate, Track, and
  more), definitions verbatim from a sha256-pinned snapshot of the PDF, each
  machine-checked against the source text.
- **OpenSysML** (pinned v0.4.3) — the four gates as `implies` constraints,
  evaluated over concrete runs: the clean run holds, the escalated run holds
  because the human step is engaged, and a counterexample run with no human
  in the loop fails with exit 1.
- **PROV-O + EARL** — one execution Track: automatic Guard results (passed,
  failed, cantTell), fired Gates, and a named human approval (`earl:manual`).
- **SHACL** — shapes derived from the manifest's own `track.include` list,
  with counterexamples proving they have teeth.
- **SPARQL** — the section 5.3 Track purposes (auditability, governance,
  trust) computed from the run graph.

## Read it

The primary artifact is the notebook — every claim in it is the output of an
executed cell:

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
