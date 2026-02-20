"""JSON file persistence for analysis history."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

_MAX_ENTRIES = 25


class HistoryManager:
    """Manages analysis history as individual JSON files.

    Default storage: ``~/.local/share/mcpower-gui/history/``
    """

    def __init__(self, history_dir: Path | None = None):
        if history_dir is None:
            history_dir = Path.home() / ".local" / "share" / "mcpower-gui" / "history"
        self._dir = Path(history_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        mode: str,
        result: dict,
        state_snapshot: dict,
        analysis_params: dict,
        data_file_path: str | None,
        script: str,
    ) -> str:
        """Write a new history record and enforce the entry cap.

        Returns the record id.
        """
        record_id = uuid.uuid4().hex
        record = {
            "id": record_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "result": result,
            "state_snapshot": state_snapshot,
            "analysis_params": analysis_params,
            "data_file_path": data_file_path,
            "script": script,
        }
        path = self._dir / f"{record_id}.json"
        path.write_text(json.dumps(record, default=str, indent=2), encoding="utf-8")
        self._enforce_cap()
        return record_id

    def list_records(self) -> list[dict]:
        """Return lightweight summaries sorted newest-first."""
        records = []
        for p in self._dir.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                snap = data.get("state_snapshot", {})
                aparams = data.get("analysis_params", {})
                records.append(
                    {
                        "id": data["id"],
                        "timestamp": data["timestamp"],
                        "mode": data["mode"],
                        "model_type": snap.get("model_type", "linear_regression"),
                        "formula": snap.get("formula", ""),
                        "sample_size": aparams.get("sample_size"),
                        "alpha": snap.get("alpha"),
                        "n_simulations": snap.get("n_simulations"),
                        "n_simulations_mixed_model": snap.get(
                            "n_simulations_mixed_model"
                        ),
                        "data_file_path": data.get("data_file_path"),
                        "test_formula": aparams.get("test_formula", ""),
                        "correction": aparams.get("correction", ""),
                        "scenarios": aparams.get("scenarios", False),
                        "ss_from": aparams.get("ss_from"),
                        "ss_to": aparams.get("ss_to"),
                        "ss_by": aparams.get("ss_by"),
                        "custom_name": data.get("custom_name"),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue
        records.sort(key=lambda r: r["timestamp"], reverse=True)
        return records

    def load(self, record_id: str) -> dict | None:
        """Return the full record for *record_id*, or None if not found."""
        path = self._dir / f"{record_id}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def delete(self, record_id: str) -> bool:
        """Remove a history record. Returns True if deleted."""
        path = self._dir / f"{record_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def update_custom_name(self, record_id: str, name: str | None) -> None:
        """Set or clear a custom display name on an existing history record."""
        path = self._dir / f"{record_id}.json"
        if not path.exists():
            return
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            # treat empty string as "clear"
            if name:
                record["custom_name"] = name
            else:
                record.pop("custom_name", None)
            path.write_text(json.dumps(record, default=str, indent=2), encoding="utf-8")
        except (json.JSONDecodeError, OSError):
            return

    def _enforce_cap(self):
        """Delete oldest files when exceeding MAX_ENTRIES."""
        files = sorted(self._dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
        while len(files) > _MAX_ENTRIES:
            files.pop(0).unlink()
