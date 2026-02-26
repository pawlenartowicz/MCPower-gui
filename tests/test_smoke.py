"""Test the --smoke-test CLI flag via subprocess."""

import subprocess
import sys

import pytest
from PySide6.QtWidgets import QApplication


class TestSmokeTest:
    def test_smoke_test_exits_zero(self):
        result = subprocess.run(
            [sys.executable, "-m", "mcpower_gui", "--smoke-test"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"Smoke test failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    def test_smoke_test_prints_version(self):
        result = subprocess.run(
            [sys.executable, "-m", "mcpower_gui", "--smoke-test"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert "mcpower-gui" in result.stdout


_app = QApplication.instance() or QApplication([])


@pytest.fixture
def qapp():
    return _app


def test_settings_dialog_lme_scenario_params(qapp):
    """Settings dialog round-trips LME scenario params through state."""
    from mcpower_gui.state import ModelState
    from mcpower_gui.widgets.settings_dialog import SettingsDialog

    state = ModelState()
    dlg = SettingsDialog(state)

    # Verify combo boxes exist for realistic scenario
    combos = dlg._scenario_combos.get("realistic", {})
    assert "random_effect_dist" in combos, "random_effect_dist combo missing"

    # Verify spinboxes exist for LME numeric params
    spins = dlg._scenario_spins.get("realistic", {})

    # Verify residual dist checkboxes exist
    assert "_residual_cb_heavy" in spins, "residual heavy_tailed checkbox missing"
    assert "_residual_cb_skewed" in spins, "residual skewed checkbox missing"
    for key in (
        "icc_noise_sd",
        "random_effect_df",
        "residual_change_prob",
        "residual_df",
    ):
        assert key in spins, f"{key} spin missing"

    dlg._apply_and_accept()

    # State should now have LME keys
    for scenario in ("optimistic", "realistic", "doomer"):
        cfg = state.scenario_configs[scenario]
        for key in (
            "icc_noise_sd",
            "random_effect_dist",
            "random_effect_df",
            "residual_dists",
            "residual_change_prob",
            "residual_df",
        ):
            assert key in cfg, f"{scenario}.{key} not saved to state"
