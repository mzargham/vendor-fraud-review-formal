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
   constraints; checks at component, wiring, and system level; a
   lifecycle run under trace (`model/vendor-fraud-review.sysml`). Every
   named element traces to the source, to a recorded adjudication, or
   declares itself scaffolding (`model/trace.ttl`).
4. **A run record.** One fabricated execution as a PROV-O + EARL Track
   with an oracle citation for every value a gate read
   (`track/run-001.trig`), SHACL shapes it must conform to, and
   counterexamples the shapes refuse.
5. **Queries.** The five Track purposes section 5.3 names (auditability,
   governance, learning, debugging, trust) computed by SPARQL over the
   run graph (`queries/`).
6. **A judgment record.** Code is not objective; its objectivity is
   downstream of judgment calls. Every gap the translation surfaced, the
   ruling that resolved it (verbatim, attributed, dated), and the
   implementations that resulted are RDF
   (`open-questions/adjudications.ttl`); the appendix pages are
   generated views of it.

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
generated artifact (conversion, query results, both appendix pages, both
derived counterexamples), the site build, and the full test suite. It
ends with a single `CHECKS: PASS|FAIL` line.

## Layout

| Path | What it holds |
|---|---|
| `sources/` | the sha256-pinned snapshot and its retrieval provenance |
| `vocabulary/` | SKOS concepts, definitions verbatim from the snapshot |
| `model/` | the executable assembly and its traceability map |
| `track/` | the recorded run |
| `shapes/` | SHACL over the Track, the judgment record, and the trace |
| `queries/` | the five section 5.3 purposes as SPARQL |
| `counterexamples/` | negatives every checking layer must refuse |
| `open-questions/` | the judgment record and its two generated pages |
| `chapters/`, `index.md` | the walkthrough (executed notebooks + front door) |
| `exhibits.py` | the committed machinery the chapter cells call |
| `checks/`, `tests/` | the gate script, renderers, and test suite |

## Disclosure

The whitepaper provides the manifest, not data. The recorded run, its
named approver, the vendors, invoices, readings, and every human actor
in the narration are fabricated example data; the named people are
inventions. Nothing here comes from any real organization.
