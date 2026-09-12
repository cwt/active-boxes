from active_boxes import linked_data_sig
from active_boxes.data_integrity import (
    generate_integrity_proof,
    has_integrity_proof,
    jcs_canonicalize,
    verify_integrity_proof,
)
from active_boxes.key import Ed25519Key


def _sample_doc():
    return {
        "@context": [
            "https://www.w3.org/ns/activitystreams",
            "https://w3id.org/security/data-integrity/v2",
        ],
        "id": "https://example.com/notes/1",
        "type": "Note",
        "attributedTo": "https://example.com/users/alice",
        "content": "Hello world",
    }


def test_jcs_canonicalize_sorts_keys():
    assert jcs_canonicalize({"b": 1, "a": 2}) == b'{"a":2,"b":1}'


def test_integrity_proof_roundtrip():
    key = Ed25519Key("https://example.com/users/alice")
    key.new()
    doc = _sample_doc()
    proof = generate_integrity_proof(doc, key)
    assert proof["type"] == "DataIntegrityProof"
    assert proof["cryptosuite"] == "eddsa-jcs-2022"
    assert has_integrity_proof(doc) is True
    assert verify_integrity_proof(doc, key) is True


def test_integrity_proof_tamper_fails():
    key = Ed25519Key("https://example.com/users/alice")
    key.new()
    doc = _sample_doc()
    generate_integrity_proof(doc, key)
    doc["content"] = "Tampered"
    assert verify_integrity_proof(doc, key) is False


def test_integrity_proof_wrong_key_fails():
    key = Ed25519Key("https://example.com/users/alice")
    key.new()
    other = Ed25519Key("https://example.com/users/bob")
    other.new()
    doc = _sample_doc()
    generate_integrity_proof(doc, key)
    assert verify_integrity_proof(doc, other) is False


def test_integrity_proof_strips_legacy_signature():
    ed_key = Ed25519Key("https://example.com/users/alice")
    ed_key.new()
    doc = _sample_doc()
    doc["actor"] = "https://example.com/users/alice"
    generate_integrity_proof(doc, ed_key)
    # Add a legacy signature afterwards (compat mode: proof first, sig second).
    # Use a stub signature to avoid pyld network resolution in unit tests;
    # proof verification must ignore it per FEP-8b32.
    doc["signature"] = {
        "type": "RsaSignature2017",
        "creator": "https://example.com/users/alice#main-key",
        "created": "2026-01-01T00:00:00Z",
        "signatureValue": "invalid",
    }
    # Proof must still verify when signature is ignored per FEP-8b32
    assert verify_integrity_proof(doc, ed_key) is True
    # Embedded helper falls through to proof when LD sig is invalid
    assert linked_data_sig.verify_embedded_signature(doc, None, ed_key) is True
