package VendorFraudReviewMiswired {
    doc /* COUNTEREXAMPLE: an oracle's reading port wired into a summary
       input — a seam whose ends do not match its interface definition.
       `-validate -strict` ACCEPTS this file (probed 2026-09-04); the
       wiring rules in tests/test_wiring.py must refuse it. The parser
       holds the wiring; code over the conversion holds the wiring rules. */

    item def Reading;
    item def Summary;

    port def ReadingWrite { out item r : Reading; }
    port def SummaryWrite { out item s : Summary; }

    interface def ReadingSeam {
        end supplier : ReadingWrite;
        end consumer : ~ReadingWrite;
    }

    part def ExtractionConfidenceOracle {
        port reading : ReadingWrite;
    }

    part def AnomalySummaryCog {
        port summaryIn : ~SummaryWrite;
    }

    part def MiswiredOp {
        part confidenceOracle : ExtractionConfidenceOracle;
        part summaryCog : AnomalySummaryCog;
        // A ReadingSeam whose consumer end lands on a ~SummaryWrite port.
        interface confidenceSeam : ReadingSeam connect confidenceOracle.reading to summaryCog.summaryIn;
    }

    part miswiredOp : MiswiredOp;
}
