"""HTTP Signatures for ActivityPub.

This module implements both generations of HTTP signatures required for
federation:

- draft-cavage-http-signatures-12 (legacy, still required for Mastodon <4.5
  and many fediverse implementations) with ``rsa-sha256``.
- RFC 9421 HTTP Message Signatures (preferred by Mastodon 4.5+, Misskey,
  Fedify) with ``rsa-v1_5-sha256`` and ``ed25519``.

Inbound verification tries RFC 9421 first when ``Signature-Input`` is
present, then falls back to cavage. Outbound callers should try RFC 9421
first and retry with cavage on HTTP 400/401 (double-knock), matching
Mastodon 4.7 behaviour.

Mastodon and other Fediverse instances won't accept unsigned requests.
"""

import base64
import hashlib
import hmac
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, cast
from urllib.parse import urlparse

from Crypto.Hash import SHA256
from Crypto.PublicKey import ECC
from Crypto.Signature import PKCS1_v1_5, eddsa

from ._sync import _run_sync
from .activitypub import _await_if_coroutine, _has_type, get_backend
from .errors import ActivityGoneError, ActivityNotFoundError
from .key import Ed25519Key, Key

logger = logging.getLogger(__name__)


def _build_signed_string(
    signed_headers: str,
    method: str,
    path: str,
    headers: dict[str, str],
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
            # Case-insensitive: real HTTP headers arrive capitalized
            # ("User-Agent") while the signed names are lowercase.
            out.append(signed_header + ": " + (get_header(headers, signed_header) or ""))
    return "\n".join(out)


def _parse_sig_header(val: str | None) -> dict[str, str] | None:
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


def _body_digest(body: str | bytes) -> str:
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


def _body_bytes(body: str | bytes | None) -> bytes:
    """Normalize a body to bytes."""
    if body is None:
        return b""
    if isinstance(body, bytes):
        return body
    return body.encode("utf-8")


def compute_content_digest(body: str | bytes) -> str:
    """Compute an RFC 9530 Content-Digest header value.

    Args:
        body: The request body as string or bytes

    Returns:
        Content-Digest value, e.g. ``sha-256=:abc...=:``
    """
    digest = hashlib.sha256(_body_bytes(body)).digest()
    b64 = base64.b64encode(digest).decode("ascii")
    return f"sha-256=:{b64}:"


def parse_content_digest(value: str | None) -> dict[str, str]:
    """Parse an RFC 9530 Content-Digest header into ``{alg: b64}``."""
    out: dict[str, str] = {}
    if not value:
        return out
    # Dictionary style: sha-256=:abc=:, sha-512=:def=:
    for item in value.split(","):
        item = item.strip()
        match = re.match(r"^([a-z0-9-]+)=:([A-Za-z0-9+/=]+):$", item)
        if match:
            out[match.group(1).lower()] = match.group(2)
    return out


def verify_content_digest(
    body: str | bytes | None, header_value: str | None
) -> bool:
    """Verify that a body matches an RFC 9530 Content-Digest header."""
    if not header_value:
        return False
    parsed = parse_content_digest(header_value)
    raw = _body_bytes(body)
    for alg, b64 in parsed.items():
        if alg == "sha-256":
            expected = base64.b64encode(hashlib.sha256(raw).digest()).decode(
                "ascii"
            )
            if hmac.compare_digest(expected, b64):
                return True
        elif alg == "sha-512":
            expected = base64.b64encode(hashlib.sha512(raw).digest()).decode(
                "ascii"
            )
            if hmac.compare_digest(expected, b64):
                return True
    return False


def verify_digest_header(
    body: str | bytes | None, header_value: str | None
) -> bool:
    """Verify a legacy RFC 3230 Digest header (``SHA-256=...``)."""
    if not header_value:
        return False
    # Allow "SHA-256=..." or "sha-256=..." with optional whitespace
    candidate = header_value.strip()
    expected = _body_digest(_body_bytes(body))
    if hmac.compare_digest(expected.lower(), candidate.lower()):
        return True
    # Some servers send bare base64 without prefix; accept it too
    try:
        raw = _body_bytes(body)
        exp_b64 = base64.b64encode(hashlib.sha256(raw).digest()).decode()
        if hmac.compare_digest(exp_b64, candidate):
            return True
    except (ValueError, TypeError):
        return False
    return False


def get_header(headers: dict[str, str], name: str) -> str | None:
    """Case-insensitive header lookup."""
    lowered = name.lower()
    for key, value in headers.items():
        if key.lower() == lowered:
            return value
    return None


def parse_signature_input(
    value: str | None,
) -> dict[str, dict[str, Any]] | None:
    """Parse an RFC 9421 Signature-Input header.

    Returns a mapping of ``label -> {covered, created, expires, keyid,
    alg, raw_params}`` or None if unparsable.
    """
    if not value:
        return None
    out: dict[str, dict[str, Any]] = {}
    # Split on commas not inside quotes or parens. Mastodon only sends one
    # signature, so a careful split is enough.
    parts: list[str] = []
    current = ""
    depth = 0
    in_quotes = False
    for char in value:
        if char == '"' and current[-1:] != "\\":
            in_quotes = not in_quotes
            current += char
        elif not in_quotes and char == "(":
            depth += 1
            current += char
        elif not in_quotes and char == ")":
            depth = max(0, depth - 1)
            current += char
        elif not in_quotes and depth == 0 and char == ",":
            parts.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        parts.append(current.strip())
    for part in parts:
        match = re.match(r"^([A-Za-z0-9-_]+)=\(([^)]*)\)(.*)$", part, re.DOTALL)
        if not match:
            continue
        label = match.group(1)
        covered_raw = match.group(2).strip()
        params_raw = match.group(3).strip()
        covered: list[str] = re.findall(r'"([^"]+)"', covered_raw)
        params: dict[str, Any] = {}
        for param in re.finditer(
            r";\s*([a-z0-9]+)=(\"([^\"]*)\"|([0-9]+))", params_raw
        ):
            key = param.group(1)
            if param.group(3) is not None:
                params[key] = param.group(3)
            else:
                try:
                    params[key] = int(param.group(4))
                except ValueError:
                    params[key] = param.group(4)
        params["covered"] = covered
        params["raw_params"] = params_raw
        out[label] = params
    return out or None


def parse_rfc9421_signature(value: str | None) -> dict[str, str] | None:
    """Parse an RFC 9421 Signature header into ``{label: b64}``."""
    if not value:
        return None
    out: dict[str, str] = {}
    for match in re.finditer(r"([A-Za-z0-9-_]+)=:([A-Za-z0-9+/=]+):", value):
        out[match.group(1)] = match.group(2)
    return out or None


def verify_created(created: Any, max_age_seconds: int = 43200) -> bool:
    """Verify an RFC 9421 ``created`` timestamp (default 12h, like Mastodon)."""
    if created is None:
        return False
    try:
        created_ts = int(created)
    except (TypeError, ValueError):
        return False
    now = int(time.time())
    # Allow small clock skew into the future
    if created_ts > now + 60:
        return False
    return (now - created_ts) <= max_age_seconds


def _rfc9421_component_value(
    component: str,
    method: str,
    target_uri: str,
    headers: dict[str, str],
) -> str | None:
    """Resolve a single RFC 9421 covered component value."""
    comp = component.lower()
    parsed = urlparse(target_uri)
    lowered_headers = {key.lower(): val.strip() for key, val in headers.items()}
    if comp == "@method":
        return method.upper()
    if comp == "@target-uri":
        return target_uri
    if comp == "@authority":
        return parsed.netloc.lower()
    if comp == "@scheme":
        return parsed.scheme.lower()
    if comp == "@path":
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        return path
    if comp == "@query":
        return "?" + parsed.query if parsed.query else ""
    if comp.startswith("@"):
        # Unsupported derived component
        return None
    return lowered_headers.get(comp)


def build_rfc9421_signature_base(
    method: str,
    target_uri: str,
    headers: dict[str, str],
    covered: list[str],
    params_raw: str,
) -> str | None:
    """Build the RFC 9421 signature base string."""
    lines: list[str] = []
    for component in covered:
        value = _rfc9421_component_value(component, method, target_uri, headers)
        if value is None:
            return None
        lines.append(f'"{component.lower()}": {value}')
    # params_raw includes leading ';' e.g. ;created=...;keyid="..."
    lines.append(f'"@signature-params": ({_quote_list(covered)}){params_raw}')
    return "\n".join(lines)


def _quote_list(items: list[str]) -> str:
    """Serialize a covered-component list, e.g. '"a" "b"'."""
    return " ".join(f'"{item.lower()}"' for item in items)


def _sign_bytes_rsa(privkey: Any, data: bytes) -> bytes:
    """Sign bytes with RSA PKCS1v1.5 + SHA-256."""
    signer = PKCS1_v1_5.new(privkey)
    digest = SHA256.new(data)
    return signer.sign(digest)


def _verify_bytes_rsa(pubkey: Any, data: bytes, signature: bytes) -> bool:
    """Verify RSA PKCS1v1.5 + SHA-256 signature."""
    try:
        verifier = PKCS1_v1_5.new(pubkey)
        digest = SHA256.new(data)
        return bool(verifier.verify(digest, signature))
    except (ValueError, TypeError):
        return False


def _sign_bytes_ed25519(privkey: ECC.EccKey, data: bytes) -> bytes:
    """Sign bytes with Ed25519 (RFC 8032)."""
    signer = eddsa.new(privkey, "rfc8032")
    return signer.sign(data)


def _verify_bytes_ed25519(pubkey: ECC.EccKey, data: bytes, sig: bytes) -> bool:
    """Verify Ed25519 signature."""
    try:
        verifier = eddsa.new(pubkey, "rfc8032")
        verifier.verify(data, sig)
        return True
    except (ValueError, TypeError):
        return False


async def _get_public_key(key_id: str) -> Key:
    """Fetch and parse an RSA public key by key ID (async).

    Kept for backwards compatibility. For new code prefer
    :func:`get_verification_key` which also supports Ed25519/Multikey.

    Args:
        key_id: The key ID to fetch

    Returns:
        The Key object

    Raises:
        ValueError: If the key format is invalid
    """
    key, kind = await get_verification_key(key_id)
    if kind != "rsa":
        raise ValueError(f"key {key_id} is not an RSA key")
    assert isinstance(key, Key)
    return key


def _get_public_key_sync(key_id: str) -> Key:
    """Fetch and parse a public key by key ID (sync wrapper).

    For async code, use await _get_public_key() instead.

    Args:
        key_id: The key ID to fetch

    Returns:
        The Key object
    """
    return _run_sync(_get_public_key(key_id))


def _match_multikey_entry(entries: Any, key_id: str) -> dict[str, Any] | None:
    """Find a Multikey entry with matching id in assertionMethod/other lists."""
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        return None
    for entry in entries:
        if isinstance(entry, dict) and entry.get("id") == key_id:
            return entry
    return None


async def get_verification_key(
    key_id: str,
) -> tuple[Key | Ed25519Key, str]:
    """Fetch a verification key by key ID, supporting RSA and Ed25519.

    Supports legacy ``publicKey.publicKeyPem``, bare ``Key`` objects, and
    FEP-521a ``Multikey`` entries in ``assertionMethod``.

    Returns:
        Tuple of ``(key_object, kind)`` where kind is ``"rsa"`` or
        ``"ed25519"``.
    """
    backend = get_backend()
    result = backend.fetch_iri(key_id)
    actor = await _await_if_coroutine(result)

    if not isinstance(actor, dict):
        raise TypeError(f"unexpected actor structure: {actor!r}")

    # Direct Multikey document (fragment resolution returned the key itself)
    if actor.get("type") == "Multikey" and "publicKeyMultibase" in actor:
        ed_key = Ed25519Key.from_multikey(actor)
        return ed_key, "ed25519"

    # Bare Key object with publicKeyPem
    actor_type = actor.get("type")
    if actor_type is not None and _has_type(actor_type, "Key"):
        public_key_pem = actor.get("publicKeyPem")
        owner = actor.get("owner")
        actor_id = actor.get("id")
        if public_key_pem and owner and actor_id:
            rsa_key = Key(owner, actor_id)
            rsa_key.load_pub(public_key_pem)
            if key_id != rsa_key.key_id():
                raise ValueError(f"key id mismatch for {key_id}")
            return rsa_key, "rsa"

    # FEP-521a: look in assertionMethod first (preferred for Ed25519)
    for field in ("assertionMethod", "publicKey"):
        entries = actor.get(field)
        entry = _match_multikey_entry(entries, key_id)
        if entry is None:
            continue
        if entry.get("type") == "Multikey" and "publicKeyMultibase" in entry:
            return Ed25519Key.from_multikey(entry), "ed25519"
        if "publicKeyPem" in entry:
            owner = entry.get("owner") or actor.get("id", "")
            rsa_key = Key(owner, entry.get("id", key_id))
            rsa_key.load_pub(entry["publicKeyPem"])
            return rsa_key, "rsa"

    # Legacy publicKey object
    public_key = actor.get("publicKey")
    if isinstance(public_key, dict):
        public_key_id = public_key.get("id")
        public_key_pem = public_key.get("publicKeyPem")
        actor_id = actor.get("id", "")
        if public_key_pem and public_key_id:
            rsa_key = Key(actor_id, public_key_id)
            rsa_key.load_pub(public_key_pem)
            if key_id != rsa_key.key_id():
                raise ValueError(f"key id mismatch for {key_id}")
            return rsa_key, "rsa"

    raise ValueError(f"unexpected actor structure: {actor!r}")


def get_verification_key_sync(
    key_id: str,
) -> tuple[Key | Ed25519Key, str]:
    """Sync wrapper for :func:`get_verification_key`."""
    return _run_sync(get_verification_key(key_id))


def _target_uri_from_path(path: str, headers: dict[str, str]) -> str:
    """Reconstruct a full target URI from path + Host header."""
    if "://" in path:
        return path
    host = get_header(headers, "host") or "localhost"
    # Prefer https for federation; fall back to path as-is if no host
    if not path.startswith("/"):
        path = "/" + path
    scheme = "https"
    return f"{scheme}://{host}{path}"


async def verify_request_cavage(
    method: str, path: str, headers: dict[str, str], body: str
) -> bool:
    """Verify a draft-cavage HTTP Signature (async)."""
    sig_header = get_header(headers, "signature")
    if not (hsig := _parse_sig_header(sig_header)):
        logger.debug("no cavage signature in header")
        return False
    if "keyId" not in hsig or "signature" not in hsig or "headers" not in hsig:
        return False
    signed_string = _build_signed_string(
        hsig["headers"], method, path, headers, _body_digest(body)
    )
    try:
        key, kind = await get_verification_key(hsig["keyId"])
    except (ActivityGoneError, ActivityNotFoundError, ValueError, TypeError):
        logger.debug("cannot get public key")
        return False
    if kind != "rsa":
        return False
    rsa_key = cast(Key, key)
    try:
        return _verify_h(
            signed_string, base64.b64decode(hsig["signature"]), rsa_key.pubkey
        )
    except (ValueError, TypeError):
        return False


async def verify_request_rfc9421(
    method: str,
    url: str,
    headers: dict[str, str],
    body: str | bytes | None,
    max_age_seconds: int = 43200,
) -> bool:
    """Verify an RFC 9421 HTTP Message Signature (async).

    Requires ``Signature-Input`` + ``Signature`` headers, ``@method``,
    ``@target-uri`` and ``content-digest`` coverage, and a fresh ``created``.

    Args:
        method: HTTP method, e.g. ``POST``
        url: Full target URI, e.g. ``https://example.com/inbox``
        headers: Request headers (case-insensitive)
        body: Request body
        max_age_seconds: Max age for ``created`` (default 12h, Mastodon-style)

    Returns:
        True if valid, False otherwise.
    """
    sig_input = parse_signature_input(get_header(headers, "signature-input"))
    sigs = parse_rfc9421_signature(get_header(headers, "signature"))
    if not sig_input or not sigs:
        return False
    # Mastodon supports only a single signature
    label = next(iter(sig_input))
    params = sig_input[label]
    covered = params.get("covered", [])
    # Enforce Mastodon minimal coverage
    lowered_covered = [item.lower() for item in covered]
    if "@method" not in lowered_covered or "@target-uri" not in lowered_covered:
        return False
    if "content-digest" not in lowered_covered:
        return False
    created = params.get("created")
    if created is None or not verify_created(created, max_age_seconds):
        logger.debug("rfc9421: missing or stale created")
        return False
    key_id = params.get("keyid")
    if not key_id:
        return False
    # Content-Digest must match the body
    content_digest = get_header(headers, "content-digest")
    if not verify_content_digest(body, content_digest):
        logger.debug("rfc9421: content-digest mismatch")
        return False
    if label not in sigs:
        return False
    try:
        signature = base64.b64decode(sigs[label])
    except (ValueError, TypeError):
        return False
    base = build_rfc9421_signature_base(
        method, url, headers, covered, params.get("raw_params", "")
    )
    if base is None:
        return False
    alg = str(params.get("alg", "")).lower()
    try:
        key, kind = await get_verification_key(key_id)
    except (ActivityGoneError, ActivityNotFoundError, ValueError, TypeError):
        return False
    data = base.encode("ascii")
    if kind == "rsa":
        if alg and alg not in ("rsa-v1_5-sha256", "rsa-sha256"):
            return False
        rsa_key = cast(Key, key)
        return _verify_bytes_rsa(rsa_key.pubkey, data, signature)
    if kind == "ed25519":
        if alg and alg not in ("ed25519", "ed25519-sha512", ""):
            return False
        ed_key = cast(Ed25519Key, key)
        if ed_key.pubkey is None:
            return False
        return _verify_bytes_ed25519(ed_key.pubkey, data, signature)
    return False


def verify_request_rfc9421_sync(
    method: str,
    url: str,
    headers: dict[str, str],
    body: str | bytes | None,
    max_age_seconds: int = 43200,
) -> bool:
    """Sync wrapper for :func:`verify_request_rfc9421`."""
    return _run_sync(
        verify_request_rfc9421(method, url, headers, body, max_age_seconds)
    )


async def verify_request(
    method: str, path: str, headers: dict[str, str], body: str
) -> bool:
    """Verify an HTTP Signature on a request (async).

    Tries RFC 9421 first when ``Signature-Input`` is present, then falls
    back to draft-cavage. ``path`` may be a full URL or an origin-form path;
    the target URI is reconstructed from the Host header when needed.

    Args:
        method: HTTP method (e.g., "GET", "POST")
        path: Request path or full URL
        headers: Request headers
        body: Request body

    Returns:
        True if the signature is valid, False otherwise
    """
    if get_header(headers, "signature-input") is not None:
        target = path if "://" in path else _target_uri_from_path(path, headers)
        if await verify_request_rfc9421(method, target, headers, body):
            return True
        # Fall through to cavage for hybrid senders
    return await verify_request_cavage(method, path, headers, body)


def verify_request_sync(
    method: str, path: str, headers: dict[str, str], body: str
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
    headers: dict[str, str],
    key: Key,
    body: str | None = None,
    host: str | None = None,
) -> dict[str, str]:
    """Sign a request with draft-cavage HTTP Signatures (async).

    Sets both ``Digest`` (RFC 3230) and ``Content-Digest`` (RFC 9530) so
    receivers on either stack can validate the body.

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

    raw_body = _body_bytes(body) if body is not None else b""
    body_digest = _body_digest(raw_body) if body else ""
    content_digest = compute_content_digest(raw_body) if body else ""

    date = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")

    if body:
        headers["Digest"] = body_digest
        headers["Content-Digest"] = content_digest
    headers["Date"] = date
    headers["Host"] = host

    sigheaders = "(request-target) user-agent host date digest content-type"

    to_be_signed = _build_signed_string(
        sigheaders, method, path, headers, body_digest
    )
    assert key.privkey is not None, "Private key is required for signing"
    sig_bytes = _sign_bytes_rsa(key.privkey, to_be_signed.encode("utf-8"))
    sig = base64.b64encode(sig_bytes).decode("utf-8")

    key_id = key.key_id()
    signature_header = (
        f'keyId="{key_id}",algorithm="rsa-sha256",'
        f'headers="{sigheaders}",signature="{sig}"'
    )
    logger.debug(f"signature header={signature_header}")

    headers["Signature"] = signature_header
    return headers


def sign_request_sync(
    method: str,
    path: str,
    headers: dict[str, str],
    key: Key,
    body: str | None = None,
    host: str | None = None,
) -> dict[str, str]:
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


async def sign_request_rfc9421(
    method: str,
    url: str,
    headers: dict[str, str],
    key: Key | Ed25519Key,
    body: str | bytes | None = None,
    created: int | None = None,
    label: str = "sig1",
    covered: list[str] | None = None,
) -> dict[str, str]:
    """Sign a request with RFC 9421 HTTP Message Signatures (async).

    Covers ``@method``, ``@target-uri`` and ``content-digest`` by default,
    matching Mastodon's minimal requirements.

    Args:
        method: HTTP method, e.g. ``POST``
        url: Full target URI, e.g. ``https://example.com/inbox``
        headers: Request headers to update (case preserved)
        key: RSA :class:`Key` or :class:`Ed25519Key` with private material
        body: Request body (use ``b""``/``""``/None for empty)
        created: Unix timestamp for ``created`` (defaults to now)
        label: Signature label (default ``sig1``)
        covered: Covered components (default method/target-uri/content-digest)

    Returns:
        Updated headers dict with ``Content-Digest``, ``Signature-Input``
        and ``Signature``.
    """
    if covered is None:
        covered = ["@method", "@target-uri", "content-digest"]
        # Only include content-digest when there is a body; Mastodon
        # requires it for POST. For empty GET, sign method + target only
        # unless caller explicitly passes covered.
        if body is None or _body_bytes(body) == b"":
            covered = ["@method", "@target-uri"]
    raw_body = _body_bytes(body)
    if raw_body:
        content_digest = compute_content_digest(raw_body)
        headers["Content-Digest"] = content_digest
        # Also set legacy Digest for hybrid receivers
        headers["Digest"] = _body_digest(raw_body)
    if created is None:
        created = int(time.time())
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"url must be absolute for RFC9421: {url!r}")
    # Ensure Host header is present for derived @authority checks
    if get_header(headers, "host") is None:
        headers["Host"] = parsed.netloc
    key_id = key.key_id()
    if isinstance(key, Ed25519Key):
        alg = "ed25519"
        if key.privkey is None:
            raise ValueError("Ed25519 private key required for signing")
        params_raw = f';created={created};keyid="{key_id}";alg="{alg}"'
        base = build_rfc9421_signature_base(
            method, url, headers, covered, params_raw
        )
        if base is None:
            raise ValueError("unsupported covered component")
        sig_bytes = _sign_bytes_ed25519(key.privkey, base.encode("ascii"))
    else:
        alg = "rsa-v1_5-sha256"
        if key.privkey is None:
            raise ValueError("RSA private key required for signing")
        params_raw = f';created={created};keyid="{key_id}";alg="{alg}"'
        base = build_rfc9421_signature_base(
            method, url, headers, covered, params_raw
        )
        if base is None:
            raise ValueError("unsupported covered component")
        sig_bytes = _sign_bytes_rsa(key.privkey, base.encode("ascii"))
    sig_b64 = base64.b64encode(sig_bytes).decode("ascii")
    covered_serialized = _quote_list(covered)
    headers["Signature-Input"] = f"{label}=({covered_serialized}){params_raw}"
    headers["Signature"] = f"{label}=:{sig_b64}:"
    logger.debug(f"rfc9421 Signature-Input={headers['Signature-Input']}")
    return headers


def sign_request_rfc9421_sync(
    method: str,
    url: str,
    headers: dict[str, str],
    key: Key | Ed25519Key,
    body: str | bytes | None = None,
    created: int | None = None,
    label: str = "sig1",
    covered: list[str] | None = None,
) -> dict[str, str]:
    """Sync wrapper for :func:`sign_request_rfc9421`."""
    return _run_sync(
        sign_request_rfc9421(
            method, url, headers, key, body, created, label, covered
        )
    )


class HTTPSigAuth:
    """HTTP Signature authentication for signing requests.

    Defaults to draft-cavage for backwards compatibility. Pass
    ``mode="rfc9421"`` with a full URL to use RFC 9421.
    """

    def __init__(self, key: Key | Ed25519Key, mode: str = "cavage") -> None:
        """Initialize with a key and default mode."""
        self.key = key
        self.mode = mode

    def __call__(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: str | None = None,
    ) -> dict[str, str]:
        """Sign a request (sync interface for backwards compatibility)."""
        if self.mode == "rfc9421":
            if "://" not in path:
                raise ValueError("rfc9421 mode requires a full URL as path")
            return sign_request_rfc9421_sync(
                method, path, headers, self.key, body
            )
        assert isinstance(self.key, Key)
        return sign_request_sync(method, path, headers, self.key, body)

    async def sign(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: str | None = None,
    ) -> dict[str, str]:
        """Sign a request (async interface)."""
        if self.mode == "rfc9421":
            if "://" not in path:
                raise ValueError("rfc9421 mode requires a full URL as path")
            return await sign_request_rfc9421(
                method, path, headers, self.key, body
            )
        assert isinstance(self.key, Key)
        return await sign_request(method, path, headers, self.key, body)

    def sign_sync(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: str | None = None,
    ) -> dict[str, str]:
        """Sign a request (sync interface)."""
        return self.__call__(method, path, headers, body)
