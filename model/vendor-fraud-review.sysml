package VendorFraudReview {
    doc /* The Vendor Fraud Review Op manifest (whitepaper section 5.6),
       rendered literally as an executable specification. Every gate is
       the direct implication form of a manifest line quoted verbatim in
       its doc comment. Interpretive choices are logged in
       open-questions/computability-gaps.md: entries marked provisional
       await adjudication; entries marked adjudicated carry the ruling
       recorded in open-questions/adjudication-log.md. */

    package Manifest {

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
               value; INTERFACE-01 binds the two at the manifest's 0.80
               boundary. */
            high;
            low;
            unknown;
        }

        part def VendorFraudReviewOp {
            doc /* op: name: vendor-fraud-review
               frames: company-policy, procurement-rules, fraud-detection-methodology
               cogs: invoice-extraction-cog, vendor-risk-cog, anomaly-summary-cog
               Source: WP section 5.6, manifest sketch. */

            /* Raw readings. provisional: GAP-04 (consensus_disagreement is
               never defined; modeled as a scalar compared against the 0.25
               threshold, metric semantics left open pending adjudication). */
            attribute confidence : ScalarValues::Real;
            attribute confidenceLevel : ConfidenceLevel;
            attribute consensusDisagreement : ScalarValues::Real;
            attribute sensitiveDataDetected : ScalarValues::Boolean;
            attribute vendorRisk : RiskLevel;

            /* Obligations. adjudicated: GAP-02 — a then-clause names an
               obligation: a required action, abstract, not yet materialized.
               State (the readings above) implies obligation; a concrete
               action discharges the obligation and must also mutate state
               (the Track evidences both the action and the state it
               generated). */
            attribute humanReviewRequired : ScalarValues::Boolean;
            attribute expertReviewRequired : ScalarValues::Boolean;
            attribute stopAndEscalate : ScalarValues::Boolean;
            attribute humanApprovalRequired : ScalarValues::Boolean;

            /* Discharges: whether the concrete action materialized. */
            attribute humanReviewPerformed : ScalarValues::Boolean;
            attribute expertReviewPerformed : ScalarValues::Boolean;
            attribute escalationPerformed : ScalarValues::Boolean;
            attribute humanApprovalGiven : ScalarValues::Boolean;
        }

        requirement def <'INTERFACE-01'> ConfidenceInterface {
            doc /* adjudicated: GAP-03 — the interface contract between the
               raw confidence reading and its level: the manifest's 0.80
               threshold is the boundary of the simplified scheme. */
            subject op : VendorFraudReviewOp;
            require constraint { op.confidence < 0.80 implies op.confidenceLevel == ConfidenceLevel::low }
            require constraint { op.confidence >= 0.80 implies op.confidenceLevel == ConfidenceLevel::high }
        }

        requirement def <'GATE-01'> ConfidenceGate {
            doc /* - if: confidence < 0.80
                    then: human_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject op : VendorFraudReviewOp;
            require constraint { op.confidence < 0.80 implies op.humanReviewRequired }
        }

        requirement def <'GATE-02'> ConsensusGate {
            doc /* - if: consensus_disagreement > 0.25
                    then: expert_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject op : VendorFraudReviewOp;
            require constraint { op.consensusDisagreement > 0.25 implies op.expertReviewRequired }
        }

        requirement def <'GATE-03'> SensitiveDataGate {
            doc /* - if: sensitive_data_detected
                    then: stop_and_escalate
               Source: WP section 5.6 gates block, verbatim. */
            subject op : VendorFraudReviewOp;
            require constraint { op.sensitiveDataDetected implies op.stopAndEscalate }
        }

        requirement def <'GATE-04'> VendorRiskGate {
            doc /* - if: vendor_risk == high
                    then: human_approval_required
               Source: WP section 5.6 gates block, verbatim.
               adjudicated: GAP-01 — high is RiskLevel::high. */
            subject op : VendorFraudReviewOp;
            require constraint { op.vendorRisk == RiskLevel::high implies op.humanApprovalRequired }
        }

        requirement def <'DISCHARGE-01'> ObligationsDischarged {
            doc /* adjudicated: GAP-02 — a closed run must show every raised
               obligation discharged by a concrete action; the Track shapes
               additionally require that the discharging action mutated
               state. */
            subject op : VendorFraudReviewOp;
            require constraint { op.humanReviewRequired implies op.humanReviewPerformed }
            require constraint { op.expertReviewRequired implies op.expertReviewPerformed }
            require constraint { op.stopAndEscalate implies op.escalationPerformed }
            require constraint { op.humanApprovalRequired implies op.humanApprovalGiven }
        }
    }

    package RunConfigurations {
        doc /* Concrete runs of the Op. Satisfy sweeps these: the clean run
           holds with no obligation raised; the escalated run holds because
           its obligations are raised AND discharged. The negative
           counterparts live in counterexamples/run-unattended.sysml and
           must fail. */

        part def CleanRun :> Manifest::VendorFraudReviewOp {
            attribute :>> confidence = 0.92;
            attribute :>> confidenceLevel = Manifest::ConfidenceLevel::high;
            attribute :>> consensusDisagreement = 0.10;
            attribute :>> sensitiveDataDetected = false;
            attribute :>> vendorRisk = Manifest::RiskLevel::low;
            attribute :>> humanReviewRequired = false;
            attribute :>> expertReviewRequired = false;
            attribute :>> stopAndEscalate = false;
            attribute :>> humanApprovalRequired = false;
            attribute :>> humanReviewPerformed = false;
            attribute :>> expertReviewPerformed = false;
            attribute :>> escalationPerformed = false;
            attribute :>> humanApprovalGiven = false;
        }

        part def EscalatedRun :> Manifest::VendorFraudReviewOp {
            doc /* The run demonstrated in track/run-001.trig: extraction
               confidence 0.71 fires GATE-01 and vendor risk high fires
               GATE-04; both obligations are discharged by the recorded
               human review. */
            attribute :>> confidence = 0.71;
            attribute :>> confidenceLevel = Manifest::ConfidenceLevel::low;
            attribute :>> consensusDisagreement = 0.10;
            attribute :>> sensitiveDataDetected = false;
            attribute :>> vendorRisk = Manifest::RiskLevel::high;
            attribute :>> humanReviewRequired = true;
            attribute :>> expertReviewRequired = false;
            attribute :>> stopAndEscalate = false;
            attribute :>> humanApprovalRequired = true;
            attribute :>> humanReviewPerformed = true;
            attribute :>> expertReviewPerformed = false;
            attribute :>> escalationPerformed = false;
            attribute :>> humanApprovalGiven = true;
        }

        part cleanRun : CleanRun;
        part escalatedRun : EscalatedRun;

        requirement cleanInterface01 : Manifest::ConfidenceInterface { subject op = cleanRun; }
        requirement cleanGate01 : Manifest::ConfidenceGate { subject op = cleanRun; }
        requirement cleanGate02 : Manifest::ConsensusGate { subject op = cleanRun; }
        requirement cleanGate03 : Manifest::SensitiveDataGate { subject op = cleanRun; }
        requirement cleanGate04 : Manifest::VendorRiskGate { subject op = cleanRun; }
        requirement cleanDischarge01 : Manifest::ObligationsDischarged { subject op = cleanRun; }

        requirement escalatedInterface01 : Manifest::ConfidenceInterface { subject op = escalatedRun; }
        requirement escalatedGate01 : Manifest::ConfidenceGate { subject op = escalatedRun; }
        requirement escalatedGate02 : Manifest::ConsensusGate { subject op = escalatedRun; }
        requirement escalatedGate03 : Manifest::SensitiveDataGate { subject op = escalatedRun; }
        requirement escalatedGate04 : Manifest::VendorRiskGate { subject op = escalatedRun; }
        requirement escalatedDischarge01 : Manifest::ObligationsDischarged { subject op = escalatedRun; }

        verification def CleanRunCase {
            objective {
                verify cleanInterface01;
                verify cleanGate01;
                verify cleanGate02;
                verify cleanGate03;
                verify cleanGate04;
                verify cleanDischarge01;
            }
        }
        verification def EscalatedRunCase {
            objective {
                verify escalatedInterface01;
                verify escalatedGate01;
                verify escalatedGate02;
                verify escalatedGate03;
                verify escalatedGate04;
                verify escalatedDischarge01;
            }
        }
        verification cleanRunCase : CleanRunCase;
        verification escalatedRunCase : EscalatedRunCase;
    }
}
