"""MCPower GUI — PySide6 desktop application for Monte Carlo power analysis."""

try:
    from importlib.metadata import version as _get_version

    __version__ = _get_version("mcpower-gui")
except Exception:
    __version__ = "0.3.1"
