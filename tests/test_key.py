from active_boxes.key import Ed25519Key, Key, base58btc_decode, base58btc_encode


def test_key_new_load():
    owner = "http://lol.com"
    k = Key(owner)
    k.new()

    assert k.to_dict() == {
        "id": f"{owner}#main-key",
        "owner": owner,
        "publicKeyPem": k.pubkey_pem,
        "type": "Key",
    }

    k2 = Key(owner)
    k2.load(k.privkey_pem)

    assert k2.to_dict() == k.to_dict()


def test_base58btc_roundtrip():
    data = b"\xed\x01" + bytes(range(32))
    assert base58btc_decode(base58btc_encode(data)) == data
    assert base58btc_encode(b"\x00\x00abc").startswith("11")


def test_ed25519_new_and_multikey():
    owner = "https://example.com/users/alice"
    key = Ed25519Key(owner)
    key.new()
    assert len(key.pub_raw()) == 32
    multikey = key.to_multikey()
    assert multikey["type"] == "Multikey"
    assert multikey["controller"] == owner
    assert multikey["publicKeyMultibase"].startswith("z")
    restored = Ed25519Key.from_multikey(multikey)
    assert restored.pub_raw() == key.pub_raw()
    assert restored.key_id() == key.key_id()


def test_ed25519_pem_roundtrip():
    owner = "https://example.com/users/bob"
    key = Ed25519Key(owner)
    key.new()
    assert key.privkey_pem is not None
    other = Ed25519Key(owner, key.key_id())
    other.load_priv_pem(key.privkey_pem)
    assert other.pub_raw() == key.pub_raw()
