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
            "n_simulations_mixed_model": 800,
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


def test_update_custom_name_sets_name(tmp_path):
    hm = HistoryManager(tmp_path)
    record_id = hm.save(**_dummy_record())
    hm.update_custom_name(record_id, "My Run")
    record = hm.load(record_id)
    assert record["custom_name"] == "My Run"


def test_update_custom_name_clears_name(tmp_path):
    hm = HistoryManager(tmp_path)
    record_id = hm.save(**_dummy_record())
    hm.update_custom_name(record_id, "My Run")
    hm.update_custom_name(record_id, None)
    record = hm.load(record_id)
    assert "custom_name" not in record


def test_update_custom_name_nonexistent_is_noop(tmp_path):
    hm = HistoryManager(tmp_path)
    hm.update_custom_name("doesnotexist", "Boom")  # must not raise


def test_list_records_includes_custom_name(tmp_path):
    hm = HistoryManager(tmp_path)
    record_id = hm.save(**_dummy_record())
    hm.update_custom_name(record_id, "Named")
    summaries = hm.list_records()
    assert summaries[0]["custom_name"] == "Named"


def test_list_records_custom_name_none_when_absent(tmp_path):
    hm = HistoryManager(tmp_path)
    hm.save(**_dummy_record())
    summaries = hm.list_records()
    assert summaries[0]["custom_name"] is None
