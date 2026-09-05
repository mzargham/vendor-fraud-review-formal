package VendorFraudReviewUnattended {
    doc /* Negative counterparts: the value-check subset of the assembled
       Op, with three runs that must FAIL satisfy (exit 1) — one per check
       level. unattendedRun: the gate condition holds but no obligation was
       raised (component level). undischargedRun: the obligation was raised
       and no concrete action discharged it (system level, GAP-02).
       stoppedButEmittedRun: the Op stopped and emitted output anyway
       (aggregate level, GAP-06; WP section 5.2: "the Op stops before
       external transmission"). Self-contained on purpose. */

    package Manifest {
        part def ValidationStrategyParameters {
            attribute confidenceThreshold : ScalarValues::Real = 0.80;
        }

        part def PolicyEngine {
            part policy : ValidationStrategyParameters;
            attribute confidence : ScalarValues::Real;
            attribute humanReviewRequired : ScalarValues::Boolean;
            attribute stopAndEscalate : ScalarValues::Boolean;
        }

        part def HumanAction {
            attribute humanReviewPerformed : ScalarValues::Boolean;
            attribute escalationPerformed : ScalarValues::Boolean;
        }

        part def AnomalySummaryCog {
            attribute outputEmitted : ScalarValues::Boolean;
        }

        part def VendorFraudReviewOp {
            part policyEngine : PolicyEngine;
            part humanAction : HumanAction;
            part summaryCog : AnomalySummaryCog;
        }

        requirement def <'GATE-01'> ConfidenceGate {
            doc /* - if: confidence < 0.80
                    then: human_review_required
               Source: WP section 5.6 gates block, verbatim. */
            subject pe : PolicyEngine;
            require constraint { pe.confidence < pe.policy.confidenceThreshold implies pe.humanReviewRequired }
        }

        requirement def <'SYSTEM-01'> ObligationsDischarged {
            subject op : VendorFraudReviewOp;
            require constraint { op.policyEngine.humanReviewRequired implies op.humanAction.humanReviewPerformed }
        }

        requirement def <'SYSTEM-02'> StopMeansNoOutput {
            doc /* WP section 5.2, verbatim: "the Op stops before external
               transmission." */
            subject op : VendorFraudReviewOp;
            require constraint { op.policyEngine.stopAndEscalate implies not op.summaryCog.outputEmitted }
        }
    }

    package RunConfigurations {
        part def UnattendedRun :> Manifest::VendorFraudReviewOp {
            doc /* Confidence 0.71 fires GATE-01, but no obligation was
               raised: the Op proceeded with no human in the loop. */
            part :>> policyEngine {
                attribute :>> confidence = 0.71;
                attribute :>> humanReviewRequired = false;
                attribute :>> stopAndEscalate = false;
            }
            part :>> humanAction {
                attribute :>> humanReviewPerformed = false;
                attribute :>> escalationPerformed = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
        }

        part def UndischargedRun :> Manifest::VendorFraudReviewOp {
            doc /* The obligation was raised — and never discharged by any
               concrete action. */
            part :>> policyEngine {
                attribute :>> confidence = 0.71;
                attribute :>> humanReviewRequired = true;
                attribute :>> stopAndEscalate = false;
            }
            part :>> humanAction {
                attribute :>> humanReviewPerformed = false;
                attribute :>> escalationPerformed = false;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
        }

        part def StoppedButEmittedRun :> Manifest::VendorFraudReviewOp {
            doc /* The stop obligation was raised and even discharged — and
               the Op transmitted its output anyway. Navigating the rules
               and executing regardless is the aggregate violation. */
            part :>> policyEngine {
                attribute :>> confidence = 0.92;
                attribute :>> humanReviewRequired = false;
                attribute :>> stopAndEscalate = true;
            }
            part :>> humanAction {
                attribute :>> humanReviewPerformed = false;
                attribute :>> escalationPerformed = true;
            }
            part :>> summaryCog { attribute :>> outputEmitted = true; }
        }

        part unattendedRun : UnattendedRun;
        part undischargedRun : UndischargedRun;
        part stoppedButEmittedRun : StoppedButEmittedRun;

        requirement unattendedGate01 : Manifest::ConfidenceGate { subject pe = unattendedRun.policyEngine; }
        requirement undischargedSystem01 : Manifest::ObligationsDischarged { subject op = undischargedRun; }
        requirement emittedSystem02 : Manifest::StopMeansNoOutput { subject op = stoppedButEmittedRun; }

        verification def NegativeRunsCase {
            objective {
                verify unattendedGate01;
                verify undischargedSystem01;
                verify emittedSystem02;
            }
        }
        verification negativeRunsCase : NegativeRunsCase;
    }
}
