# Adjudication log

<!-- GENERATED from adjudications.ttl by checks/render_log.py. Do not edit
     by hand: this page is a view of the judgment record, and the checks
     refuse a page that drifts from it. -->

Rulings and design notes, in the order they were made. Each entry records
the date, the adjudicator's words verbatim, and what changed in the
substrate as a result. The machine-readable record (gap, ruling, named
adjudicator, derived implementations) is adjudications.ttl.


## 2026-09-04 — GAP-01

**Ruling (verbatim):** "convert it to an enum with high, low and unknown. and
flag it as an interpretation and a place where modeling could be enhanced with
an actual risk model in the future."

**Changed:** `vendorRisk` retyped from String to `enum def RiskLevel {high,
low, unknown}`; GATE-04 compares against `RiskLevel::high`; the enum's doc
comment flags the interpretation and the future risk-model enhancement point
(model/vendor-fraud-review.sysml).

## 2026-09-04 — GAP-02

**Ruling (verbatim):** "needs to be decomposed. we don't want hybrids, state,
obligation (is a required action that is abstract, not yet materialized)
whereas a concrete action can discharge an obligation; these are distinct
concepts. if state x implies obligation, then the action which discharges that
obligation must also mutate state."

**Changed:** the hybrid reading was replaced by a three-way decomposition.
Model: GATE requirements raise obligations from state; a requirement (now
SYSTEM-01) demands every raised obligation be discharged; discharge attributes
added; the counterexample exhibits both failure kinds (gate fired with no
obligation raised; obligation raised with no discharge). Track:
`vfr:Obligation` nodes raised by gate decisions; the approval `vfr:discharges`
them and `prov:generated` the post-review case state. Shapes: obligations must
be discharged; a discharging action must be named, rationaled, and must record
the state it generated. Queries: governance reports undischarged obligations;
auditability traverses gate to obligation to discharging action.

## 2026-09-04 — GAP-03

**Ruling (verbatim):** "confidence level treated with enum similar to risk.
likely requires its own confidence model eventually but here can serve as an
interface contract with a simplified scheme. notes on future enrichment"

**Changed:** `enum def ConfidenceLevel {high, low, unknown}` added alongside
the raw scalar; INTERFACE-01 binds the two at the manifest's 0.80 boundary as
the interface contract; doc comments carry the future-enrichment note
(model/vendor-fraud-review.sysml).

## 2026-09-04 — GAP-04 (deferral)

**Ruling (verbatim):** "we need to come back to this when we have a better
sense of what the spaces are being compared. is this bit-exact comparison,
semantic distance or some other metrics. if we can get this tighter we can
treat it as error correcting code style interpretation. this requires we can
reduce to yes/no/canttell facts we're agreeing or disagreeing on"

**Changed:** nothing in the substrate; the entry remained open with the
ruling's direction recorded as an adjudication note.

## 2026-09-04 — GAP-05

**Ruling (verbatim):** "where ever we need a number we must assume an oracle
that can provide it and have an identity for that oracle, and be able to
precisely cite it. that means we need to know what service we called what
payload we sent, what response code we got and what response we got. our
system needs these answers to apply its policies but is not itself the
provider of these numbers. so these make up interface contract."

**Changed:** the Track gained an interface graph: four identified oracle
services, one cited call per gate variable (request payload, response code,
response payload), and a reading node per value. Gate decisions now cite the
reading they evaluated. Shapes refuse unsourced readings, calls missing any of
the four citation fields, and gate decisions with no cited reading. A new
interface query renders the full citation table; a new counterexample proves
the shapes bite.

## 2026-09-04 — design note: categories over numerical ranges

**Note (verbatim):** "the suggestion that this system prefer categories over
numerical ranges as their interface contract and let the numerical precision
live inside the oracles or within well documented threshold rules."

**Changed:** the raw numerics remain exactly as the manifest states them
(GATE-01 and GATE-02 evaluate the literal 0.80 and 0.25 comparisons); the
category layer (RiskLevel, ConfidenceLevel) is the preferred interface;
INTERFACE-01 is the documented threshold rule mapping number to category; the
numbers themselves are oracle-provided (GAP-05). This note is a suggestion
about the system's design, available to raise with the author; it changes no
verbatim rendering of the source text.

## 2026-09-04 — design note: parameters factored

**Note (verbatim):** "numerical parameters in policies need to be factored out
as parameters. this is part of what the implementation can do easily that a
whitepaper cannot."

**Changed:** the thresholds became single-point definitions
(ValidationStrategyParameters: confidenceThreshold = 0.80,
consensusDisagreementThreshold = 0.25, vendorRiskTrigger = high) that GATE-01,
GATE-02, GATE-04, and INTERFACE-01 reference; outside verbatim doc quotes each
literal appears exactly once, enforced by test. The Track records the
parameter values in force per run — section 5.3's "the model versions and
configuration parameters" made executable — and an execution that omits them
fails the shapes.

## 2026-09-04 — GAP-06, and the assembly directive

**Ruling (verbatim):** "this reveals that we need to account for aggregate
outputs. we successfully navigated the rules but the aggregate is no-op. which
is different than successfully navigating the rules and executing. my
intuition is that we've severely underutilitized the opensysml tool for its
ability to define abstract and concrete parts, then wire them together along
ports. this is what allows us to assemble complex workflows with both
component level checks, wiring level checks, and system level checks with one
toolchain"

