"""Plain Python dataclass holding the GUI model state.

No Qt dependencies — keeps state testable and decoupled from the UI.
"""

from __future__ import annotations

import copy
import os
from dataclasses import dataclass, field

SCENARIO_ORDER = ["optimistic", "realistic", "doomer"]

SCENARIO_DEFAULTS: dict[str, dict[str, float | str | int]] = {
    "optimistic": {
        "heterogeneity": 0.0,
        "heteroskedasticity": 0.0,
        "correlation_noise_sd": 0.0,
        "distribution_change_prob": 0.0,
        # LME-specific (only consumed by mixed models)
        "icc_noise_sd": 0.0,
        "random_effect_dist": "normal",
        "random_effect_df": 5,
        "residual_dist": "normal",
        "residual_change_prob": 0.0,
        "residual_df": 10,
    },
    "realistic": {
        "heterogeneity": 0.2,
        "heteroskedasticity": 0.1,
        "correlation_noise_sd": 0.2,
        "distribution_change_prob": 0.3,
        # LME-specific
        "icc_noise_sd": 0.15,
        "random_effect_dist": "heavy_tailed",
        "random_effect_df": 5,
        "residual_dist": "heavy_tailed",
        "residual_change_prob": 0.3,
        "residual_df": 10,
    },
    "doomer": {
        "heterogeneity": 0.4,
        "heteroskedasticity": 0.2,
        "correlation_noise_sd": 0.4,
        "distribution_change_prob": 0.6,
        # LME-specific
        "icc_noise_sd": 0.30,
        "random_effect_dist": "heavy_tailed",
        "random_effect_df": 3,
        "residual_dist": "heavy_tailed",
        "residual_change_prob": 0.8,
        "residual_df": 5,
    },
}


def build_variable_type_string(variable_types: dict[str, dict]) -> str:
    """Build MCPower set_variable_type string from variable_types dict.

    Shared by AnalysisWorker and script_generator.
    """
    parts: list[str] = []
    for name, info in variable_types.items():
        vtype = info.get("type", "continuous")
        if vtype == "continuous":
            continue
        elif vtype == "binary":
            proportion = info.get("proportion", 0.5)
            parts.append(f"{name}=(binary, {proportion})")
        elif vtype == "factor":
            proportions = info.get("proportions", [])
            if proportions:
                props_str = ", ".join(str(p) for p in proportions)
                parts.append(f"{name}=(factor, {props_str})")
            else:
                n_levels = info.get("n_levels", 3)
                parts.append(f"{name}=(factor, {n_levels})")
    return ", ".join(parts)


def build_correlations_string(correlations: dict[str, float]) -> str:
    """Build MCPower set_correlations string from correlations dict.

    Keys are in ``"var1,var2"`` format.
    Shared by AnalysisWorker and script_generator.
    """
    parts = []
    for key, val in correlations.items():
        var1, var2 = key.split(",")
        parts.append(f"corr({var1}, {var2})={val}")
    return ", ".join(parts)


@dataclass
class ModelState:
    """Snapshot of all user-configurable model parameters."""

    # Model type: "linear_regression" or "anova"
    model_type: str = "linear_regression"

    # Formula
    formula: str = ""
    dep_var: str = ""
    predictors: list[str] = field(default_factory=list)

    # ANOVA-specific fields (raw user input for UI restoration)
    anova_factors: list[dict] = field(default_factory=list)
    anova_interactions: list[str] = field(default_factory=list)

    # Named factor level metadata (populated from data upload)
    factor_reference_levels: dict[str, str] = field(default_factory=dict)
    factor_level_labels: dict[str, list[str]] = field(default_factory=dict)

    # Effect sizes: predictor name -> float (may include expanded factor dummies)
    effects: dict[str, float] = field(default_factory=dict)

    # Variable types: predictor name -> type info dict
    # e.g. {"x1": {"type": "continuous"}, "x2": {"type": "binary", "proportion": 0.5},
    #        "x3": {"type": "factor", "n_levels": 3, "proportions": [0.33, 0.33, 0.34]}}
    variable_types: dict[str, dict] = field(default_factory=dict)

    # Uploaded empirical data (None = no data uploaded)
    uploaded_data: dict[str, list] | None = None
    data_file_path: str | None = None

    # Correlation settings
    preserve_correlation: str = "partial"  # "strict" | "partial" | "no"
    correlations: dict[str, float] = field(default_factory=dict)  # key "x1,x2" -> float

    # Cluster configurations for mixed models (random effects)
    cluster_configs: list[dict] = field(default_factory=list)

    # Analysis settings
    n_simulations: int = 1600
    n_simulations_mixed_model: int = 800
    alpha: float = 0.05
    target_power: float = 80.0

    # Advanced settings (managed by Settings dialog)
    seed: int = 2137
    max_failed_simulations: float = 0.03
    parallel: bool | str = "mixedmodels"  # False, True, or "mixedmodels"
    n_cores: int = field(default_factory=lambda: max(1, (os.cpu_count() or 4) // 2))
    scenario_configs: dict = field(
        default_factory=lambda: {k: dict(v) for k, v in SCENARIO_DEFAULTS.items()}
    )

    def build_variable_type_string(self) -> str:
        """Build MCPower set_variable_type string from variable_types dict."""
        return build_variable_type_string(self.variable_types)

    def snapshot(self) -> dict:
        """Return a JSON-serializable snapshot (no DataFrame)."""
        return {
            "model_type": self.model_type,
            "formula": self.formula,
            "dep_var": self.dep_var,
            "predictors": list(self.predictors),
            "effects": dict(self.effects),
            "variable_types": {k: dict(v) for k, v in self.variable_types.items()},
            "anova_factors": [dict(f) for f in self.anova_factors],
            "anova_interactions": list(self.anova_interactions),
            "factor_reference_levels": dict(self.factor_reference_levels),
            "factor_level_labels": {
                k: list(v) for k, v in self.factor_level_labels.items()
            },
            "uploaded_columns": list(self.uploaded_data.keys()) if self.uploaded_data else [],
            "n_simulations": self.n_simulations,
            "n_simulations_mixed_model": self.n_simulations_mixed_model,
            "alpha": self.alpha,
            "target_power": self.target_power,
            "seed": self.seed,
            "max_failed_simulations": self.max_failed_simulations,
            "parallel": self.parallel,
            "n_cores": self.n_cores,
            "preserve_correlation": self.preserve_correlation,
            "correlations": dict(self.correlations),
            "cluster_configs": copy.deepcopy(self.cluster_configs),
            "scenario_configs": {k: dict(v) for k, v in self.scenario_configs.items()},
        }
