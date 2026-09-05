package VendorFraudReview {
    doc /* The Vendor Fraud Review Op manifest (whitepaper section 5.6),
       rendered literally as an executable specification. Every gate is
       the direct implication form of a manifest line quoted verbatim in
       its doc comment. Interpretive choices forced by the substrate are
       marked provisional and logged in open-questions/computability-gaps.md. */

    package Manifest {

        part def VendorFraudReviewOp {
            doc /* op: name: vendor-fraud-review
               frames: company-policy, procurement-rules, fraud-detection-methodology
               cogs: invoice-extraction-cog, vendor-risk-cog, anomaly-summary-cog
               Source: WP section 5.6, manifest sketch. */

            /* Decision variables read by the gates. provisional: GAP-03
               (which Guard produces confidence, and at what granularity,
               is not stated; modeled as one per-run scalar). */
            attribute confidence : ScalarValues::Real;

            /* provisional: GAP-04 (consensus_disagreement is never defined;
               modeled as a scalar compared against the 0.25 threshold). */
            attribute consensusDisagreement : ScalarValues::Real;

            attribute sensitiveDataDetected : ScalarValues::Boolean;

            /* provisional: GAP-01 (the type of vendor_risk and the value
               'high' are undeclared; modeled as a string attribute compared
               to the string "high"). */
            attribute vendorRisk : ScalarValues::String;

            /* Gate consequents. provisional: GAP-02 (whether a then-clause
               names a state the Op enters, an obligation on the Track, or
               an action is not stated; modeled as Boolean attributes that
               must hold whenever their gate condition holds). */
            attribute humanReviewRequired : ScalarValues::Boolean;
            attribute expertReviewRequired : ScalarValues::Boolean;
            attribute stopAndEscalate : ScalarValues::Boolean;
            attribute humanApprovalRequired : ScalarValues::Boolean;
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
               Source: WP section 5.6 gates block, verbatim. */
            subject op : VendorFraudReviewOp;
            require constraint { op.vendorRisk == "high" implies op.humanApprovalRequired }
        }
    }

    package RunConfigurations {
        doc /* Concrete runs of the Op. Satisfy sweeps these: the clean run
           holds with no human step engaged; the escalated run holds because
           the human step IS engaged. The negative counterpart lives in
           counterexamples/run-unattended.sysml and must fail. */

        part def CleanRun :> Manifest::VendorFraudReviewOp {
            attribute :>> confidence = 0.92;
            attribute :>> consensusDisagreement = 0.10;
            attribute :>> sensitiveDataDetected = false;
            attribute :>> vendorRisk = "low";
            attribute :>> humanReviewRequired = false;
            attribute :>> expertReviewRequired = false;
            attribute :>> stopAndEscalate = false;
            attribute :>> humanApprovalRequired = false;
        }

        part def EscalatedRun :> Manifest::VendorFraudReviewOp {
            doc /* The run demonstrated in track/run-001.trig: extraction
               confidence 0.71 fires GATE-01 and the human review step is
               engaged, so the gate holds. */
            attribute :>> confidence = 0.71;
            attribute :>> consensusDisagreement = 0.10;
            attribute :>> sensitiveDataDetected = false;
            attribute :>> vendorRisk = "high";
            attribute :>> humanReviewRequired = true;
            attribute :>> expertReviewRequired = false;
            attribute :>> stopAndEscalate = false;
            attribute :>> humanApprovalRequired = true;
        }

        part cleanRun : CleanRun;
        part escalatedRun : EscalatedRun;

        requirement cleanGate01 : Manifest::ConfidenceGate { subject op = cleanRun; }
        requirement cleanGate02 : Manifest::ConsensusGate { subject op = cleanRun; }
        requirement cleanGate03 : Manifest::SensitiveDataGate { subject op = cleanRun; }
        requirement cleanGate04 : Manifest::VendorRiskGate { subject op = cleanRun; }

        requirement escalatedGate01 : Manifest::ConfidenceGate { subject op = escalatedRun; }
        requirement escalatedGate02 : Manifest::ConsensusGate { subject op = escalatedRun; }
        requirement escalatedGate03 : Manifest::SensitiveDataGate { subject op = escalatedRun; }
        requirement escalatedGate04 : Manifest::VendorRiskGate { subject op = escalatedRun; }

        verification def CleanRunCase {
            objective {
                verify cleanGate01;
                verify cleanGate02;
                verify cleanGate03;
                verify cleanGate04;
            }
        }
        verification def EscalatedRunCase {
            objective {
                verify escalatedGate01;
                verify escalatedGate02;
                verify escalatedGate03;
                verify escalatedGate04;
            }
        }
        verification cleanRunCase : CleanRunCase;
        verification escalatedRunCase : EscalatedRunCase;
    }
}
