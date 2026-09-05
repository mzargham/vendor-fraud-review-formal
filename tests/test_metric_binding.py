"""The model's metric definitions are bound to their implementations.

The binding is a stated, mechanical convention — a definition's metric id
is derived from its name (DissentFractionMetric -> dissent-fraction) —
and it is checked in both directions: every concrete specialization of
DisagreementMetric in the model has exactly one implementation, every
implementation has exactly one definition, and the metric a Track cites
is bindable.
"""
import re
import sys

import rdflib

from conftest import MODEL, ROOT, TRACK, VFR

sys.path.insert(0, str(ROOT))
import exhibits  # noqa: E402


def _model_defs():
    return re.findall(r"part def (\w+Metric) :> DisagreementMetric", MODEL.read_text())


def test_model_definitions_and_implementations_are_one_to_one():
    defs = _model_defs()
    assert len(defs) == 3, "three concrete metric definitions expected in the model"
    derived = {exhibits.metric_id(d) for d in defs}
    assert derived == set(exhibits.METRICS), (
        f"model definitions {derived} and implementations "
        f"{set(exhibits.METRICS)} do not correspond one-to-one"
    )


def test_track_recorded_metric_is_bindable():
    ds = rdflib.Dataset(default_union=True)
    ds.parse(TRACK, format="trig")
    recorded = [
        str(row[0]) for row in ds.query(
            f"SELECT ?m WHERE {{ ?call <{VFR}metric> ?m }}"
        )
    ]
    assert recorded, "run-001 records no metric on the consensus oracle call"
    for metric in recorded:
        assert metric in exhibits.METRICS, (
            f"run-001 cites metric {metric!r} with no bound implementation"
        )
