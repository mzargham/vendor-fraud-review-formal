# Adjudication log

Rulings on entries in `computability-gaps.md`. Each ruling records: the gap id,
the date, the ruling (the adjudicator's words, verbatim), and what changed in
the substrate as a result. Until a gap id appears here, its provisional reading
remains provisional. Adjudicator: Z.

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
Model: GATE requirements raise obligations from state; a new DISCHARGE-01
requirement demands every raised obligation be discharged; discharge
attributes added; the counterexample now exhibits both failure kinds (gate
fired with no obligation raised; obligation raised with no discharge). Track:
`vfr:Obligation` nodes raised by gate decisions; the human approval
`vfr:discharges` them and `prov:generated` the post-review case state.
Shapes: obligations must be discharged; a discharging action must be
earl:manual, named, rationaled, and must record the state it generated.
Queries: governance reports undischarged obligations; auditability traverses
gate → obligation → discharging action.

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

**Changed:** nothing in the substrate; the entry remains PENDING with the
ruling's direction recorded as an adjudication note.
