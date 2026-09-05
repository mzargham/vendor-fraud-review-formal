# Computability gaps

Places where a literal parsing of the whitepaper (Revision 9) under-specifies
what the executable substrate requires. Nothing here is silently repaired: where
the build could not proceed without a choice, the most literal available reading
was taken, marked `provisional: GAP-nn` at the point of use, and logged here.
Every entry stays PENDING until an adjudication is recorded in
`adjudication-log.md`. Possible readings are listed without a choice being
made in the entry; the provisional reading is only what the build currently
runs with.

## GAP-01 — the type of `vendor_risk` and the value `high`

**Status:** PENDING
**Locus:** WP §5.6, gates block: `- if: vendor_risk == high` / `then: human_approval_required`
**Problem:** `high` is an unquoted symbol; the manifest declares no type or value
set for `vendor_risk`. An executable comparison needs both.
**Substrate forces:** an attribute type and a comparable literal.
**Possible readings:** (a) an enumeration (e.g. low / medium / high) declared
somewhere upstream, perhaps by the vendor-risk-cog; (b) a free string compared
to "high"; (c) an ordered scale with `high` a threshold on a numeric score.
**Provisional reading in use:** (b) — `vendorRisk : String` compared to
`"high"` (model/vendor-fraud-review.sysml).

## GAP-02 — what a `then:` clause names

**Status:** PENDING
**Locus:** WP §5.6, gates block: `then: human_review_required`,
`then: expert_review_required`, `then: stop_and_escalate`,
`then: human_approval_required`; and §5.2 ("A Gate may allow the Op to
continue, pause the workflow, request human approval, escalate to an expert,
retry with a different Cog, run additional validation, or stop the Op
entirely.")
**Problem:** §5.2 describes Gate outcomes as actions on the workflow;
the §5.6 manifest writes them as bare identifiers. Whether a then-clause names
a state the Op enters, an obligation that must be discharged (and recorded on
the Track), or an action to be performed is not stated — and `stop_and_escalate`
is grammatically an action while `human_review_required` is grammatically a
predicate.
**Substrate forces:** one ontological kind per identifier before it can be
constrained or queried.
**Possible readings:** (a) states of the Op instance; (b) obligations whose
discharge the Track must evidence; (c) invocations of workflow actions.
**Provisional reading in use:** (a)/(b) hybrid — Boolean attributes that must
hold whenever their gate condition holds (model), with the Track shapes
additionally requiring a recorded human approval when a Gate fired
(shapes/track.shapes.ttl).

## GAP-03 — the provenance and granularity of `confidence`

**Status:** PENDING
**Locus:** WP §5.6: `- confidence-guard` (in_flight) and
`- if: confidence < 0.80`; §5.1 lists "whether confidence is too low for
autonomous action" as something a Guard can check.
**Problem:** the manifest never says which Guard produces the `confidence`
value the gate reads, nor whether it is per-output, per-Cog, or per-run. Three
Cogs run in this Op; each could carry its own confidence.
**Substrate forces:** one referent for the gate's variable.
**Possible readings:** (a) the minimum across Cog outputs; (b) the
invoice-extraction Cog's confidence specifically (the §4.1 running example
speaks of "low extraction confidence"); (c) a distinct confidence per Gate
evaluation.
**Provisional reading in use:** one per-run scalar, produced by the
confidence Guard and read by GATE-01 (model + track/run-001.trig).

## GAP-04 — the semantics of `consensus_disagreement`

**Status:** PENDING
**Locus:** WP §5.6: `- if: consensus_disagreement > 0.25`; §5.5 Consensus row
("Three Cogs classify a document and two must agree; outlier extractions
flagged").
**Problem:** no definition of the disagreement metric is given anywhere in the
paper: not its range, not what it is computed over, not how "two of three must
agree" maps to a number comparable with 0.25.
**Substrate forces:** a typed quantity for the comparison to execute.
**Possible readings:** (a) fraction of dissenting Cogs; (b) 1 − pairwise
agreement rate; (c) a task-specific divergence score normalized to [0, 1].
**Provisional reading in use:** an opaque scalar in [0, 1]; only the threshold
comparison is exercised, no metric semantics assumed (model).
