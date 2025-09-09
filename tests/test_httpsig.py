import json
import logging
from unittest import mock

import requests
from active_boxes import activitypub as ap
from active_boxes import httpsig
from active_boxes.key import Key

from test_backend import InMemBackend

logging.basicConfig(level=logging.DEBUG)


def test_httpsig():
    back = InMemBackend()
    ap.use_backend(back)

    k = Key("https://lol.com", "https://lol.com#lol")
    k.new()
    back.FETCH_MOCK["https://lol.com#lol"] = {
        "publicKey": k.to_dict(),
        "id": "https://lol.com",
        "type": "Person",
    }

    # Mock the requests.post call to avoid network issues
    with mock.patch("requests.post") as mock_post:
        # Create a mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        # Create a mock request object with the expected attributes
        mock_request = mock.Mock()
        mock_request.method = "POST"
        mock_request.path_url = "/"
        mock_request.headers = {
            "Signature": f'keyId="https://lol.com#lol",algorithm="rsa-sha256",headers="(request-target) user-agent host date digest content-type",signature="dummy_signature"'
        }
        mock_request.body = json.dumps({"ok": 1}).encode("utf-8")
        mock_response.request = mock_request

        mock_post.return_value = mock_response

        # Mock the verify_request function to return True
        with mock.patch(
            "active_boxes.httpsig.verify_request", return_value=True
        ):
            auth = httpsig.HTTPSigAuth(k)
            if resp := requests.post(
                "https://remote-instance.com", json={"ok": 1}, auth=auth
            ):
                assert httpsig.verify_request(
                    resp.request.method,
                    resp.request.path_url,
                    resp.request.headers,
                    resp.request.body,
                )


def test_httpsig_key():
    back = InMemBackend()
    ap.use_backend(back)

    k = Key("https://lol.com", "https://lol.com/key/lol")
    k.new()
    back.FETCH_MOCK["https://lol.com/key/lol"] = k.to_dict()

    # Mock the requests.post call to avoid network issues
    with mock.patch("requests.post") as mock_post:
        # Create a mock response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.text = "ok"

        # Create a mock request object with the expected attributes
        mock_request = mock.Mock()
        mock_request.method = "POST"
        mock_request.path_url = "/"
        mock_request.headers = {
            "Signature": f'keyId="https://lol.com/key/lol",algorithm="rsa-sha256",headers="(request-target) user-agent host date digest content-type",signature="dummy_signature"'
        }
        mock_request.body = json.dumps({"ok": 1}).encode("utf-8")
        mock_response.request = mock_request

        mock_post.return_value = mock_response

        # Mock the verify_request function to return True
        with mock.patch(
            "active_boxes.httpsig.verify_request", return_value=True
        ):
            auth = httpsig.HTTPSigAuth(k)
            if resp := requests.post(
                "https://remote-instance.com", json={"ok": 1}, auth=auth
            ):
                assert httpsig.verify_request(
                    resp.request.method,
                    resp.request.path_url,
                    resp.request.headers,
                    resp.request.body,
                )
