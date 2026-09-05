# The Vendor Fraud Review Op as an executable specification

## What this is, and what it is not

This walkthrough is an exercise in rendering a whitepaper computational.
It takes the running example of *The Distributed AI Economy*
[@oliphant2026] and implements it, literally, on an executable substrate.
It makes no attempt to alter or cast judgment on that work: this is a
translation, not an audit. Where the translation had to fill a gap, the
gap belongs to the limits of the written form, not to oversights by the
author; prose can leave open what an executable substrate must decide.
Where filling those gaps required judgment calls, they are ours, and each
one is acknowledged and logged with its ruling in the appendix rather
than silently blended into the model.

The scope is deliberately narrow. This is not the full scope of the
whitepaper; it is one piece of it, the section 5.6 Vendor Fraud Review
Op and its Validation Strategy manifest, chosen because a single
concrete Op manifest is well suited to this kind of demonstration. The
wider architecture (Intelligence Hubs, Frames, the accountability plane
as a whole) is cited but not modeled.

One more boundary. The whitepaper provides the manifest, not data:
every run shown here is fabricated example data, constructed to
exercise the specification. That includes the recorded execution and
its named approver, the vendors, invoices, and oracle readings in the
worked examples, and the human actors in the narration. The named
people are inventions, not real persons; they appear because the record
requires a named accountable party. None of this content comes from the
paper or from any real organization.

> An Op is not complete unless it declares how its work will be
> verified.
>
> — [@oliphant2026, §5.6]

This walkthrough takes that sentence at full strength: the declaration
becomes a specification a machine can check, and everything shown here
is the output of executed code. Every quotation from the whitepaper on
these pages is itself machine-checked, verbatim, against a pinned
snapshot of the document.

## How it was made

The substrate is a small stack of open standards, one layer per job:

1. **A pinned source.** One content-addressed PDF snapshot of the
   whitepaper (its filename is its own sha256). Every definition and
   every quotation traces to it.
2. **A verbatim vocabulary.** The paper's concepts (Op, Cog, Frame,
   Guard, Gate, Track, and more) as SKOS [@skos2009] concepts whose
   definitions are lifted exactly from the pinned text, with section
   locators, and checked against the PDF by the test suite.
3. **An executable model.** The section 5.6 manifest as an OpenSysML
   [@opensysml043] assembly: oracle components wired along ports to a
   policy engine, counterparty actions, and a summary cog, with the
   four gates as constraints and checks at three levels (component,
   wiring, system).
4. **A run record.** One execution as a PROV-O [@provo2013] + EARL
   [@earl2017] Track, with SHACL [@shacl2017] shapes that the record
   must conform to, and counterexamples proving the shapes can refuse.
5. **Queries.** The purposes section 5.3 names for a Track
   (auditability, governance, trust) answered by SPARQL [@sparql2013]
   over the run graph [@rdf2014].
6. **A judgment record.** Code is not objective; its objectivity is
   downstream of judgment calls. Where the text under-specified what an
   executable specification requires, each gap, the ruling that
   resolved it (verbatim, attributed to a named adjudicator, dated),
   and the implementations that resulted are themselves RDF, traceable
   end to end and checked by their own shapes.

## How to read it

Each chapter opens with what the whitepaper says (quoted and cited),
states what the substrate makes of it, executes, and interprets the
output. The chapters build in order, but each stands on its own:

1. **The pinned source** — the snapshot, its hash, and the vocabulary
   checked verbatim against it.
2. **The Op as an assembly** — the model, the four gates, the seams,
   the lifecycle, and the counterexamples the specification refuses.
3. **Worked examples** — eight narrated runs with mocked oracles,
   driven through the committed policy text itself.
4. **One type, three semantics** — the consensus-disagreement metric as
   an open policy question, exhibited rather than answered.
5. **The Track** — the durable record, its shapes, and the queries that
   answer the paper's own questions about it.
6. **Open questions** — everything the translation could not settle
   without judgment, and the rulings in force.

The appendix holds the full list of computability gaps and the log of
rulings, verbatim.

## Running it

```sh
uv sync
uv run myst start        # this site, served locally
checks/run-checks.sh     # the whole stack, one PASS/FAIL line
```

Every chapter notebook executes headlessly in the test suite, and the
committed outputs shown on these pages are asserted equal to a fresh
execution. Nothing on these pages is prose-only.
