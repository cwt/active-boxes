"""Data Integrity Proofs for ActivityPub (FEP-8b32).

Implements the ``eddsa-jcs-2022`` cryptosuite with JSON Canonicalization
Scheme (JCS, RFC 8785 subset) and Ed25519, alongside the legacy
``RsaSignature2017`` path kept in :mod:`linked_data_sig`.

Mastodon 4.7 verifies top-level ``eddsa-jcs-2022`` (or ``mldsa44-jcs-2024``)
proofs inbound but still emits ``RsaSignature2017``. This module therefore
focuses on verify + generate for ``eddsa-jcs-2022`` so this library can
federate both ways while keeping the old signatures for compatibility.

Per FEP-8b32 backward compatibility: when both ``proof`` and ``signature``
are present, ``signature`` MUST be removed before verifying ``proof``.
"""

import base64
import hashlib
import json
import math
from datetime import datetime, timezone
from typing import Any

from Crypto.PublicKey import ECC
from Crypto.Signature import eddsa

from .key import Ed25519Key, base58btc_decode, base58btc_encode

SUPPORTED_CRYPTOSUITES = ("eddsa-jcs-2022",)


def jcs_canonicalize(value: Any) -> bytes:
    """Canonicalize JSON with JCS subset (RFC 8785).

    Uses sorted keys, no whitespace, UTF-8. Numbers that are not finite
    (NaN/Infinity) are rejected per JCS. For typical ActivityPub ASCII
    documents this matches full JCS; non-BMP string ordering may differ
    from UTF-16 code-unit order in edge cases.
    """

    def _check_numbers(item: Any) -> None:
        if isinstance(item, float):
            if math.isnan(item) or math.isinf(item):
                raise ValueError("non-finite numbers not allowed in JCS")
        elif isinstance(item, dict):
            for val in item.values():
                _check_numbers(val)
        elif isinstance(item, list):
            for val in item:
                _check_numbers(val)

    _check_numbers(value)
    text = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return text.encode("utf-8")


def _proof_config_hash(proof: dict[str, Any]) -> bytes:
    """Hash a proof config (proof without proofValue) per vc-di-eddsa."""
    config = {key: val for key, val in proof.items() if key != "proofValue"}
    return hashlib.sha256(jcs_canonicalize(config)).digest()


def _doc_hash(doc: dict[str, Any]) -> bytes:
    """Hash a document without proof/signature per FEP-8b32."""
    clean = {
        key: val
        for key, val in doc.items()
        if key not in ("proof", "signature")
    }
    return hashlib.sha256(jcs_canonicalize(clean)).digest()


def signing_bytes(doc: dict[str, Any], proof: dict[str, Any]) -> bytes:
    """Return signing bytes: proofHash + docHash (both raw SHA-256)."""
    return _proof_config_hash(proof) + _doc_hash(doc)


def generate_integrity_proof(
    doc: dict[str, Any],
    key: Ed25519Key,
    verification_method: str | None = None,
    created: str | None = None,
    expires: str | None = None,
) -> dict[str, Any]:
    """Add an eddsa-jcs-2022 DataIntegrityProof to a document in place.

    Args:
        doc: ActivityPub object/activity to sign (modified in place)
        key: Ed25519Key with private material
        verification_method: Key URI (defaults to key.key_id())
        created: ISO8601 timestamp (defaults to now, no microseconds)
        expires: Optional ISO8601 expiry

    Returns:
        The proof dict that was added under ``doc["proof"]``.
    """
    if key.privkey is None:
        raise ValueError("Ed25519 private key required")
    method = verification_method or key.key_id()
    if created is None:
        created = (
            datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"
            if datetime.now(timezone.utc).tzinfo
            else datetime.now(timezone.utc).isoformat() + "Z"
        )
        # Normalize: datetime.now(timezone.utc) already aware; ensure Z suffix
        if created.endswith("+00:00"):
            created = created[:-6] + "Z"
    proof: dict[str, Any] = {
        "type": "DataIntegrityProof",
        "cryptosuite": "eddsa-jcs-2022",
        "verificationMethod": method,
        "proofPurpose": "assertionMethod",
        "created": created,
    }
    if expires is not None:
        proof["expires"] = expires
    to_sign = signing_bytes(doc, proof)
    signer = eddsa.new(key.privkey, "rfc8032")
    sig = signer.sign(to_sign)
    proof["proofValue"] = "z" + base58btc_encode(sig)
    doc["proof"] = proof
    return proof


def _decode_proof_value(proof_value: str) -> bytes:
    """Decode a multibase base58btc proofValue to raw signature bytes."""
    if not proof_value.startswith("z"):
        raise ValueError("only base58-btc multibase proofValue supported")
    return base58btc_decode(proof_value[1:])


def verify_integrity_proof(
    doc: dict[str, Any],
    key: Ed25519Key | ECC.EccKey | bytes,
) -> bool:
    """Verify an eddsa-jcs-2022 DataIntegrityProof with a given key.

    Args:
        doc: Document containing ``proof``
        key: Ed25519Key, raw ECC public key, or 32-byte raw public bytes

    Returns:
        True if valid, False otherwise (unsupported suite, expired,
        bad shape, bad signature).
    """
    proof = doc.get("proof")
    if not isinstance(proof, dict):
        return False
    if proof.get("type") != "DataIntegrityProof":
        return False
    if proof.get("cryptosuite") not in SUPPORTED_CRYPTOSUITES:
        return False
    if proof.get("proofPurpose") != "assertionMethod":
        return False
    if "verificationMethod" not in proof or "proofValue" not in proof:
        return False
    # Expiry check if present
    expires = proof.get("expires")
    if expires is not None:
        try:
            text = str(expires)
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            exp = datetime.fromisoformat(text)
            now = datetime.now(timezone.utc)
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < now:
                return False
        except (ValueError, TypeError):
            return False
    try:
        sig = _decode_proof_value(str(proof["proofValue"]))
    except (ValueError, KeyError):
        return False
    if len(sig) != 64:
        return False
    pubkey: ECC.EccKey | None = None
    if isinstance(key, Ed25519Key):
        pubkey = key.pubkey
        if pubkey is None and key.privkey is not None:
            pubkey = key.privkey.public_key()
    elif isinstance(key, bytes):
        if len(key) != 32:
            return False
        der = bytes.fromhex("302a300506032b6570032100") + key
        try:
            pubkey = ECC.import_key(der)
        except (ValueError, TypeError):
            return False
    else:
        pubkey = key
    if pubkey is None:
        return False
    to_verify = signing_bytes(doc, proof)
    try:
        verifier = eddsa.new(pubkey, "rfc8032")
        verifier.verify(to_verify, sig)
        return True
    except (ValueError, TypeError):
        return False


def has_integrity_proof(doc: dict[str, Any]) -> bool:
    """Check whether a document carries a DataIntegrityProof."""
    proof = doc.get("proof")
    return isinstance(proof, dict) and proof.get("type") == "DataIntegrityProof"


def multibase_sig_to_b64(proof_value: str) -> str:
    """Convert a multibase proofValue to standard base64 (for debugging)."""
    return base64.b64encode(_decode_proof_value(proof_value)).decode("ascii")
