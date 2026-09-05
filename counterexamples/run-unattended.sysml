// GENERATED COUNTEREXAMPLE (checks/render_counterexamples.py): the
// committed policy text of model/vendor-fraud-review.sysml, byte-identical,
// plus three runs that must FAIL satisfy — this file is NOT the model.
package VendorFraudReview {
    doc /* The Vendor Fraud Review Op manifest (whitepaper section 5.6),
       rendered as an executable specification: abstract and concrete
       parts wired along ports into an assembly, with component-level
       checks (the gates), wiring-level checks (seam integrity), and
       system-level checks (obligations discharged across components;
       aggregate outcome). Every gate is the direct implication form of
       a manifest line quoted verbatim in its doc comment. Interpretive
       choices are recorded, with the adjudicator's rulings verbatim, in
       open-questions/adjudications.ttl; model/trace.ttl maps every
       named element here to its provenance. */

    package Manifest {

        // ------------------------------------------------------------
        // Enumerations and parameters
        // ------------------------------------------------------------

        enum def RiskLevel {
            doc /* adjudicated: GAP-01 — vendor_risk is an enumeration
               {high, low, unknown}. An interpretation, and a place where
               modeling could be enhanced with an actual risk model. */
            high;
            low;
            unknown;
        }

        enum def ConfidenceLevel {
            doc /* adjudicated: GAP-03 — confidence level as an enumeration,
               a simplified scheme serving as an interface contract with the
               guard that produces it; likely requires its own confidence
               model eventually. The numeric reading is retained as the raw
               value; INTERFACE-01 binds the two at the manifest's threshold
               boundary. */
            high;
            low;
            unknown;
        }

        enum def AggregateOutcome {
            doc /* adjudicated: GAP-06 — successfully navigating the rules
               with a no-op aggregate is different from navigating the
               rules and executing. An Op run either executed (its output
               was emitted) or was a deliberate no-op (stopped, nothing
               transmitted; WP section 5.2: "the Op stops before external
               transmission"). */
            executed;
            noOp;
        }

        enum def DenominatorBasis {
            doc /* adjudicated: GAP-11 — what a metric's value is a fraction
               OF. The three exhibited metrics do not share a denominator:
               dissent-fraction is a fraction of answers (facts x
               checkers); both undecodability metrics are fractions of
               facts. The manifest's single threshold therefore sits on
               different scales under different bindings. Each concrete
               metric declares its basis so the difference is a model
               fact, and a binding is calibrated to the policy's number,
               which stays where the manifest puts it (second external
               review, 2026-09-05). */
            facts;
            factsTimesCheckers;
        }

        enum def NullPolicy {
            doc /* adjudicated: GAP-04 (class split, 2026-09-05) — how a
               metric treats a null (cannot tell) answer: punitive counts
               it as dissent; quorumBlocking lets it block a quorum;
               erasure drops it before deciding. */
            punitive;
            quorumBlocking;
            erasure;
        }

        part def ValidationStrategyParameters {
            doc /* The numerical parameters of the policy, factored out as
               single-point definitions the gates reference — what an
               implementation can do that a whitepaper cannot. The defaults
               are the manifest's literals, verbatim; changing a threshold
               is a change HERE, nowhere else, and the Track records the
               values in force per run (WP section 5.3: Track contents
               include "the model versions and configuration parameters"). */
            attribute confidenceThreshold : ScalarValues::Real = 0.80;
            attribute consensusDisagreementThreshold : ScalarValues::Real = 0.25;
            attribute vendorRiskTrigger : RiskLevel = RiskLevel::high;
        }

        // ------------------------------------------------------------
        // Payloads and ports
        // ------------------------------------------------------------

        item def Reading;
        item def Obligation;
        item def Clearance;
        item def Summary;
        item def Escalation;
        item def Proceed;

        port def ReadingWrite { out item r : Reading; }
        port def ObligationWrite { out item o : Obligation; }
        port def ClearanceWrite { out item c : Clearance; }
        port def SummaryWrite { out item s : Summary; }
        port def StopIn { in item e : Escalation; }
        port def ProceedIn { in item p : Proceed; }

        // ------------------------------------------------------------
        // Components: abstract defs carry attributes; ports on concretes
        // ------------------------------------------------------------

        abstract part def OpComponent {
            attribute componentName : ScalarValues::String;
        }

        abstract part def OracleService :> OpComponent {
            doc /* adjudicated: GAP-05 — every value the policy reads is
               provided by an identified oracle. An oracle is a process
               that answers a question: a service the Op queries for a
               value it does not compute itself, with each exchange cited
               (service, payload, response code, response). The term is
               the adjudicator's, from the GAP-05 ruling; the paper does
               not use it. The components below hold what their service
               returned; the policy engine rules on it; WIRE-01..04 check
               the two agree across the seam. */
            attribute service : ScalarValues::String;
        }

        part def ExtractionConfidenceOracle :> OracleService {
            attribute returnedConfidence : ScalarValues::Real;
            port reading : ReadingWrite;
        }

        abstract part def ConsensusInadequacyMetric {
            doc /* adjudicated: GAP-04 — the rule does not say what the
               number is, and no metric is chosen HERE. This abstract def
               is the type signature: a metric maps a fact-by-checker
               answer matrix of nullable Booleans to a scalar in [0, 1]
               comparable against the manifest's 0.25 threshold; the
               codomain is a checked constraint (TYPE-01), not only this
               sentence. Each answer is one checker's reply, given the
               datum as context and irrespective of which Cog produced it,
               to the question "do you agree with the datum?": True =
               agree, False = disagree, null = cannot tell (the outcome
               the Track records as earl:cantTell). Checkers are factored
               apart from generators: the Cog that produced a datum may
               itself answer False when asked whether it stands; no
               producer is assumed to file True, and a Cog's answer about
               its own datum is one column like any other (GAP-04
               clarifications, 2026-09-04 and 2026-09-05). The matrix is
               rectangular: every fact has one answer per checker, and an
               absent checker is not a null answer; a run with zero facts
               scores 0. The class splits along one axiom (GAP-04 class
               split, 2026-09-05): a DisagreementMetric is monotone in
               dissent and saturates at unanimous dissent; an
               UndecodabilityMetric measures whether a fact resolves and
               is neither. Each concrete metric declares its properties
               as attributes, and the test suite proves them by exhaustive
               enumeration. Three type-satisfying alternatives with
               different semantics follow; which is fit for purpose is an
               open algorithmic policy design question, unlikely to have a
               unique correct answer, with different implications on
               incentives. The right answer is not limited to these
               three. */
            attribute metricName : ScalarValues::String;
            attribute denominator : DenominatorBasis;
            attribute nullPolicy : NullPolicy;
            attribute monotoneInDissent : ScalarValues::Boolean;
            attribute saturatesAtUnanimousDissent : ScalarValues::Boolean;
            attribute ensembleSizeInvariant : ScalarValues::Boolean;
        }

        abstract part def DisagreementMetric :> ConsensusInadequacyMetric {
            doc /* Measures HOW MUCH dissent a run carries. Axioms: flipping
               one answer from agree to disagree cannot decrease the
               value; unanimous disagreement scores 1. */
            attribute :>> monotoneInDissent = true;
            attribute :>> saturatesAtUnanimousDissent = true;
        }

        abstract part def UndecodabilityMetric :> ConsensusInadequacyMetric {
            doc /* Measures WHETHER facts resolve, not how much dissent they
               carry. Not monotone in dissent: unanimous disagreement
               decodes and scores 0. Its name says undecodable; it feeds
               the manifest's consensus_disagreement variable all the
               same, which is the point of exhibiting it in the same
               slot. */
            attribute :>> monotoneInDissent = false;
            attribute :>> saturatesAtUnanimousDissent = false;
        }

        part def DissentFractionMetric :> DisagreementMetric {
            doc /* Fraction of answers that are not True: disagreement and
               null (cannot tell) both count as dissent. Incentive
               implication: honest abstention is punished, so checkers are
               pushed to affirm rather than say cannot tell. Note: on the
               paper's own section 5.5 example (three Cogs, two must
               agree) this metric FIRES the gate at the 0.25 threshold,
               contradicting the example's intent. */
            attribute :>> denominator = DenominatorBasis::factsTimesCheckers;
            attribute :>> nullPolicy = NullPolicy::punitive;
            attribute :>> ensembleSizeInvariant = true;
        }

        part def StrictQuorumUndecodableMetric :> UndecodabilityMetric {
            doc /* Fraction of facts where no answer value reaches a quorum
               of two identical non-null answers; null blocks quorum. The
               quorum is the absolute two of the paper's section 5.5
               example (three Cogs, two must agree), deliberately (ruling,
               2026-09-05): the metric is admissible for a three-checker
               ensemble only. It is not ensemble-size invariant: with one
               checker, unanimous agreement scores 1; with nine, two
               agreements outvote seven dissents. Incentive implication:
               abstention is conservative: it escalates more runs to
               expert review, spending review capacity. Consistent with
               the section 5.5 example because, on three checkers with no
               abstention, it is identically zero: the gate cannot fire
               under it unless a checker abstains. */
            attribute :>> denominator = DenominatorBasis::facts;
            attribute :>> nullPolicy = NullPolicy::quorumBlocking;
            attribute :>> ensembleSizeInvariant = false;
        }

        part def ErasureAwareUndecodableMetric :> UndecodabilityMetric {
            doc /* Fraction of facts undecodable among non-null answers
               only: null (cannot tell) is an erasure, not an error, so a
               lone expressed voice among abstentions decodes. Incentive
               implication: abstention shifts power to whoever still
               answers. Consistent with the section 5.5 example for the
               same reason as the strict quorum: identically zero on three
               checkers without abstention. */
            attribute :>> denominator = DenominatorBasis::facts;
            attribute :>> nullPolicy = NullPolicy::erasure;
            attribute :>> ensembleSizeInvariant = true;
        }

        part def ConsensusComparatorOracle :> OracleService {
            doc /* adjudicated: GAP-04 — the metric slot below is typed by
               the abstract ConsensusInadequacyMetric and deliberately left
               unbound: the model states that a metric of this type is
               required and refuses to choose one. A deployment binds it,
               choosing a branch (disagreement or undecodability) as a
               visible policy decision; the Track records which one a run
               used, and the matrix it ran on (GAP-12). */
            part metric : ConsensusInadequacyMetric;
            attribute returnedDisagreement : ScalarValues::Real;
            port reading : ReadingWrite;
        }

        part def SensitiveDataScannerOracle :> OracleService {
            attribute returnedDetected : ScalarValues::Boolean;
            port reading : ReadingWrite;
        }

        part def VendorRiskOracle :> OracleService {
            attribute returnedRisk : RiskLevel;
            port reading : ReadingWrite;
        }

        part def PolicyEngine :> OpComponent {
            doc /* Applies the section 5.6 gates to the oracle-provided
               readings. It consumes values; it never produces them. */
            part policy : ValidationStrategyParameters;

            attribute confidence : ScalarValues::Real;
            attribute confidenceLevel : ConfidenceLevel;
            attribute consensusDisagreement : ScalarValues::Real;
            attribute sensitiveDataDetected : ScalarValues::Boolean;
            attribute vendorRisk : RiskLevel;

            /* Obligations raised (adjudicated: GAP-02 — a then-clause names
               an obligation: a required action, abstract, not yet
               materialized). */
            attribute humanReviewRequired : ScalarValues::Boolean;
            attribute expertReviewRequired : ScalarValues::Boolean;
            attribute stopAndEscalate : ScalarValues::Boolean;
            attribute humanApprovalRequired : ScalarValues::Boolean;

            port fromConfidence : ~ReadingWrite;
            port fromConsensus : ~ReadingWrite;
            port fromScanner : ~ReadingWrite;
            port fromRisk : ~ReadingWrite;
            port toCounterparty : ObligationWrite;
            port toCog : ClearanceWrite;
        }

        part def CounterpartyAction :> OpComponent {
            doc /* The concrete actions that discharge obligations
               (adjudicated: GAP-02 — a concrete action discharges an
               obligation and must also mutate state; the Track evidences
               both). Who acts: three of the four actions are paper-named
               human — review and approval by the section 5.6 manifest
               tokens, expert review by the section 5.1/5.5 prose ("routes
               sampled or high-risk outputs to human review"; "Human or
               known-expert judgment"). Attribute names keep the
               manifest's words. Only the escalation target is
               unspecified: there the actor is another system outside the
               modeled boundary, acting on the Op, with a counterparty
               assumed accountable for its behavior (adjudicated: GAP-09,
               extended 2026-09-04). */
            attribute humanReviewPerformed : ScalarValues::Boolean;
            attribute expertReviewPerformed : ScalarValues::Boolean;
            attribute escalationPerformed : ScalarValues::Boolean;
            attribute humanApprovalGiven : ScalarValues::Boolean;
            port fromEngine : ~ObligationWrite;
        }

        part def AnomalySummaryCog :> OpComponent {
            doc /* The Op's output producer (the anomaly-summary-cog of the
               section 5.6 manifest). Whether its output was emitted is the
               aggregate fact SYSTEM-02/03 rule on. */
            attribute outputEmitted : ScalarValues::Boolean;
            port clearance : ~ClearanceWrite;
            port summary : SummaryWrite;
        }

        // ------------------------------------------------------------
        // Seams
        // ------------------------------------------------------------

        interface def ReadingSeam {
            doc /* An oracle's returned value crosses to the policy engine.
               adjudicated: GAP-08 — the paper draws no internal wiring;
               this explicit, checkable topology is the formalization's
               contribution, gained by shifting from the textual to the
               computational representation. */
            end supplier : ReadingWrite;
            end consumer : ~ReadingWrite;
        }
        interface def ObligationSeam {
            doc /* Raised obligations cross to the counterparty that
               discharges them: human where the manifest says so,
               otherwise unspecified (adjudicated: GAP-09). */
            end supplier : ObligationWrite;
            end consumer : ~ObligationWrite;
        }
        interface def ClearanceSeam {
            doc /* The engine's clearance crosses to the output producer. */
            end supplier : ClearanceWrite;
            end consumer : ~ClearanceWrite;
        }

        // ------------------------------------------------------------
        // The assembly
        // ------------------------------------------------------------

        part def VendorFraudReviewOp {
            doc /* op: name: vendor-fraud-review
               frames: company-policy, procurement-rules, fraud-detection-methodology
               cogs: invoice-extraction-cog, vendor-risk-cog, anomaly-summary-cog
               Source: WP section 5.6, manifest sketch.
               The Op as an assembly: four oracle components feed the policy
               engine; obligations flow to the counterparty actions;
               clearance flows to the summary cog; the boundary exposes
               the result.
               Interface usages are declared before the parts they connect
               (executor materializes in declaration order). */

            interface confidenceSeam : ReadingSeam connect confidenceOracle.reading to policyEngine.fromConfidence;
            interface consensusSeam : ReadingSeam connect consensusOracle.reading to policyEngine.fromConsensus;
            interface scannerSeam : ReadingSeam connect scannerOracle.reading to policyEngine.fromScanner;
            interface riskSeam : ReadingSeam connect riskOracle.reading to policyEngine.fromRisk;
            interface obligationSeam : ObligationSeam connect policyEngine.toCounterparty to counterparty.fromEngine;
            interface clearanceSeam : ClearanceSeam connect policyEngine.toCog to summaryCog.clearance;

            part confidenceOracle : ExtractionConfidenceOracle;
            part consensusOracle : ConsensusComparatorOracle;
            part scannerOracle : SensitiveDataScannerOracle;
            part riskOracle : VendorRiskOracle;
            part policyEngine : PolicyEngine;
            part counterparty : CounterpartyAction;
            part summaryCog : AnomalySummaryCog;

            port result : SummaryWrite;
            bind result = summaryCog.summary;

            port stopSignal : StopIn;
            port proceedSignal : ProceedIn;

            attribute aggregateOutcome : AggregateOutcome;

            exhibit state run {
                doc /* Lifecycle on the assembly itself (v0.4.3: binds do
                   not relay messages; work-around per the pinned-toolchain
                   idiom list). A run either completes or stops — WP
                   section 5.2: "the Op stops before external
                   transmission". */
                entry; then running;
                state running;
                state stopped;
                state completed;
                transition halt first running accept e : Escalation via stopSignal then stopped;
                transition finish first running accept p : Proceed via proceedSignal then completed;
            }
        }

        // ------------------------------------------------------------
        // Component-level checks: the manifest's gates
        // ------------------------------------------------------------

        requirement def <'INTERFACE-01'> ConfidenceInterface {
            doc /* adjudicated: GAP-03 — the documented threshold rule
               binding the oracle-provided numeric to its category.
               Categories are the preferred interface; numerical precision
               lives inside the oracles or in rules like this one. */
            subject pe : PolicyEngine;
            require constraint { pe.confidence < pe.policy.confidenceThreshold implies pe.confidenceLevel == ConfidenceLevel::low }
            require constraint { pe.confidence >= pe.policy.confidenceThreshold implies pe.confidenceLevel == ConfidenceLevel::high }
        }

        requirement def <'TYPE-01'> DisagreementReadingInRange {
            doc /* The metric class's doc states a codomain of [0, 1]; stated
               here as a constraint so it is checked, not promised: a
               binding returning 1.4 fails the run. The reading is
               oracle-provided (GAP-05), so the check sits on the value the
               engine rules on (second external review, 2026-09-05). */
            subject pe : PolicyEngine;
            require constraint { pe.consensusDisagreement >= 0.0 }
            require constraint { pe.consensusDisagreement <= 1.0 }
        }

        requirement def <'GATE-01'> ConfidenceGate {
            doc /* - if: confidence < 0.80
                    then: human_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject pe : PolicyEngine;
            require constraint { pe.confidence < pe.policy.confidenceThreshold implies pe.humanReviewRequired }
        }

        requirement def <'GATE-02'> ConsensusGate {
            doc /* - if: consensus_disagreement > 0.25
                    then: expert_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject pe : PolicyEngine;
            require constraint { pe.consensusDisagreement > pe.policy.consensusDisagreementThreshold implies pe.expertReviewRequired }
        }

        requirement def <'GATE-03'> SensitiveDataGate {
            doc /* - if: sensitive_data_detected
                    then: stop_and_escalate
               Source: WP section 5.6 gates block, verbatim. */
            subject pe : PolicyEngine;
            require constraint { pe.sensitiveDataDetected implies pe.stopAndEscalate }
        }

        requirement def <'GATE-04'> VendorRiskGate {
            doc /* - if: vendor_risk == high
                    then: human_approval_required
               Source: WP section 5.6 gates block, verbatim.
               adjudicated: GAP-01 — high is RiskLevel::high. */
            subject pe : PolicyEngine;
            require constraint { pe.vendorRisk == pe.policy.vendorRiskTrigger implies pe.humanApprovalRequired }
        }

        // ------------------------------------------------------------
        // Wiring-level checks: seam integrity (value form). The
        // structural form lives in tests/test_wiring.py over the RDF
        // conversion, because -validate -strict accepts a mismatched
        // connect (probed 2026-09-04).
        // ------------------------------------------------------------

        requirement def <'WIRE-01'> ConfidenceSeamIntegrity {
            doc /* The value the engine ruled on is the value the oracle
               returned — nothing altered a reading in transit. */
            subject op : VendorFraudReviewOp;
            require constraint { op.confidenceOracle.returnedConfidence == op.policyEngine.confidence }
        }

        requirement def <'WIRE-02'> ConsensusSeamIntegrity {
            subject op : VendorFraudReviewOp;
            require constraint { op.consensusOracle.returnedDisagreement == op.policyEngine.consensusDisagreement }
        }

        requirement def <'WIRE-03'> ScannerSeamIntegrity {
            subject op : VendorFraudReviewOp;
            require constraint { op.scannerOracle.returnedDetected == op.policyEngine.sensitiveDataDetected }
        }

        requirement def <'WIRE-04'> RiskSeamIntegrity {
            subject op : VendorFraudReviewOp;
            require constraint { op.riskOracle.returnedRisk == op.policyEngine.vendorRisk }
        }

        // ------------------------------------------------------------
        // System-level checks: properties of the composed Op
        // ------------------------------------------------------------

        requirement def <'SYSTEM-01'> ObligationsDischarged {
            doc /* adjudicated: GAP-02 — a closed run must show every raised
               obligation discharged by a concrete action; genuinely a
               system property: raised in the policy engine, discharged in
               the counterparty actions (adjudicated: GAP-09 on who may
               act). */
            subject op : VendorFraudReviewOp;
            require constraint { op.policyEngine.humanReviewRequired implies op.counterparty.humanReviewPerformed }
            require constraint { op.policyEngine.expertReviewRequired implies op.counterparty.expertReviewPerformed }
            require constraint { op.policyEngine.stopAndEscalate implies op.counterparty.escalationPerformed }
            require constraint { op.policyEngine.humanApprovalRequired implies op.counterparty.humanApprovalGiven }
        }

        requirement def <'SYSTEM-02'> StopMeansNoOutput {
            doc /* WP section 5.2, verbatim: "If a Privacy Guard detects
               sensitive information, the Op stops before external
               transmission." A stopped Op emits nothing — navigating the
               rules and then executing anyway is a violation.
               adjudicated: GAP-06. */
            subject op : VendorFraudReviewOp;
            require constraint { op.policyEngine.stopAndEscalate implies not op.summaryCog.outputEmitted }
        }

        requirement def <'SYSTEM-03'> OutcomeCoherence {
            doc /* adjudicated: GAP-06 — the aggregate outcome names what
               actually happened: executed means the output was emitted;
               noOp means it was not; a stop forces noOp. */
            subject op : VendorFraudReviewOp;
            require constraint { op.aggregateOutcome == AggregateOutcome::executed implies op.summaryCog.outputEmitted }
            require constraint { op.aggregateOutcome == AggregateOutcome::noOp implies not op.summaryCog.outputEmitted }
            require constraint { op.policyEngine.stopAndEscalate implies op.aggregateOutcome == AggregateOutcome::noOp }
        }
    }

    package RunConfigurations {
        doc /* Four runs that must FAIL satisfy (exit 1), one per check
           level, against the committed model itself: unattendedRun — the
           gate condition holds but no obligation was raised (component
           level); undischargedRun — the obligation was raised and no
           concrete action discharged it (system level, GAP-02);
           emittedRun — the Op stopped and emitted output anyway
           (aggregate level, GAP-06); outOfRangeRun — the consensus
           oracle returned 1.4, outside the metric class's declared
           codomain (type level, TYPE-01). This file is GENERATED by
           checks/render_counterexamples.py: the policy text between the
           banner and this package is the committed model's,
           byte-identical. */

        part def UnattendedRun :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.71; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 0.10; }
            part :>> scannerOracle { attribute :>> returnedDetected = false; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::low; }
            part :>> policyEngine {
                attribute :>> confidence = 0.71;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::low;
                attribute :>> consensusDisagreement = 0.10;
                attribute :>> sensitiveDataDetected = false;
                attribute :>> vendorRisk = Manifest::RiskLevel::low;
                attribute :>> humanReviewRequired = false;
                attribute :>> expertReviewRequired = false;
                attribute :>> stopAndEscalate = false;
                attribute :>> humanApprovalRequired = false;
            }
            part :>> counterparty {
                attribute :>> humanReviewPerformed = false;
                attribute :>> expertReviewPerformed = false;
                attribute :>> escalationPerformed = false;
                attribute :>> humanApprovalGiven = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }
        part unattendedRun : UnattendedRun;
        requirement unattendedGate01 : Manifest::ConfidenceGate { subject pe = unattendedRun.policyEngine; }

        part def UndischargedRun :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.71; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 0.10; }
            part :>> scannerOracle { attribute :>> returnedDetected = false; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::low; }
            part :>> policyEngine {
                attribute :>> confidence = 0.71;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::low;
                attribute :>> consensusDisagreement = 0.10;
                attribute :>> sensitiveDataDetected = false;
                attribute :>> vendorRisk = Manifest::RiskLevel::low;
                attribute :>> humanReviewRequired = true;
                attribute :>> expertReviewRequired = false;
                attribute :>> stopAndEscalate = false;
                attribute :>> humanApprovalRequired = false;
            }
            part :>> counterparty {
                attribute :>> humanReviewPerformed = false;
                attribute :>> expertReviewPerformed = false;
                attribute :>> escalationPerformed = false;
                attribute :>> humanApprovalGiven = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }
        part undischargedRun : UndischargedRun;
        requirement undischargedSystem01 : Manifest::ObligationsDischarged { subject op = undischargedRun; }

        part def EmittedRun :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.92; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 0.10; }
            part :>> scannerOracle { attribute :>> returnedDetected = true; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::low; }
            part :>> policyEngine {
                attribute :>> confidence = 0.92;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::high;
                attribute :>> consensusDisagreement = 0.10;
                attribute :>> sensitiveDataDetected = true;
                attribute :>> vendorRisk = Manifest::RiskLevel::low;
                attribute :>> humanReviewRequired = false;
                attribute :>> expertReviewRequired = false;
                attribute :>> stopAndEscalate = true;
                attribute :>> humanApprovalRequired = false;
            }
            part :>> counterparty {
                attribute :>> humanReviewPerformed = false;
                attribute :>> expertReviewPerformed = false;
                attribute :>> escalationPerformed = true;
                attribute :>> humanApprovalGiven = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }
        part emittedRun : EmittedRun;
        requirement emittedSystem02 : Manifest::StopMeansNoOutput { subject op = emittedRun; }

        part def OutOfRangeRun :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.92; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 1.4; }
            part :>> scannerOracle { attribute :>> returnedDetected = false; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::low; }
            part :>> policyEngine {
                attribute :>> confidence = 0.92;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::high;
                attribute :>> consensusDisagreement = 1.4;
                attribute :>> sensitiveDataDetected = false;
                attribute :>> vendorRisk = Manifest::RiskLevel::low;
                attribute :>> humanReviewRequired = false;
                attribute :>> expertReviewRequired = true;
                attribute :>> stopAndEscalate = false;
                attribute :>> humanApprovalRequired = false;
            }
            part :>> counterparty {
                attribute :>> humanReviewPerformed = false;
                attribute :>> expertReviewPerformed = true;
                attribute :>> escalationPerformed = false;
                attribute :>> humanApprovalGiven = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }
        part outOfRangeRun : OutOfRangeRun;
        requirement outOfRangeType01 : Manifest::DisagreementReadingInRange { subject pe = outOfRangeRun.policyEngine; }

        verification def CounterexampleCase {
            objective {
                verify unattendedGate01;
                verify undischargedSystem01;
                verify emittedSystem02;
                verify outOfRangeType01;
            }
        }
        verification counterexampleCase : CounterexampleCase;
    }
}
