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

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §5.6, gates block: `- if: vendor_risk == high` / `then: human_approval_required`
**Problem:** `high` is an unquoted symbol; the manifest declares no type or value
set for `vendor_risk`. An executable comparison needs both.
**Substrate forces:** an attribute type and a comparable literal.
**Possible readings:** (a) an enumeration (e.g. low / medium / high) declared
somewhere upstream, perhaps by the vendor-risk-cog; (b) a free string compared
to "high"; (c) an ordered scale with `high` a threshold on a numeric score.
**Adjudicated reading in use:** (a) — an enumeration {high, low, unknown}
(`RiskLevel` in model/vendor-fraud-review.sysml). Flagged as an
interpretation, and as a place where modeling could be enhanced with an
actual risk model in the future.

## GAP-02 — what a `then:` clause names

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
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
**Adjudicated reading in use:** decomposed, no hybrids. State, obligation
(a required action, abstract, not yet materialized), and concrete action are
distinct: state implies obligation (the GATE requirements); a concrete action
discharges the obligation and must also mutate state (the DISCHARGE-01
requirement in the model; vfr:Obligation / vfr:discharges / prov:generated in
the Track, enforced by shapes/track.shapes.ttl).

## GAP-03 — the provenance and granularity of `confidence`

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
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
**Adjudicated reading in use:** a confidence level enumeration {high, low,
unknown} alongside the raw scalar, bound at the manifest's 0.80 boundary
(`ConfidenceLevel` and INTERFACE-01 in model/vendor-fraud-review.sysml). The
simplified scheme serves as an interface contract with the guard that
produces it; likely requires its own confidence model eventually — noted for
future enrichment.

## GAP-04 — the semantics of `consensus_disagreement`

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md) — adjudicated OPEN
**Locus:** WP §5.6: `- if: consensus_disagreement > 0.25`; §5.5 Consensus row
("Three Cogs classify a document and two must agree; outlier extractions
flagged").
**Problem:** no definition of the disagreement metric is given anywhere in the
paper: not its range, not what it is computed over, not how "two of three must
agree" maps to a number comparable with 0.25.
**Substrate forces:** a typed quantity for the comparison to execute.
**Possible readings:** (a) fraction of dissenting Cogs; (b) 1 − pairwise
agreement rate; (c) a task-specific divergence score normalized to [0, 1].
**Adjudicated reading in use:** deliberately open, with the openness made
structural. The metric's TYPE is fixed (a fact-by-reader answer matrix,
answers in {agree, no, cantTell}, mapped to a scalar in [0, 1] against the
0.25 threshold — the abstract DisagreementMetric in the model), and three
type-satisfying alternatives with different semantics are exhibited
(dissent-fraction, strict-quorum-undecodable, erasure-aware-undecodable),
evaluated on the same answer matrix in the notebook, where they disagree
about whether the gate fires. No metric is chosen: a correctly constructed
policy is not the same as a fit-for-purpose policy, and what is right for
the job here is an open algorithmic policy design question — unlikely to
have a unique correct answer, with many viable answers carrying different
implications on incentives, and not limited to these three. The comparator
oracle's metric slot is typed and unbound; a deployment binds it, and the
Track records which metric a run used (recording is not endorsing).
**Earlier deferral note (2026-09-04):** revisit when the compared spaces are
known; if the comparison reduces to yes/no/cantTell facts, an
error-correcting-code style interpretation becomes available — that
reduction is now the type signature.

## GAP-05 — who provides the gate variables (oracle identity and citation)

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §5.6 gates block and §4.5 Op composition — the manifest names
the variables its gates read (`confidence`, `consensus_disagreement`,
`sensitive_data_detected`, `vendor_risk`) but never declares what service
provides each value, what was asked of it, or what came back. §5.3 lists
"input data and source references" among Track contents without binding them
to the gate variables.
**Problem:** a policy engine cannot act on a value it cannot source; the
thresholds are precise (0.80, 0.25 verbatim) but the values they test arrive
from nowhere.
**Substrate forces:** an identified provider and a citable exchange for every
value a gate evaluates.
**Possible readings:** (a) the values are ambient Op state, provenance out of
scope; (b) each in-flight Guard is implicitly the provider of "its" variable;
(c) every value is provided by an identified oracle, and the Track cites the
call: service, request payload, response code, response payload.
**Adjudicated reading in use:** (c) — `vfr:Oracle` / `vfr:OracleCall` /
`vfr:Reading` in the Track's interface graph; every Gate decision must cite
the reading it evaluated; shapes refuse unsourced readings and calls without
a response code (track/run-001.trig, shapes/track.shapes.ttl,
queries/interface.rq). Service identities are urn:example placeholders
pending real endpoints.

