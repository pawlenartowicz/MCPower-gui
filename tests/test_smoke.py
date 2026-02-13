"""Test the --smoke-test CLI flag via subprocess."""

import subprocess
import sys


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
