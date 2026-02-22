"""Background update checker — queries GitHub Releases API."""

from __future__ import annotations

import json
import sys
import urllib.request

from packaging.version import Version

from PySide6.QtCore import QThread, Signal

LATEST_RELEASE_URL = (
    "https://api.github.com/repos/pawlenartowicz/mcpower-gui/releases/latest"
)
TIMEOUT_SECONDS = 5

# Platform → asset filename patterns (matched case-insensitively)
_PLATFORM_ASSET_NAMES: dict[str, list[str]] = {
    "win32": ["MCPower.exe"],
    "darwin": ["MCPower-macos.zip"],
    "linux": ["MCPower-linux"],
}


def _find_platform_asset(assets: list[dict]) -> str | None:
    """Return the browser_download_url for the asset matching the current platform."""
    expected = _PLATFORM_ASSET_NAMES.get(sys.platform, [])
    for expected_name in expected:
        for asset in assets:
            if asset.get("name", "").lower() == expected_name.lower():
                return asset.get("browser_download_url")
    return None


def check_for_update(current_version: str) -> tuple[str, str] | None:
    """Check GitHub for a newer release.

    Returns (new_version, download_url) if a newer version exists, else None.
    The download_url points to the platform-specific asset if available,
    otherwise falls back to the release page.
    Returns None on any error.
    """
    try:
        req = urllib.request.Request(
            LATEST_RELEASE_URL,
            headers={"Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            data = json.loads(resp.read())

        tag = data["tag_name"]
        remote_version = tag.lstrip("v")

        remote = Version(remote_version)
        if remote.is_prerelease:
            return None
        if remote > Version(current_version):
            download_url = _find_platform_asset(data.get("assets", []))
            if not download_url:
                download_url = data["html_url"]
            return remote_version, download_url
    except Exception:
        pass
    return None


class UpdateChecker(QThread):
    """QThread that checks for updates and emits a signal if one is found."""

    update_available = Signal(str, str)  # (new_version, release_url)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self._current_version = current_version

    def run(self):
        result = check_for_update(self._current_version)
        if result is not None:
            self.update_available.emit(*result)
