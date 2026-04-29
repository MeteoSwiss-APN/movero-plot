"""Test that plotting functions close every matplotlib figure they open."""
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from matplotlib.lines import Line2D

matplotlib.use("Agg")

import matplotlib.figure
import moveroplot.config.plot_settings as plot_settings
from moveroplot.daytime_scores import _plot_and_save_scores as daytime_plot_and_save
from moveroplot.time_scores import _plot_and_save_scores as time_plot_and_save
from moveroplot.total_scores import _plot_and_save_scores as total_plot_and_save

_MODEL = "C-1E_ch"
_PARAMETER = "T_2M"
_LT_RANGES = ["01-06", "07-12"]
_SCORES = [["ME"], ["MAE"], ["FBI(0)"], ["POD(0)"], ["FAR(0)"]]
_SCORE_NAMES = [s for g in _SCORES for s in g]


def _header():
    return {
        "Missing value code": ["-0.999900E+09"],
        "Unit": ["degC"],
        "Model version": [_MODEL],
        "Start time": ["2024-01-01"],
        "End time": ["2024-01-31"],
    }


@pytest.fixture(autouse=True)
def _test_setup(monkeypatch):
    monkeypatch.setattr(plot_settings, "modelcolors", {_MODEL: "tab:red"})
    monkeypatch.setattr(matplotlib.figure.Figure, "savefig", lambda *a, **kw: None)


def _total_models_data():
    """models_data for total_scores._plot_and_save_scores."""
    df = pd.DataFrame({"Total": {s: float(i) for i, s in enumerate(_SCORE_NAMES)}})
    ltr_data = {ltr: {"df": df, "header": _header()} for ltr in _LT_RANGES}
    return {_MODEL: ltr_data}


def _daytime_ltr_models_data():
    """ltr_models_data for daytime_scores._plot_and_save_scores."""
    hours = list(range(0, 24))
    df = pd.DataFrame(
        {"hh": hours, **{s: np.ones(24) * float(i) for i, s in enumerate(_SCORE_NAMES)}}
    )
    entry = {"df": df, "header": _header()}
    return {ltr: {_MODEL: entry} for ltr in _LT_RANGES}


def _time_ltr_models_data():
    """ltr_models_data for time_scores._plot_and_save_scores."""
    timestamps = pd.date_range("2024-01-01", periods=24, freq="h")
    df = pd.DataFrame(
        {"timestamp": timestamps, **{s: np.ones(24) * float(i) for i, s in enumerate(_SCORE_NAMES)}}
    )
    entry = {"df": df, "header": _header()}
    return {ltr: {_MODEL: entry} for ltr in _LT_RANGES}


def test_total_scores_closes_all_figures(tmp_path):
    """total_scores._plot_and_save_scores must leave no open figures behind."""
    total_plot_and_save(
        output_dir=str(tmp_path),
        base_filename="total_test_",
        parameter=_PARAMETER,
        plot_scores_setup=_SCORES,
        sup_title="Test",
        models_data=_total_models_data(),
        models_color_lines=[Line2D([0], [0], color="tab:red", lw=2)],
        debug=False,
    )

    assert plt.get_fignums() == [], "total_scores._plot_and_save_scores leaked figures"


def test_daytime_scores_closes_all_figures(tmp_path):
    """daytime_scores._plot_and_save_scores must leave no open figures behind."""
    daytime_plot_and_save(
        output_dir=str(tmp_path),
        base_filename="daytime_test",
        parameter=_PARAMETER,
        plot_scores_setup=_SCORES,
        sup_title="Test",
        ltr_models_data=_daytime_ltr_models_data(),
        debug=False,
    )

    assert plt.get_fignums() == [], "daytime_scores._plot_and_save_scores leaked figures"


def test_time_scores_closes_all_figures(tmp_path):
    """time_scores._plot_and_save_scores must leave no open figures behind."""
    time_plot_and_save(
        output_dir=str(tmp_path),
        base_filename="time_test",
        parameter=_PARAMETER,
        plot_scores_setup=_SCORES,
        sup_title="Test",
        ltr_models_data=_time_ltr_models_data(),
        debug=False,
    )

    assert plt.get_fignums() == [], "time_scores._plot_and_save_scores leaked figures"
