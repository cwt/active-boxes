"""HTTP Signatures for ActivityPub.

This module implements HTTP Signatures (RFC draft-cavage-http-signatures)
which is required by ActivityPub for server-to-server communication.

Mastodon and other Fediverse instances won't accept unsigned requests.
"""

import asyncio
import base64
import hashlib
import logging
from datetime import datetime
from datetime import timezone
from typing import Dict, Optional, Union
from urllib.parse import urlparse

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5

from .activitypub import _has_type
from .activitypub import _await_if_coroutine
from .activitypub import get_backend
from .errors import ActivityGoneError
from .errors import ActivityNotFoundError
from .key import Key

logger = logging.getLogger(__name__)


def _run_sync(coro):
    """Run an async coroutine from sync code.

    This enables Flask/Django and other sync frameworks to use the library.
    For new code, prefer async/await syntax.

    Args:
        coro: A coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        RuntimeError: If called from within an async context
    """
    if not asyncio.iscoroutine(coro):
        return coro

    try:
        asyncio.get_running_loop()
        raise RuntimeError(
            "Cannot run async code from within an async context. "
            "Use 'await' instead of the _sync() wrapper."
        )
    except RuntimeError as e:
        if "no running event loop" in str(e):
            return asyncio.run(coro)
        raise


def _build_signed_string(
    signed_headers: str,
    method: str,
    path: str,
    headers: Dict[str, str],
    body_digest: str,
) -> str:
    """Build the string to be signed."""
    out = []
    for signed_header in signed_headers.split(" "):
        if signed_header == "(request-target)":
            out.append("(request-target): " + method.lower() + " " + path)
        elif signed_header == "digest":
            out.append("digest: " + body_digest)
        else:
            out.append(signed_header + ": " + headers.get(signed_header, ""))
    return "\n".join(out)


def _parse_sig_header(val: Optional[str]) -> Optional[Dict[str, str]]:
    """Parse the Signature header value."""
    if not val:
        return None
    out = {}
    for data in val.split(","):
        k, v = data.split("=", 1)
        out[k] = v[1 : len(v) - 1]
    return out


def _verify_h(signed_string: str, signature: bytes, pubkey) -> bool:
    """Verify a signature using a public key."""
    signer = PKCS1_v1_5.new(pubkey)
    digest = SHA256.new()
    digest.update(signed_string.encode("utf-8"))
    return signer.verify(digest, signature)


def _body_digest(body: Union[str, bytes]) -> str:
    """Compute the SHA-256 digest of a body.

    Args:
        body: The request body as string or bytes

    Returns:
        Digest header value (RFC 3230 format)
    """
    h = hashlib.sha256()
    if isinstance(body, bytes):
        h.update(body)
    else:
        h.update(body.encode("utf-8"))
    return "SHA-256=" + base64.b64encode(h.digest()).decode("utf-8")


async def _get_public_key(key_id: str) -> Key:
    """Fetch and parse a public key by key ID (async).

    Args:
        key_id: The key ID to fetch

    Returns:
        The Key object

    Raises:
        ValueError: If the key format is invalid
    """
    backend = get_backend()
    result = backend.fetch_iri(key_id)
    actor = await _await_if_coroutine(result)

    match actor:
        case {
            "type": actor_type,
            "publicKeyPem": public_key_pem,
            "owner": owner,
            "id": actor_id,
        } if _has_type(actor_type, "Key"):
            k = Key(owner, actor_id)
            k.load_pub(public_key_pem)
        case {
            "publicKey": {"id": public_key_id, "publicKeyPem": public_key_pem},
            "id": actor_id,
        }:
            k = Key(actor_id, public_key_id)
            k.load_pub(public_key_pem)
        case _:
            raise ValueError(f"unexpected actor structure: {actor!r}")

    if key_id != k.key_id():
        raise ValueError(
            f"failed to fetch requested key {key_id}: got {actor['publicKey']['id']}"
        )

    return k


