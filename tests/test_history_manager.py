"""Tests for mcpower_gui.history_manager — save/load/list/delete, cap enforcement."""

import time

from mcpower_gui.history_manager import HistoryManager


def _dummy_record(**overrides):
    record = {
        "mode": "power",
        "result": {"power": 0.8},
        "state_snapshot": {
            "formula": "y = x1",
            "alpha": 0.05,
            "n_simulations": 1600,
            "n_simulations_mixed_model": 400,
        },
        "analysis_params": {"sample_size": 100},
        "data_file_path": None,
        "script": "# test script",
    }
    record.update(overrides)
    return record


class TestSaveAndLoad:
    def test_round_trip(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        rec = _dummy_record()
        record_id = hm.save(**rec)

        loaded = hm.load(record_id)
        assert loaded is not None
        assert loaded["id"] == record_id
        assert loaded["mode"] == "power"
        assert loaded["result"]["power"] == 0.8
        assert loaded["script"] == "# test script"

    def test_load_nonexistent_returns_none(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        assert hm.load("nonexistent_id") is None


class TestListRecords:
    def test_returns_sorted_summaries(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        id1 = hm.save(**_dummy_record())
        time.sleep(0.05)
        id2 = hm.save(**_dummy_record())

        records = hm.list_records()
        assert len(records) == 2
        # Newest first
        assert records[0]["id"] == id2
        assert records[1]["id"] == id1
        # Summary fields present
        assert "formula" in records[0]
        assert "timestamp" in records[0]

    def test_empty_dir(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        assert hm.list_records() == []


class TestDelete:
    def test_delete_removes_record(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        record_id = hm.save(**_dummy_record())
        assert hm.delete(record_id) is True
        assert hm.load(record_id) is None

    def test_delete_nonexistent_returns_false(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        assert hm.delete("nonexistent_id") is False


class TestCapEnforcement:
    def test_cap_at_25(self, tmp_path):
        hm = HistoryManager(history_dir=tmp_path)
        for _ in range(27):
            hm.save(**_dummy_record())

        records = hm.list_records()
        assert len(records) == 25
