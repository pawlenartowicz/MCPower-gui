"""Tests for update_checker module."""

import json
from unittest.mock import MagicMock, patch

from mcpower_gui.update_checker import check_for_update


def _mock_response(body: bytes):
    resp = MagicMock()
    resp.read.return_value = body
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestCheckForUpdate:
    def test_newer_version_available(self):
        body = json.dumps({
            "tag_name": "v1.0.0",
            "html_url": "https://github.com/pawlenartowicz/mcpower-gui/releases/tag/v1.0.0",
        }).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            result = check_for_update("0.1.0")

        assert result is not None
        version, url = result
        assert version == "1.0.0"
        assert "releases/tag/v1.0.0" in url

    def test_same_version_returns_none(self):
        body = json.dumps({
            "tag_name": "v0.1.0",
            "html_url": "https://github.com/pawlenartowicz/mcpower-gui/releases/tag/v0.1.0",
        }).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            assert check_for_update("0.1.0") is None

    def test_older_version_returns_none(self):
        body = json.dumps({
            "tag_name": "v0.0.9",
            "html_url": "https://github.com/pawlenartowicz/mcpower-gui/releases/tag/v0.0.9",
        }).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            assert check_for_update("0.1.0") is None

    def test_network_error_returns_none(self):
        with patch("urllib.request.urlopen", side_effect=OSError("no network")):
            assert check_for_update("0.1.0") is None

    def test_malformed_json_returns_none(self):
        with patch("urllib.request.urlopen", return_value=_mock_response(b"not json")):
            assert check_for_update("0.1.0") is None

    def test_missing_tag_name_returns_none(self):
        body = json.dumps({"html_url": "https://example.com"}).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            assert check_for_update("0.1.0") is None

    def test_prerelease_current_is_older_than_stable_release(self):
        body = json.dumps({
            "tag_name": "v0.1.1",
            "html_url": "https://github.com/pawlenartowicz/mcpower-gui/releases/tag/v0.1.1",
        }).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            result = check_for_update("0.1.1rc0")

        assert result is not None
        assert result[0] == "0.1.1"

    def test_prerelease_remote_is_ignored(self):
        body = json.dumps({
            "tag_name": "v0.1.1rc1",
            "html_url": "https://github.com/pawlenartowicz/mcpower-gui/releases/tag/v0.1.1rc1",
        }).encode()

        with patch("urllib.request.urlopen", return_value=_mock_response(body)):
            assert check_for_update("0.1.1rc0") is None