**Changed:** the Op became an assembly of abstract/concrete parts wired along
ports (oracles, policy engine, counterparty action, summary cog), with checks
at three levels in one toolchain: the verbatim gates at component level; seam
integrity at wiring level (WIRE-01..04 in satisfy, structural conformance in
code over the conversion — validate accepts a mismatched connect, probed);
obligations-discharged, stop-means-no-output (section 5.2 verbatim), and
aggregate-outcome coherence at system level. AggregateOutcome {executed, noOp}
names the distinction; the assembly's lifecycle (running to stopped or
completed) runs under trace. GAP-07 and GAP-08 were logged open by the same
review.

## 2026-09-04 — GAP-07

**Ruling (verbatim):** "we need it to be conditional but we should flag that
we've made that judgement and acknowledge it departs from pinned draft"

**Changed:** final_output retention is now conditional on the aggregate
outcome: an executed run's Track must retain it; a noOp run's Track must not
carry one. Encoded as SPARQL constraints in shapes/track.shapes.ttl, whose
violation messages acknowledge the departure from the pinned draft in so many
words; the Track states its aggregate outcome as a required field; run-001
records "executed". Inline negative cases prove both directions bite.

## 2026-09-04 — GAP-08

**Ruling (verbatim):** "we claim this is our contribution, and as a benefit we
get for shifting to the computational rather than textual representation of
the same concepts"

**Changed:** the drawn topology (oracles, policy engine, counterparty action,
summary cog) is no longer provisional: it is claimed as the formalization's
contribution. The gap entry and the seam doc comment frame it as a capability
the computational representation adds — an explicit topology the wiring rules
can check — rather than an under-specification to be repaired in the source
text.

## 2026-09-04 — GAP-04 (resolution)

**Ruling (verbatim):** "given we don't want to push policy decisions. i think
this is an excellent place to show breadth. Travis' rule doesn't say what the
numer is so we can provide a type signature and three alternatives which are
all type satisfying but have different semantics. then we can highlight that
correctly constructed policies are not the same as fit for purpose polices and
that what is 'right for the job' is an open question here. and the right
answer is not limited to these 3 options. its an open algorithmic policy
design question, which is likely to have no unique correct answer but rather
many viable answers with different implications on incentives"

**Changed:** the metric's type became a first-class abstract definition
(DisagreementMetric) with three concrete type-satisfying specializations
(dissent-fraction, strict-quorum-undecodable, erasure-aware-undecodable), each
doc-commented with its semantics and incentive implication; the comparator
oracle's metric slot is typed by the abstract def and deliberately unbound.
The walkthrough evaluates all three on one answer matrix and shows the gate
firing under some and not others — the same correctly-typed policy
construction, different behavior. The Track records which metric a run used.
Nothing anywhere selects a winner.

## 2026-09-04 — GAP-09

**Ruling (verbatim):** "i am not sure we can say 'cross to the human actions'
as actions may be performed by other automated systems. i do personally assume
all automated systems have a party accountable for their behavior but not that
any particular actor is human. do not contradict Travis' text but if its left
unspecified do not inject the expectation of human action, instead assume its
an other system outside the bounds of what is modeled acting on the system
that is modeled, and we can assume there is a counterparty accountable for
those actions. if necessary you can add my interpretation as explicitly mine
and log it with adjudications."

**Changed:** part def HumanAction renamed CounterpartyAction (usage
humanAction to counterparty, port toHuman to toCounterparty) in the model, the
counterexamples, and the scenario template; its doc states which actions the
source names human and that the escalation actor is unspecified. The
obligation-seam doc and SYSTEM-01 doc updated. The Track's discharging-action
shape no longer requires earl:manual on every discharge: it requires a
declared mode and a named accountable party (prov:wasAssociatedWith), with the
accountable-counterparty assumption marked as the adjudicator's own
interpretation. Walkthrough narration reworded to match.

## 2026-09-04 — GAP-04 (type clarified)

**Ruling (verbatim):** "'{agree, no, cantTell}' -> '{True, False, Null}' but
further clarified as {agree, diagree, cannot tell} basically we want the base
data type to be nullable Bool for better type checking support but the
semantics are given a datum as context (irrespective of which Cog produced it)
there is a check bool check that can bet True, False or null which is the
answer do you agree with the datum. optionally we can assume the cog which
produced the datum in question files True but in my experience its best to
factor checkers apart from generators so its strictly possible for a cog to
produce a datum and still return false when asked if that data is true. this
clarification is going to need an adjudication record"

**Changed:** the DisagreementMetric type's answer domain moved from the label
set {agree, no, cantTell} to a nullable Boolean: each entry is one checker's
reply, given the datum as context, to "do you agree with the datum?" (True /
False / null = cannot tell, corresponding to the Track's earl:cantTell). The
abstract def's doc, the three concrete metric docs, the Python
implementations, the example answer matrix, and the chapter narration all
reworded; the metric values on the example matrix are unchanged, preserving
the one-fires-one-stays-quiet demonstration. Checkers are factored apart from
generators in both the model doc and the narration: no producer is assumed to
file True about its own datum. The openness of the metric CHOICE is untouched;
only its type got sharper.

## 2026-09-04 — GAP-09 (extension)

**Ruling (verbatim):** "Extend the ruling (selected review option, holistic
audit of 2026-09-04): treat expert review as paper-named human alongside
review and approval, per section 5.1 ("routes sampled or high-risk outputs to
human review") and section 5.5 ("Human or known-expert judgment"); only the
escalation target remains counterparty-neutral."

**Changed:** the four sites claiming "the paper leaves the actor unspecified"
for expert review were corrected: the CounterpartyAction doc now states three
of the four actions are paper-named human and only the escalation target is
unspecified; the discharging-action shape messages, the GAP-09 record fields,
and the chapter narration follow. Attribute names keep the manifest's tokens
(no rename: the manifest word is expert_review_required). governance.rq caught
up with the earlier GAP-09 ruling in the same pass, requiring a named
accountable party instead of earl:manual.
