import base64
from typing import Any

from Crypto.PublicKey import ECC, RSA
from Crypto.Util import number

# FEP-521a / Multicodec prefixes
ED25519_MULTICODEC_PREFIX = b"\xed\x01"

_B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58btc_encode(data: bytes) -> str:
    """Encode bytes with base58-btc (Bitcoin alphabet)."""
    num = int.from_bytes(data, "big")
    encoded = ""
    while num > 0:
        num, rem = divmod(num, 58)
        encoded = _B58_ALPHABET[rem] + encoded
    # Preserve leading zero bytes as '1'
    pad = 0
    for byte in data:
        if byte == 0:
            pad += 1
        else:
            break
    return "1" * pad + (encoded or "")


def base58btc_decode(data: str) -> bytes:
    """Decode base58-btc string to bytes."""
    num = 0
    for char in data:
        num = num * 58 + _B58_ALPHABET.index(char)
    full = num.to_bytes((num.bit_length() + 7) // 8, "big") if num else b""
    pad = 0
    for char in data:
        if char == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + full


class Key:
    DEFAULT_KEY_SIZE = 2048

    def __init__(self, owner: str, id_: str | None = None) -> None:
        self.owner = owner
        self.privkey_pem: str | None = None
        self.pubkey_pem: str | None = None
        self.privkey: RSA.RsaKey | None = None
        self.pubkey: RSA.RsaKey | None = None
        self.id_ = id_

    def load_pub(self, pubkey_pem: str) -> None:
        self.pubkey_pem = pubkey_pem
        self.pubkey = RSA.importKey(pubkey_pem)

    def load(self, privkey_pem: str) -> None:
        self.privkey_pem = privkey_pem
        self.privkey = RSA.importKey(self.privkey_pem)
        self.pubkey_pem = (
            self.privkey.publickey().exportKey("PEM").decode("utf-8")
        )

    def new(self) -> None:
        k = RSA.generate(self.DEFAULT_KEY_SIZE)
        self.privkey_pem = k.exportKey("PEM").decode("utf-8")
        self.pubkey_pem = k.publickey().exportKey("PEM").decode("utf-8")
        self.privkey = k

    def key_id(self) -> str:
        return self.id_ or f"{self.owner}#main-key"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.key_id(),
            "owner": self.owner,
            "publicKeyPem": self.pubkey_pem,
            "type": "Key",
        }

    @classmethod
    def from_dict(cls, data):
        try:
            if k := cls(data["owner"], data["id"]):
                k.load_pub(data["publicKeyPem"])
        except KeyError:
            raise ValueError(f"bad key data {data!r}")
        return k

    def to_magic_key(self) -> str:
        mod = base64.urlsafe_b64encode(
            number.long_to_bytes(self.privkey.n)  # type: ignore
        ).decode("utf-8")
        pubexp = base64.urlsafe_b64encode(
            number.long_to_bytes(self.privkey.e)  # type: ignore
        ).decode("utf-8")
        return f"data:application/magic-public-key,RSA.{mod}.{pubexp}"


class Ed25519Key:
    """Ed25519 key for RFC9421 and FEP-8b32 / FEP-521a.

    Backed by pycryptodome ECC. Private material is stored as PKCS8 PEM,
    public material can be exported as PEM or as FEP-521a Multikey.
    """

    def __init__(self, owner: str, id_: str | None = None) -> None:
        self.owner = owner
        self.id_ = id_
        self.privkey_pem: str | None = None
        self.pubkey_pem: str | None = None
        self.privkey: ECC.EccKey | None = None
        self.pubkey: ECC.EccKey | None = None

    def new(self) -> None:
        """Generate a fresh Ed25519 keypair."""
        k = ECC.generate(curve="ed25519")
        self.privkey = k
        self.pubkey = k.public_key()
        self.privkey_pem = k.export_key(format="PEM")
        self.pubkey_pem = self.pubkey.export_key(format="PEM")

    def load_priv_pem(self, privkey_pem: str) -> None:
        """Load a PKCS8 PEM private key."""
        k = ECC.import_key(privkey_pem)
        self.privkey = k
        self.pubkey = k.public_key()
        self.privkey_pem = privkey_pem
        pub = self.pubkey.export_key(format="PEM")
        self.pubkey_pem = pub if isinstance(pub, str) else pub.decode()

    def load_pub_pem(self, pubkey_pem: str) -> None:
        """Load a SubjectPublicKeyInfo PEM public key."""
        k = ECC.import_key(pubkey_pem)
        self.pubkey = k
        self.pubkey_pem = pubkey_pem

    def load_pub_raw(self, raw_32: bytes) -> None:
        """Load a 32-byte raw Ed25519 public key."""
        if len(raw_32) != 32:
            raise ValueError("Ed25519 public key must be 32 bytes")
        der = bytes.fromhex("302a300506032b6570032100") + raw_pub_32(raw_32)
        k = ECC.import_key(der)
        self.pubkey = k
        pub = k.export_key(format="PEM")
        self.pubkey_pem = pub if isinstance(pub, str) else pub.decode()

    def pub_raw(self) -> bytes:
        """Return 32-byte raw public key."""
        if self.pubkey is None and self.privkey is not None:
            self.pubkey = self.privkey.public_key()
        if self.pubkey is None:
            raise ValueError("no public key loaded")
        raw = self.pubkey.export_key(format="raw")
        assert isinstance(raw, bytes) and len(raw) == 32
        return raw

    def key_id(self) -> str:
        return self.id_ or f"{self.owner}#ed25519-key"

    def to_multikey(self, key_id: str | None = None) -> dict[str, Any]:
        """Export as FEP-521a Multikey dict."""
        kid = key_id or self.key_id()
        multibase = "z" + base58btc_encode(
            ED25519_MULTICODEC_PREFIX + self.pub_raw()
        )
        return {
            "id": kid,
            "type": "Multikey",
            "controller": self.owner,
            "publicKeyMultibase": multibase,
        }

    @classmethod
    def from_multikey(cls, data: dict[str, Any]) -> "Ed25519Key":
        """Import from FEP-521a Multikey dict."""
        try:
            multibase = data["publicKeyMultibase"]
            controller = data["controller"]
            key_id = data["id"]
        except KeyError as exc:
            raise ValueError(f"bad multikey data {data!r}: {exc}")
        if not multibase.startswith("z"):
            raise ValueError("only base58-btc multibase supported")
        raw = base58btc_decode(multibase[1:])
        if not raw.startswith(ED25519_MULTICODEC_PREFIX):
            raise ValueError("not an Ed25519 multikey")
        k = cls(controller, key_id)
        k.load_pub_raw(raw[2:])
        return k


def raw_pub_32(raw: bytes) -> bytes:
    """Validate a 32-byte raw public key."""
    if len(raw) != 32:
        raise ValueError("Ed25519 public key must be 32 bytes")
    return raw


def parse_multikey(data: dict[str, Any]) -> Ed25519Key:
    """Parse a FEP-521a Multikey dict into an Ed25519Key."""
    return Ed25519Key.from_multikey(data)
