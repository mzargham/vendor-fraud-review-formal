package VendorFraudReview {
    doc /* The Vendor Fraud Review Op manifest (whitepaper section 5.6),
       rendered as an executable specification: abstract and concrete
       parts wired along ports into an assembly, with component-level
       checks (the gates), wiring-level checks (seam integrity), and
       system-level checks (obligations discharged across components;
       aggregate outcome). Every gate is the direct implication form of
       a manifest line quoted verbatim in its doc comment. Interpretive
       choices are logged in open-questions/computability-gaps.md;
       adjudicated entries carry the ruling recorded in
       open-questions/adjudication-log.md. */

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
               provided by an identified oracle; the Track cites each call
               (service, payload, response code, response). The components
               below hold what their service returned; the policy engine
               rules on it; WIRE-01..04 check the two agree across the
               seam. */
            attribute service : ScalarValues::String;
        }

        part def ExtractionConfidenceOracle :> OracleService {
            attribute returnedConfidence : ScalarValues::Real;
            port reading : ReadingWrite;
        }

        part def ConsensusComparatorOracle :> OracleService {
            doc /* provisional: GAP-04 (the disagreement metric is never
               defined; an opaque scalar, threshold semantics only). */
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
            port toHuman : ObligationWrite;
            port toCog : ClearanceWrite;
        }

        part def HumanAction :> OpComponent {
            doc /* The concrete actions that discharge obligations
               (adjudicated: GAP-02 — a concrete action discharges an
               obligation and must also mutate state; the Track evidences
               both). */
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
               provisional: GAP-08 (the paper draws no internal wiring;
               this topology is drawn from the section 4.1/4.5 narrative). */
            end supplier : ReadingWrite;
            end consumer : ~ReadingWrite;
        }
        interface def ObligationSeam {
            doc /* Raised obligations cross to the humans who discharge them. */
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
               engine; obligations flow to the human actions; clearance
               flows to the summary cog; the boundary exposes the result.
               Interface usages are declared before the parts they connect
               (executor materializes in declaration order). */

            interface confidenceSeam : ReadingSeam connect confidenceOracle.reading to policyEngine.fromConfidence;
            interface consensusSeam : ReadingSeam connect consensusOracle.reading to policyEngine.fromConsensus;
            interface scannerSeam : ReadingSeam connect scannerOracle.reading to policyEngine.fromScanner;
            interface riskSeam : ReadingSeam connect riskOracle.reading to policyEngine.fromRisk;
            interface obligationSeam : ObligationSeam connect policyEngine.toHuman to humanAction.fromEngine;
            interface clearanceSeam : ClearanceSeam connect policyEngine.toCog to summaryCog.clearance;

            part confidenceOracle : ExtractionConfidenceOracle;
            part consensusOracle : ConsensusComparatorOracle;
            part scannerOracle : SensitiveDataScannerOracle;
            part riskOracle : VendorRiskOracle;
            part policyEngine : PolicyEngine;
            part humanAction : HumanAction;
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
               the human actions. */
            subject op : VendorFraudReviewOp;
            require constraint { op.policyEngine.humanReviewRequired implies op.humanAction.humanReviewPerformed }
            require constraint { op.policyEngine.expertReviewRequired implies op.humanAction.expertReviewPerformed }
            require constraint { op.policyEngine.stopAndEscalate implies op.humanAction.escalationPerformed }
            require constraint { op.policyEngine.humanApprovalRequired implies op.humanAction.humanApprovalGiven }
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
        doc /* Concrete runs of the assembled Op. Values descend into the
           components by nested redefinition; the sweep evaluates the
           component, wiring, and system checks together. */

        part def CleanRun :> Manifest::VendorFraudReviewOp {
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.92; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 0.10; }
            part :>> scannerOracle { attribute :>> returnedDetected = false; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::low; }
            part :>> policyEngine {
                attribute :>> confidence = 0.92;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::high;
                attribute :>> consensusDisagreement = 0.10;
                attribute :>> sensitiveDataDetected = false;
                attribute :>> vendorRisk = Manifest::RiskLevel::low;
                attribute :>> humanReviewRequired = false;
                attribute :>> expertReviewRequired = false;
                attribute :>> stopAndEscalate = false;
                attribute :>> humanApprovalRequired = false;
            }
            part :>> humanAction {
                attribute :>> humanReviewPerformed = false;
                attribute :>> expertReviewPerformed = false;
                attribute :>> escalationPerformed = false;
                attribute :>> humanApprovalGiven = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }

        part def EscalatedRun :> Manifest::VendorFraudReviewOp {
            doc /* The run of track/run-001.trig: confidence 0.71 fires
               GATE-01, vendor risk high fires GATE-04; both obligations
               discharged; the Op executed and emitted its summary. */
            part :>> confidenceOracle { attribute :>> returnedConfidence = 0.71; }
            part :>> consensusOracle { attribute :>> returnedDisagreement = 0.10; }
            part :>> scannerOracle { attribute :>> returnedDetected = false; }
            part :>> riskOracle { attribute :>> returnedRisk = Manifest::RiskLevel::high; }
            part :>> policyEngine {
                attribute :>> confidence = 0.71;
                attribute :>> confidenceLevel = Manifest::ConfidenceLevel::low;
                attribute :>> consensusDisagreement = 0.10;
                attribute :>> sensitiveDataDetected = false;
                attribute :>> vendorRisk = Manifest::RiskLevel::high;
                attribute :>> humanReviewRequired = true;
                attribute :>> expertReviewRequired = false;
                attribute :>> stopAndEscalate = false;
                attribute :>> humanApprovalRequired = true;
            }
            part :>> humanAction {
                attribute :>> humanReviewPerformed = true;
                attribute :>> expertReviewPerformed = false;
                attribute :>> escalationPerformed = false;
                attribute :>> humanApprovalGiven = true;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
            attribute :>> aggregateOutcome = Manifest::AggregateOutcome::executed;
        }

        part cleanRun : CleanRun;
        part escalatedRun : EscalatedRun;

        requirement cleanInterface01 : Manifest::ConfidenceInterface { subject pe = cleanRun.policyEngine; }
        requirement cleanGate01 : Manifest::ConfidenceGate { subject pe = cleanRun.policyEngine; }
        requirement cleanGate02 : Manifest::ConsensusGate { subject pe = cleanRun.policyEngine; }
        requirement cleanGate03 : Manifest::SensitiveDataGate { subject pe = cleanRun.policyEngine; }
        requirement cleanGate04 : Manifest::VendorRiskGate { subject pe = cleanRun.policyEngine; }
        requirement cleanWire01 : Manifest::ConfidenceSeamIntegrity { subject op = cleanRun; }
        requirement cleanWire02 : Manifest::ConsensusSeamIntegrity { subject op = cleanRun; }
        requirement cleanWire03 : Manifest::ScannerSeamIntegrity { subject op = cleanRun; }
        requirement cleanWire04 : Manifest::RiskSeamIntegrity { subject op = cleanRun; }
        requirement cleanSystem01 : Manifest::ObligationsDischarged { subject op = cleanRun; }
        requirement cleanSystem02 : Manifest::StopMeansNoOutput { subject op = cleanRun; }
        requirement cleanSystem03 : Manifest::OutcomeCoherence { subject op = cleanRun; }

        requirement escalatedInterface01 : Manifest::ConfidenceInterface { subject pe = escalatedRun.policyEngine; }
        requirement escalatedGate01 : Manifest::ConfidenceGate { subject pe = escalatedRun.policyEngine; }
        requirement escalatedGate02 : Manifest::ConsensusGate { subject pe = escalatedRun.policyEngine; }
        requirement escalatedGate03 : Manifest::SensitiveDataGate { subject pe = escalatedRun.policyEngine; }
        requirement escalatedGate04 : Manifest::VendorRiskGate { subject pe = escalatedRun.policyEngine; }
        requirement escalatedWire01 : Manifest::ConfidenceSeamIntegrity { subject op = escalatedRun; }
        requirement escalatedWire02 : Manifest::ConsensusSeamIntegrity { subject op = escalatedRun; }
        requirement escalatedWire03 : Manifest::ScannerSeamIntegrity { subject op = escalatedRun; }
        requirement escalatedWire04 : Manifest::RiskSeamIntegrity { subject op = escalatedRun; }
        requirement escalatedSystem01 : Manifest::ObligationsDischarged { subject op = escalatedRun; }
        requirement escalatedSystem02 : Manifest::StopMeansNoOutput { subject op = escalatedRun; }
        requirement escalatedSystem03 : Manifest::OutcomeCoherence { subject op = escalatedRun; }

        verification def CleanRunCase {
            objective {
                verify cleanInterface01;
                verify cleanGate01;
                verify cleanGate02;
                verify cleanGate03;
                verify cleanGate04;
                verify cleanWire01;
                verify cleanWire02;
                verify cleanWire03;
                verify cleanWire04;
                verify cleanSystem01;
                verify cleanSystem02;
                verify cleanSystem03;
            }
        }
        verification def EscalatedRunCase {
            objective {
                verify escalatedInterface01;
                verify escalatedGate01;
                verify escalatedGate02;
                verify escalatedGate03;
                verify escalatedGate04;
                verify escalatedWire01;
                verify escalatedWire02;
                verify escalatedWire03;
                verify escalatedWire04;
                verify escalatedSystem01;
                verify escalatedSystem02;
                verify escalatedSystem03;
            }
        }
        verification cleanRunCase : CleanRunCase;
        verification escalatedRunCase : EscalatedRunCase;
    }

    package ExerciseContexts {
        doc /* Trace drivers: siblings deliver signals to the assembly's own
           ports over connects (messages do not relay through binds in
           v0.4.3). Trace output is the only honest post-run evidence. */

        part def EscalationDriver {
            port fire : ~Manifest::StopIn;
            item e : Manifest::Escalation;
            exhibit state d {
                entry; then firing;
                state firing { entry action f { send e via fire; } }
                state spent;
                succession first firing then spent;
            }
        }

        part def ProceedDriver {
            port fire : ~Manifest::ProceedIn;
            item p : Manifest::Proceed;
            exhibit state d {
                entry; then firing;
                state firing { entry action f { send p via fire; } }
                state spent;
                succession first firing then spent;
            }
        }

        interface def StopWire { end source : ~Manifest::StopIn; end sink : Manifest::StopIn; }
        interface def ProceedWire { end source : ~Manifest::ProceedIn; end sink : Manifest::ProceedIn; }

        part stoppedContext {
            doc /* A sensitive-data escalation reaches the Op: the lifecycle
               must enter stopped, and nothing is transmitted. */
            interface w : StopWire connect driver.fire to op.stopSignal;
            part driver : EscalationDriver;
            part op : Manifest::VendorFraudReviewOp;
        }

        part completedContext {
            doc /* The run proceeds to completion. */
            interface w : ProceedWire connect driver.fire to op.proceedSignal;
            part driver : ProceedDriver;
            part op : Manifest::VendorFraudReviewOp;
        }
    }
}
