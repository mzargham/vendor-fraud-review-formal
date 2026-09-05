package VendorFraudReviewUnattended {
    doc /* Negative counterpart: the same manifest gates, with a run whose
       extraction confidence fires GATE-01 while no human review step is
       engaged. Satisfy on RunConfigurations must FAIL (exit 1) — this file
       proves the gate algebra can say no. Self-contained on purpose. */

    package Manifest {
        part def VendorFraudReviewOp {
            attribute confidence : ScalarValues::Real;
            attribute consensusDisagreement : ScalarValues::Real;
            attribute sensitiveDataDetected : ScalarValues::Boolean;
            attribute vendorRisk : ScalarValues::String;
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
    }

    package RunConfigurations {
        part def UnattendedRun :> Manifest::VendorFraudReviewOp {
            doc /* Confidence 0.71 fires GATE-01, but human_review_required
               is false: the Op proceeded with no human in the loop. */
            attribute :>> confidence = 0.71;
            attribute :>> consensusDisagreement = 0.10;
            attribute :>> sensitiveDataDetected = false;
            attribute :>> vendorRisk = "low";
            attribute :>> humanReviewRequired = false;
            attribute :>> expertReviewRequired = false;
            attribute :>> stopAndEscalate = false;
            attribute :>> humanApprovalRequired = false;
        }

        part unattendedRun : UnattendedRun;

        requirement unattendedGate01 : Manifest::ConfidenceGate { subject op = unattendedRun; }

        verification def UnattendedRunCase {
            objective {
                verify unattendedGate01;
            }
        }
        verification unattendedRunCase : UnattendedRunCase;
    }
}