def _get_public_key_sync(key_id: str) -> Key:
    """Fetch and parse a public key by key ID (sync wrapper).

    For async code, use await _get_public_key() instead.

    Args:
        key_id: The key ID to fetch

    Returns:
        The Key object
    """
    return _run_sync(_get_public_key(key_id))


async def verify_request(
    method: str, path: str, headers: Dict[str, str], body: str
) -> bool:
    """Verify an HTTP Signature on a request (async).

    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path
        headers: Request headers
        body: Request body

    Returns:
        True if the signature is valid, False otherwise
    """
    if not (hsig := _parse_sig_header(headers.get("Signature"))):
        logger.debug("no signature in header")
        return False

    signed_string = _build_signed_string(
        hsig["headers"], method, path, headers, _body_digest(body)
    )

    try:
        k = await _get_public_key(hsig["keyId"])
    except (ActivityGoneError, ActivityNotFoundError):
        logger.debug("cannot get public key")
        return False

    return _verify_h(
        signed_string, base64.b64decode(hsig["signature"]), k.pubkey
    )


def verify_request_sync(
    method: str, path: str, headers: Dict[str, str], body: str
) -> bool:
    """Verify an HTTP Signature on a request (sync wrapper).

    For async code, use await verify_request() instead.

    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path
        headers: Request headers
        body: Request body

    Returns:
        True if the signature is valid, False otherwise
    """
    return _run_sync(verify_request(method, path, headers, body))


async def sign_request(
    method: str,
    path: str,
    headers: Dict[str, str],
    key: Key,
    body: Optional[str] = None,
    host: Optional[str] = None,
) -> Dict[str, str]:
    """Sign a request with HTTP Signatures (async).

    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path
        headers: Request headers
        key: The key to sign with
        body: Optional request body
        host: Optional host header value

    Returns:
        Updated headers dict with signature
    """
    logger.info(f"keyid={key.key_id()}")

    if host is None:
        parsed = urlparse(path if "://" in path else f"http://localhost{path}")
        host = parsed.netloc

    body_digest = _body_digest(body) if body else ""

    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    headers["Digest"] = body_digest
    headers["Date"] = date
    headers["Host"] = host

    sigheaders = "(request-target) user-agent host date digest content-type"

    to_be_signed = _build_signed_string(
        sigheaders, method, path, headers, body_digest
    )
    assert key.privkey is not None, "Private key is required for signing"
    signer = PKCS1_v1_5.new(key.privkey)
    digest = SHA256.new()
    digest.update(to_be_signed.encode("utf-8"))
    sig = base64.b64encode(signer.sign(digest)).decode("utf-8")

    key_id = key.key_id()
    signature_header = f'keyId="{key_id}",algorithm="rsa-sha256",headers="{sigheaders}",signature="{sig}"'
    logger.debug(f"signature header={signature_header}")

    headers["Signature"] = signature_header
    return headers


def sign_request_sync(
    method: str,
    path: str,
    headers: Dict[str, str],
    key: Key,
    body: Optional[str] = None,
    host: Optional[str] = None,
) -> Dict[str, str]:
    """Sign a request with HTTP Signatures (sync wrapper).

    For async code, use await sign_request() instead.

    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path
        headers: Request headers
        key: The key to sign with
        body: Optional request body
        host: Optional host header value

    Returns:
        Updated headers dict with signature
    """
    return _run_sync(sign_request(method, path, headers, key, body, host))


class HTTPSigAuth:
    """HTTP Signature authentication for signing requests.

    This class provides both async and sync interfaces for signing
    outgoing requests with HTTP Signatures.
    """

    def __init__(self, key: Key) -> None:
        """Initialize with a key."""
        self.key = key

    def __call__(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None,
    ) -> Dict[str, str]:
        """Sign a request (sync interface for backwards compatibility)."""
        return sign_request_sync(method, path, headers, self.key, body)

    async def sign(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None,
    ) -> Dict[str, str]:
        """Sign a request (async interface)."""
        return await sign_request(method, path, headers, self.key, body)

    def sign_sync(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: Optional[str] = None,
    ) -> Dict[str, str]:
        """Sign a request (sync interface)."""
        return sign_request_sync(method, path, headers, self.key, body)
