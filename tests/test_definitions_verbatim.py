"""The vocabulary is his text, provably.

Every skos:definition in the vocabulary must appear verbatim (normalized) in
the pinned PDF snapshot, and the snapshot's sha256 must match the Source
node's contentHash.
"""
import hashlib

import rdflib
from rdflib.namespace import SKOS

from conftest import ROOT, VFR, normalized


def test_snapshot_hash_matches_source_node(vocabulary_graph):
    pdfs = sorted((ROOT / "sources").glob("*.pdf"))
    assert len(pdfs) == 1
    actual = hashlib.sha256(pdfs[0].read_bytes()).hexdigest()
    declared = list(
        vocabulary_graph.objects(None, rdflib.URIRef(VFR + "contentHash"))
    )
    assert len(declared) == 1, "exactly one Source node with a contentHash expected"
    assert str(declared[0]) == actual, "Source contentHash != sha256 of the snapshot"
    assert pdfs[0].name == f"{actual}.pdf", "snapshot filename is its own sha256"


def test_every_definition_is_verbatim_from_the_snapshot(vocabulary_graph, pdf_text):
    definitions = list(vocabulary_graph.subject_objects(SKOS.definition))
    assert len(definitions) >= 10, "at least ten defined concepts expected"
    for concept, definition in definitions:
        assert normalized(str(definition)) in pdf_text, (
            f"definition of {concept} is not verbatim from the pinned snapshot"
        )


def test_every_defined_concept_cites_the_source_with_a_locator(vocabulary_graph):
    cites = rdflib.URIRef(VFR + "cites")
    locator = rdflib.URIRef(VFR + "locator")
    for concept in set(vocabulary_graph.subjects(SKOS.definition, None)):
        sources = list(vocabulary_graph.objects(concept, cites))
        assert sources, f"{concept} has a definition but cites no source"
        locators = list(vocabulary_graph.objects(concept, locator))
        assert locators, f"{concept} has no section locator"
        assert any("§" in str(v) for v in locators), (
            f"{concept} locator does not carry a section reference"
        )
