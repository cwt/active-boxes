import base64
import hashlib
import typing
from datetime import datetime, timezone
from typing import Any

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from pyld import jsonld  # type: ignore[import-untyped]

if typing.TYPE_CHECKING:
    from .key import Key


# cache the downloaded "schemas", otherwise the library is super slow
# (https://github.com/digitalbazaar/pyld/issues/70)
_CACHE: dict[str, Any] = {}
LOADER = jsonld.requests_document_loader()


def _caching_document_loader(
    url: str, options: dict[str, Any] | None = None
) -> Any:
    opts = options if options is not None else {}
    if url in _CACHE:
        return _CACHE[url]
    resp = LOADER(url, opts)
    _CACHE[url] = resp
    return resp


jsonld.set_document_loader(_caching_document_loader)


def _options_hash(doc):
    doc = dict(doc["signature"])
    for k in ["type", "id", "signatureValue"]:
        if k in doc:
            del doc[k]
    doc["@context"] = "https://w3id.org/identity/v1"
    if normalized := jsonld.normalize(
        doc, {"algorithm": "URDNA2015", "format": "application/nquads"}
    ):
        h = hashlib.new("sha256")
        h.update(normalized.encode("utf-8"))
        return h.hexdigest()
    return ""


def _doc_hash(doc):
    doc = dict(doc)
    if "signature" in doc:
        del doc["signature"]
    if normalized := jsonld.normalize(
        doc, {"algorithm": "URDNA2015", "format": "application/nquads"}
    ):
        h = hashlib.new("sha256")
        h.update(normalized.encode("utf-8"))
        return h.hexdigest()
    return ""


def verify_signature(doc: dict[str, Any], key: "Key") -> bool:
    to_be_signed = _options_hash(doc) + _doc_hash(doc)
    signature = doc["signature"]["signatureValue"]
    signer = PKCS1_v1_5.new(key.pubkey or key.privkey)  # type: ignore
    digest = SHA256.new()
    digest.update(to_be_signed.encode("utf-8"))
    return signer.verify(digest, base64.b64decode(signature))  # type: ignore


def generate_signature(doc: dict[str, Any], key: "Key") -> None:
    options = {
        "type": "RsaSignature2017",
        "creator": doc["actor"] + "#main-key",
        "created": datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        + "Z",
    }
    doc["signature"] = options
    to_be_signed = _options_hash(doc) + _doc_hash(doc)
    if not key.privkey:
        raise ValueError(f"missing privkey on key {key!r}")

    signer = PKCS1_v1_5.new(key.privkey)
    digest = SHA256.new()
    digest.update(to_be_signed.encode("utf-8"))
    sig = base64.b64encode(signer.sign(digest))  # type: ignore
    options["signatureValue"] = sig.decode("utf-8")


def verify_embedded_signature(
    doc: dict[str, Any],
    rsa_key: Any = None,
    ed25519_key: Any = None,
) -> bool:
    """Verify embedded object signatures, preferring LD then proof.

    Matches Mastodon behaviour: try ``RsaSignature2017`` first when both
    key and ``signature`` are present, then try FEP-8b32 ``proof`` when a
    key is available. Returns False when neither verifies.

    Per FEP-8b32, ``signature`` is stripped before proof verification.
    """
    # Lazy import to avoid a hard dependency cycle at module load
    import logging

    from .data_integrity import verify_integrity_proof

    logger = logging.getLogger(__name__)
    if isinstance(doc.get("signature"), dict) and rsa_key is not None:
        try:
            if verify_signature(doc, rsa_key):
                return True
        except (ValueError, TypeError, KeyError):
            logger.debug("LD signature verification failed", exc_info=True)
    if isinstance(doc.get("proof"), dict) and ed25519_key is not None:
        try:
            return bool(verify_integrity_proof(doc, ed25519_key))
        except (ValueError, TypeError, KeyError):
            logger.debug("integrity proof verification failed", exc_info=True)
            return False
    return False


def has_embedded_signature(doc: dict[str, Any]) -> bool:
    """Check whether a document carries signature and/or proof."""
    return isinstance(doc.get("signature"), dict) or isinstance(
        doc.get("proof"), dict
    )
