import json
import logging
from unittest import mock

from active_boxes import linked_data_sig
from active_boxes.key import Key
from pyld import jsonld  # type: ignore[import-untyped]  # noqa: F401

logging.basicConfig(level=logging.DEBUG)


DOC = """{"type": "Create", "actor": "https://microblog.pub", "object": {"type": "Note", "sensitive": false, "cc": ["https://microblog.pub/followers"], "to": ["https://www.w3.org/ns/activitystreams#Public"], "content": "<p>Hello world!</p>", "tag": [], "source": {"mediaType": "text/markdown", "content": "Hello world!"}, "attributedTo": "https://microblog.pub", "published": "2018-05-21T15:51:59Z", "id": "https://microblog.pub/outbox/988179f13c78b3a7/activity", "url": "https://microblog.pub/note/988179f13c78b3a7", "replies": {"type": "OrderedCollection", "totalItems": 0, "first": "https://microblog.pub/outbox/988179f13c78b3a7/replies?page=first", "id": "https://microblog.pub/outbox/988179f13c78b3a7/replies"}, "likes": {"type": "OrderedCollection", "totalItems": 2, "first": "https://microblog.pub/outbox/988179f13c78b3a7/likes?page=first", "id": "https://microblog.pub/outbox/988179f13c78b3a7/likes"}, "shares": {"type": "OrderedCollection", "totalItems": 3, "first": "https://microblog.pub/outbox/988179f13c78b3a7/shares?page=first", "id": "https://microblog.pub/outbox/988179f13c78b3a7/shares"}}, "@context": ["https://www.w3.org/ns/activitystreams", "https://w3id.org/security/v1", {"Hashtag": "as:Hashtag", "sensitive": "as:sensitive"}], "published": "2018-05-21T15:51:59Z", "to": ["https://www.w3.org/ns/activitystreams#Public"], "cc": ["https://microblog.pub/followers"], "id": "https://microblog.pub/outbox/988179f13c78b3a7"}"""  # noqa: E501

# Mock identity context to avoid network calls
IDENTITY_CONTEXT = {
    "@context": {
        "id": "@id",
        "type": "@type",
        "cred": "https://w3id.org/credentials#",
        "dc": "http://purl.org/dc/terms/",
        "identity": "https://w3id.org/identity#",
        "perm": "https://w3id.org/permissions#",
        "ps": "https://w3id.org/payswarm#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "sec": "https://w3id.org/security#",
        "schema": "http://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "Group": "https://www.w3.org/ns/activitystreams#Group",
        "claim": {"@id": "cred:claim", "@type": "@id"},
        "credential": {"@id": "cred:credential", "@type": "@id"},
        "issued": {"@id": "cred:issued", "@type": "xsd:dateTime"},
        "issuer": {"@id": "cred:issuer", "@type": "@id"},
        "recipient": {"@id": "cred:recipient", "@type": "@id"},
        "referenceId": "cred:referenceId",
        "Identity": "identity:Identity",
        "address": {"@id": "identity:address", "@type": "@id"},
        "email": "schema:email",
        "entity": {"@id": "identity:entity", "@type": "@id"},
        "ethereumAddress": "sec:ethereumAddress",
        "expires": {"@id": "sec:expires", "@type": "xsd:dateTime"},
        "member": {"@id": "identity:member", "@type": "@id"},
        "memberOf": {"@id": "identity:memberOf", "@type": "@id"},
        "opensig": "http://opensig.net/",
        "phone": "schema:telephone",
        "permission": {"@id": "perm:permission", "@type": "@id"},
        "privateKey": {"@id": "sec:privateKey", "@container": "@index"},
        "privateKeyPem": "sec:privateKeyPem",
        "privateKeyService": {"@id": "sec:privateKeyService", "@type": "@id"},
        "privateKeyWif": "sec:privateKeyWif",
        "publicKey": {"@id": "sec:publicKey", "@container": "@index"},
        "publicKeyBase58": "sec:publicKeyBase58",
        "publicKeyPem": "sec:publicKeyPem",
        "publicKeyService": {"@id": "sec:publicKeyService", "@type": "@id"},
        "publicKeyWif": "sec:publicKeyWif",
        "signature": {"@id": "sec:signature", "@type": "@id"},
        "BitcoinAddress": "sec:BitcoinAddress",
        "BitcoinSignature2016": "sec:BitcoinSignature2016",
        "CryptographicKey": "sec:Key",
        "Ed25519Signature2018": "sec:Ed25519Signature2018",
        "EncryptedMessage": "sec:EncryptedMessage",
        "GraphSignature2012": "sec:GraphSignature2012",
        "LinkedDataSignature2015": "sec:LinkedDataSignature2015",
        "LinkedDataSignature2016": "sec:LinkedDataSignature2016",
        "CryptographicKeyCredential": "sec:KeyCredential",
        "AuthenticationCredential": "sec:AuthenticationCredential",
        "RsaCryptographicKey": "sec:RsaCryptographicKey",
        "RsaSignatureAuthentication2018": "sec:RsaSignatureAuthentication2018",
        "RsaSignature2015": "sec:RsaSignature2015",
        "Sha256CryptographicKey": "sec:Sha256CryptographicKey",
        "Sha256Signature2018": "sec:Sha256Signature2018",
        "capability": {"@id": "perm:capability", "@type": "@id"},
        "capabilityAction": "perm:capabilityAction",
        "capabilityChain": {
            "@id": "perm:capabilityChain",
            "@type": "@id",
            "@container": "@list",
        },
        "delegator": {"@id": "perm:delegator", "@type": "@id"},
        "invoker": {"@id": "perm:invoker", "@type": "@id"},
        "caveat": {"@id": "perm:caveat", "@type": "@id", "@container": "@list"},
    }
}


@mock.patch("active_boxes.linked_data_sig._caching_document_loader")
def test_linked_data_sig(mock_loader):
    # Mock the document loader to return a local context instead of making network calls
    mock_loader.return_value = {
        "contentType": "application/ld+json",
        "contextUrl": None,
        "documentUrl": "https://w3id.org/identity/v1",
        "document": IDENTITY_CONTEXT,
    }

    # Also mock jsonld.load_document to avoid network calls
    with mock.patch("pyld.jsonld.load_document") as mock_load_document:
        mock_load_document.return_value = {
            "contentType": "application/ld+json",
            "contextUrl": None,
            "documentUrl": "https://w3id.org/identity/v1",
            "document": IDENTITY_CONTEXT,
        }

        doc = json.loads(DOC)

        k = Key("https://lol.com")
        k.new()

        linked_data_sig.generate_signature(doc, k)
        assert linked_data_sig.verify_signature(doc, k)