## GAP-06 — aggregate outcome: navigating the rules vs executing

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §5.6 gates block (`then: stop_and_escalate`) against §5.2:
"If a Privacy Guard detects sensitive information, the Op stops before
external transmission."; §4.5 defines an Op by the outcome it delivers.
**Problem:** the manifest's constraints can all hold on a run that stopped —
and equally on a run that stopped and transmitted anyway. Nothing in a flat
rendering distinguishes successfully navigating the rules with a no-op
aggregate from navigating the rules and executing.
**Substrate forces:** an explicit aggregate: what the composed Op actually
did, distinct from which rules held.
**Possible readings:** (a) out of scope, gates are advisory routing only;
(b) the aggregate is an output fact (emitted or not) constrained by the
gates; (c) the aggregate is a lifecycle terminal state (completed vs
stopped) with the output fact derived.
**Adjudicated reading in use:** (b)+(c) — `AggregateOutcome {executed, noOp}`
on the assembly, SYSTEM-02 (stop means no output, §5.2 verbatim), SYSTEM-03
(outcome coherence), and a lifecycle on the assembly (running → stopped |
completed) exercised under trace.

## GAP-07 — `track.include` lists `final_output` unconditionally

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §5.6 manifest, `track: include: - final_output`; §5.2 "the Op
stops before external transmission".
**Problem:** a stopped run has no final output to retain, yet the manifest's
retention list is unconditional. Either a stopped run's Track is permitted
to omit `final_output`, or the stop record itself counts as the final
output, or the manifest intends `include` as "include when produced".
**Substrate forces:** nothing yet — the committed Track (run-001) is an
executed run with an output, so the tension is latent. It binds the moment a
stopped run's Track is written.
**Possible readings:** (a) conditional inclusion (include when produced);
(b) the stop-and-escalation record is the final output of a stopped run;
(c) unconditional, so a stopped run's Track is non-conformant by design.
**Adjudicated reading in use:** (a) — conditional inclusion: an executed
run's Track must retain final_output; a noOp run's Track carries none.
**This is a judgment, and it departs from the pinned draft**, which lists
final_output unconditionally; the departure is acknowledged in the shape
messages themselves (shapes/track.shapes.ttl) and flagged for the author.

## GAP-08 — the Op's internal wiring topology

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §4.5 (an Op composes Cogs, Frames, a supervising model,
integration logic) and the §5.6 manifest (lists of frames, cogs, guards,
gates) — no dataflow between them is ever drawn.
**Problem:** assembling the Op as components wired along ports requires a
topology the paper does not state: which component feeds which, where the
guards sit on the flow, what reaches the output producer.
**Substrate forces:** drawn seams.
**Possible readings:** (a) a pipeline in the order the cogs are listed;
(b) a hub topology — a supervising engine mediates all flows; (c) guard
placement per lifecycle stage (§5.4) with gates inline on each seam.
**Adjudicated reading in use:** (b) — oracles → policy engine →
counterparty action / summary cog (model/vendor-fraud-review.sysml, the
seams in VendorFraudReviewOp; the component was renamed from "human
action" under GAP-09). **Claimed as this formalization's contribution**, not
a defect in the paper: an explicit, checkable topology is a benefit gained
by shifting from the textual to the computational representation of the
same concepts. The prose could not carry it; the model must, and does.

## GAP-09 — who performs the discharging actions

**Status:** ADJUDICATED (2026-09-04, see adjudication-log.md)
**Locus:** WP §5.6 gates (`human_review_required`,
`human_approval_required` name a human; `expert_review_required` and
`stop_and_escalate` do not) and §5.2 ("routes the output to human
review", "escalates to an expert", "stops before external transmission").
**Problem:** the assembly needs one component to hold the concrete
actions that discharge obligations, and its first name (HumanAction)
painted all four actions human. The manifest specifies a human for two
of the four; for expert review and the escalation target the actor is
unspecified.
**Substrate forces:** the discharging component must be typed and named;
the Track's discharging-action shape must say what mode and agent
evidence is required.
**Possible readings:** (a) all discharges human (over-reads the source);
(b) actor unspecified where the text is silent — modeled as another
system outside the modeled boundary acting on the Op, with a
counterparty assumed accountable for its behavior.
**Adjudicated reading in use:** (b). The component is CounterpartyAction;
the two manifest-named human attributes keep the manifest's words
(humanReviewPerformed, humanApprovalGiven); the discharging-action shape
requires a declared mode (manual or automatic) and a named accountable
party rather than requiring every discharge to be manual. The
accountable-counterparty assumption is explicitly the adjudicator's
interpretation, not the paper's.
