"""Background update checker — queries GitHub Releases API."""

from __future__ import annotations

import json
import urllib.request

from packaging.version import Version

from PySide6.QtCore import QThread, Signal

LATEST_RELEASE_URL = (
    "https://api.github.com/repos/pawlenartowicz/mcpower-gui/releases/latest"
)
TIMEOUT_SECONDS = 5


def check_for_update(current_version: str) -> tuple[str, str] | None:
    """Check GitHub for a newer release.

    Returns (new_version, release_url) if a newer version exists, else None.
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
        release_url = data["html_url"]

        remote = Version(remote_version)
        if remote.is_prerelease:
            return None
        if remote > Version(current_version):
            return remote_version, release_url
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
