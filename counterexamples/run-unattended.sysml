package VendorFraudReviewUnattended {
    doc /* Negative counterparts: the same manifest gates and discharge rule,
       with two runs that must FAIL satisfy (exit 1). unattendedRun: the gate
       condition holds but no obligation was raised. undischargedRun: the
       obligation was raised but no concrete action discharged it
       (adjudicated: GAP-02 — obligation and discharge are distinct).
       Self-contained on purpose. */

    package Manifest {
        part def VendorFraudReviewOp {
            attribute confidence : ScalarValues::Real;
            attribute humanReviewRequired : ScalarValues::Boolean;
            attribute humanReviewPerformed : ScalarValues::Boolean;
        }

        requirement def <'GATE-01'> ConfidenceGate {
            doc /* - if: confidence < 0.80
                    then: human_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject op : VendorFraudReviewOp;
            require constraint { op.confidence < 0.80 implies op.humanReviewRequired }
        }

        requirement def <'DISCHARGE-01'> ObligationsDischarged {
            subject op : VendorFraudReviewOp;
            require constraint { op.humanReviewRequired implies op.humanReviewPerformed }
        }
    }

    package RunConfigurations {
        part def UnattendedRun :> Manifest::VendorFraudReviewOp {
            doc /* Confidence 0.71 fires GATE-01, but human_review_required
               is false: the Op proceeded with no obligation raised. */
            attribute :>> confidence = 0.71;
            attribute :>> humanReviewRequired = false;
            attribute :>> humanReviewPerformed = false;
        }

        part def UndischargedRun :> Manifest::VendorFraudReviewOp {
            doc /* The obligation was raised — and never discharged by any
               concrete action. */
            attribute :>> confidence = 0.71;
            attribute :>> humanReviewRequired = true;
            attribute :>> humanReviewPerformed = false;
        }

        part unattendedRun : UnattendedRun;
        part undischargedRun : UndischargedRun;

        requirement unattendedGate01 : Manifest::ConfidenceGate { subject op = unattendedRun; }
        requirement undischargedDischarge01 : Manifest::ObligationsDischarged { subject op = undischargedRun; }

        verification def UnattendedRunCase {
            objective {
                verify unattendedGate01;
                verify undischargedDischarge01;
            }
        }
        verification unattendedRunCase : UnattendedRunCase;
    }
}
