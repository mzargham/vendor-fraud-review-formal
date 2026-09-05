# vendor-fraud-review-formal

The **Vendor Fraud Review Op** of *The Distributed AI Economy:
Intelligence Hubs, Frames, Cogs, Ops, and the Accountability Plane*
(Revision 9, August 2026), implemented as an executable specification.
This is a translation, not an audit: the whitepaper's section 5.6
manifest is rendered onto an RDF + SysML substrate without altering or
judging the source, and every place the written form left something an
executable form must decide, the judgment was flagged, attributed, and
recorded rather than blended in.

## The layers

Each layer is machine-checked; nothing below is a prose-only claim.

1. **A pinned source.** One content-addressed PDF snapshot of the
   whitepaper (the filename is its own sha256). Every definition, quote,
   and section locator in this repo is verified against it, inside the
   section it cites.
2. **A verbatim vocabulary.** The paper's concepts as SKOS, definitions
   lifted exactly from the pinned text (`vocabulary/op-concepts.ttl`).
3. **An executable model.** The manifest as an OpenSysML assembly:
   oracle components wired along ports to a policy engine, counterparty
   actions, and a summary cog; the four gates as satisfiable
   constraints; the consensus metric as a typed class whose declared
   properties are proved by enumeration; checks at type, component,
   wiring, and system level; a
   lifecycle run under trace (`model/vendor-fraud-review.sysml`). Every
   named element traces to the source, to a recorded adjudication, or
   declares itself scaffolding (`model/trace.ttl`).
4. **A run record.** One fabricated execution as a PROV-O + EARL Track
   with an oracle citation for every value a gate read
   (`track/run-001.trig`), SHACL shapes it must conform to, and
   counterexamples the shapes refuse.
5. **Queries.** The five Track purposes section 5.3 names (auditability,
   governance, learning, debugging, trust), plus the GAP-05 interface
   contract, computed by SPARQL over the run graph (`queries/`).
6. **A judgment record.** Code is not objective; its objectivity is
   downstream of judgment calls. Every gap the translation surfaced, the
   ruling that resolved it (verbatim, attributed, dated), and the
   implementations that resulted are RDF
   (`open-questions/adjudications.ttl`); the walkthrough's
   open-questions chapter renders it in full.

## Read it

The walkthrough is a chaptered MyST site; its index page is the front
door, and every claim on its pages is the output of an executed cell:

```sh
uv sync
uv run myst start
```

## Verify it

```sh
checks/run-checks.sh
```

One script: pinned toolchain, strict validation, the satisfy sweep, the
counterexamples that must fail, byte-identical regeneration of every
generated artifact (conversion, query results, both derived
counterexamples), the site build, and the full test suite. It ends with
a single `CHECKS: PASS|FAIL` line.

## Layout

| Path | What it holds |
|---|---|
| `sources/` | the sha256-pinned snapshot and its retrieval provenance |
| `vocabulary/` | SKOS concepts, definitions verbatim from the snapshot |
| `model/` | the executable assembly and its traceability map |
| `track/` | the recorded run |
| `shapes/` | SHACL over the Track, the judgment record, and the trace |
| `queries/` | the five section 5.3 purposes + the interface contract, as SPARQL |
| `counterexamples/` | negatives every checking layer must refuse |
| `open-questions/` | the judgment record (adjudications.ttl) |
| `generated/` | byte-stability witnesses: the RDF conversion and query results the checks re-render and diff |
| `toolchain/` | the checksum-verified fetch of the pinned evaluator |
| `chapters/`, `index.md` | the walkthrough (executed notebooks + front door) |
| `exhibits.py` | the committed machinery the chapter cells call |
| `checks/`, `tests/` | the gate script, renderers, and test suite |

## Publishing

`.github/workflows/deploy.yml` gates and publishes: on every push to
main it runs the full check gate on a clean runner (the same
`checks/run-checks.sh`, ending in one PASS/FAIL), and only a passing
gate deploys the walkthrough to GitHub Pages. One-time setup after the
repository has a GitHub remote: Settings → Pages → Source → GitHub
Actions.

## Disclosure

The whitepaper provides the manifest, not data. The recorded run, its
named approver, the vendors, invoices, readings, and every human actor
in the narration are fabricated example data; the named people are
inventions. Nothing here comes from any real organization.

## License

The original content of this repository (the model, vocabulary
structure, shapes, queries, judgment record, walkthrough, and tooling)
is licensed under [CC BY-SA 4.0](LICENSE). The pinned whitepaper
snapshot in `sources/` and the verbatim quotations drawn from it remain
the property of their author and are not covered by the repository
license; the snapshot is redistributed with citation back to its source
(`references.bib`, `sources/sources.ttl`), per the statement recorded
in the judgment record.
