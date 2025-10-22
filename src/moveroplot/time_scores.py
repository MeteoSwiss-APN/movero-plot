# pylint: skip-file
# Standard library
import re

# Third-party
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# First-party
import moveroplot.config.plot_settings as plot_settings
from moveroplot.load_files import load_relevant_files
from moveroplot.plotting import get_total_dates_from_headers

# Local
from .utils.parse_plot_synop_ch import cat_time_score_range
from .utils.parse_plot_synop_ch import time_score_range
from .utils.set_ylims import set_ylim
from.utils.unitless_scores_lists import unit_number_scores, unitless_scores


def _time_score_transformation(df, header):
    df = df.replace(float(header["Missing value code"][0]), np.NaN)
    names = {
        "YYYY": "year",
        "MM": "month",
        "DD": "day",
        "hh": "hour",
        "mm": "minute",
    }
    df["timestamp"] = pd.to_datetime(
        df[["YYYY", "MM", "DD", "hh", "mm"]].rename(columns=names)
    )
    df.drop(
        ["YYYY", "MM", "DD", "hh", "mm", "lt_hh", "lt_mm"],
        axis=1,
        inplace=True,
    )
    return df


# enter directory / read station_scores files / call plotting pipeline
def _time_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    """Read all ATAB files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>.

        Extract relevant information (parameters/scores) from these files into a dataframe.
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists.

    Args:
        lt_ranges (list): lead time ranges, for which plots should be generated (i.e. 01-06, 07-12,...). part of the file name
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. time_scores)
        file_postfix (str): postfix of files (i.e. '.dat')
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd)
        output_dir (str): output directory (i.e. plots/)
        season (str): season of interest (i.e. 2021s4/)
        model_version (str): model_version of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        debug (bool): print further comments & debug statements

    """  # noqa: E501
    print("---initialising time score pipeline")
    if not lt_ranges:
        lt_ranges = "19-24"

    for model_plots in plot_setup["model_versions"]:
        for parameter, scores in plot_setup["parameter"].items():
            model_data = load_relevant_files(
                input_dir,
                file_prefix,
                file_postfix,
                debug,
                model_plots,
                parameter,
                lt_ranges,
                ltr_first=True,
                transform_func=_time_score_transformation,
            )
            if not model_data:
                print(f"No matching files found with given ltr {lt_ranges}")
                return
            _generate_timeseries_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )


def _clear_empty_axes_if_necessary(subplot_axes, idx):
    # remove empty ``axes`` instances
    if idx % 2 != 1:
        [ax.axis("off") for ax in subplot_axes[(idx + 1) % 2 :]]


def _save_figure(output_dir, filename, title, fig, axes, idx):
    fig.suptitle(
        title,
        horizontalalignment="center",
        verticalalignment="top",
        fontdict={
            "size": 6,
            "color": "k",
        },
        bbox={"facecolor": "none", "edgecolor": "grey"},
    )
    _clear_empty_axes_if_necessary(axes, idx)
    fig.savefig(f"{output_dir}/{filename[:-1]}.png")
    plt.close()


def _initialize_plots(labels: list):
    fig, ((ax0), (ax1)) = plt.subplots(
        nrows=2, ncols=1, tight_layout=True, figsize=(10, 10), dpi=200
    )

    custom_lines = [
        Line2D([0], [0], color=plot_settings.modelcolors[label], lw=2)
        for label in labels
    ]
    fig.legend(
        custom_lines,
        labels,
        loc="upper right",
        ncol=1,
        frameon=False,
    )
    plt.tight_layout(w_pad=8, h_pad=5, rect=(0.05, 0.05, 0.90, 0.90))
    return fig, [ax0, ax1]


def _customise_ax(parameter, scores, x_ticks, grid, ax):
    """Apply cosmetics to current ax.

    Args:
        parameter (str): current parameter
        score (str): current score
        x_ticks (list): list of x-ticks labels (lead time ranges, as strings)
        grid (bool): add grid to ax
        ax (Axes): current ax

    """
    if grid:
        ax.grid(which="major", color="#DDDDDD", linewidth=0.8)
        ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=0.5)
        ax.minorticks_on()

    ax.tick_params(axis="both", which="major", labelsize=8)
    ax.tick_params(axis="both", which="minor", labelsize=6)
    ax.set_title(f"{parameter}: {','.join(scores)}")
    ax.set_xlabel("Lead-Time Range (h)")
    # plotting too many data on the x-axis
    steps = len(x_ticks) // 7
    skip_indices = slice(None, None, steps) if steps > 0 else slice(None)
    ax.set_xticks(range(len(x_ticks))[skip_indices], x_ticks[skip_indices])
    ax.autoscale(axis="y")


def _plot_and_save_scores(
    output_dir,
    base_filename,
    parameter,
    plot_scores_setup,
    sup_title,
    ltr_models_data,
    debug=False,
):
    for ltr, models_data in ltr_models_data.items():
        fig, subplot_axes = _initialize_plots(ltr_models_data[ltr].keys())
        headers = [data["header"] for data in models_data.values()]
        total_start_date, total_end_date = get_total_dates_from_headers(headers)
        title_base = f"{parameter.upper()}: "
        model_info = (
            f" {list(models_data.keys())[0]}" if len(models_data.keys()) == 1 else ""
        )
        x_label_base = f"""{total_start_date.strftime("%Y-%m-%d %H:%M")} - {total_end_date.strftime("%Y-%m-%d %H:%M")}"""  # noqa: E501
        filename = base_filename + f"_{ltr}"
        pattern = (
            re.search(r"\(.*?\)", next(iter(plot_scores_setup))[0])
            if plot_scores_setup
            else None
        )
        prev_threshold = None
        if pattern is not None:
            prev_threshold = pattern.group()
        current_threshold = prev_threshold
        current_plot_idx = 0

        for idx, score_setup in enumerate(plot_scores_setup):
            prev_threshold = current_threshold
            pattern = re.search(r"\(.*?\)", next(iter(score_setup)))
            current_threshold = pattern.group() if pattern is not None else None
            different_threshold = prev_threshold != current_threshold
            if different_threshold:
                _clear_empty_axes_if_necessary(subplot_axes, current_plot_idx - 1)
                fig.suptitle(
                    sup_title,
                    horizontalalignment="center",
                    verticalalignment="top",
                    fontdict={
                        "size": 6,
                        "color": "k",
                    },
                    bbox={"facecolor": "none", "edgecolor": "grey"},
                )
                fig.savefig(f"{output_dir}/{filename}.png")
                plt.close()
                filename = base_filename + f"_{ltr}"
                fig, subplot_axes = _initialize_plots(ltr_models_data[ltr].keys())
                current_plot_idx += current_plot_idx % 2

            title = title_base + ",".join(score_setup) + model_info + f" LT: {ltr}"
            ax = subplot_axes[current_plot_idx % 2]
            for key, data in models_data.items():
                model_plot_color = plot_settings.modelcolors[key]
                header = data["header"]
                unit = header["Unit"][0]
                x_int = data["df"][["timestamp"]]
                y_label = ",".join(score_setup)
                #ax.setylabel 
                if any(val1.startswith(val2) for val1 in score_setup for val2 in unitless_scores):
                    ax.set_ylabel(f"{y_label.upper()}")
                elif any(val1.startswith(val2) for val1 in score_setup for val2 in unit_number_scores):
                    ax.set_ylabel(f"{y_label.upper()} (Number)")
                else:
                    ax.set_ylabel(f"{y_label.upper()} ({unit})")
                ax.set_xlabel(x_label_base)
                ax.set_title(title)
                for score_idx, score in enumerate(score_setup):
                    score_values = data["df"][[score]]
                    ax.plot(
                        np.asarray(x_int, dtype="datetime64[s]"),
                        score_values,
                        color=model_plot_color,
                        linestyle=plot_settings.line_styles[score_idx],
                        fillstyle="none",
                        label=f"{score.upper()}",
                    )
                    set_ylim(
                        param=parameter,
                        score_range=time_score_range,
                        cat_score_range=cat_time_score_range,
                        score=score,
                        ax=ax,
                        y_values=score_values[score].values,
                    )
                    ymin, ymax = ax.get_ylim()
                    if ymin <= 0 <= ymax:
                        ax.axhline(y=0, color="black", linestyle="--", linewidth=0.5)
                    if score.startswith("FBI"):
                        ax.axhline(y=1, color="black", linestyle="--", linewidth=0.5)
                    ax.tick_params(axis="both", which="major", labelsize=8)
                    ax.tick_params(axis="both", which="minor", labelsize=6)
                ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
            if len(score_setup) > 1:
                sub_plot_legend = ax.legend(
                    score_setup,
                    loc="upper right",
                    markerscale=0.9,
                    bbox_to_anchor=(1.1, 1.05),
                )
                for line in sub_plot_legend.get_lines():
                    line.set_color("black")
            filename += "_" + "_".join(score_setup)

            if current_plot_idx % 2 == 1 or idx == len(plot_scores_setup) - 1:
                _clear_empty_axes_if_necessary(subplot_axes, current_plot_idx)
                fig.suptitle(
                    sup_title,
                    horizontalalignment="center",
                    verticalalignment="top",
                    fontdict={
                        "size": 6,
                        "color": "k",
                    },
                    bbox={"facecolor": "none", "edgecolor": "grey"},
                )
                fig.savefig(f"{output_dir}/{filename}.png")
                plt.close()
                filename = base_filename + f"_{ltr}"
                fig, subplot_axes = _initialize_plots(ltr_models_data[ltr].keys())
            current_plot_idx += 1


# PLOTTING PIPELINE FOR TIME SCORES PLOTS
def _generate_timeseries_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    debug,
):
    # flat list of unique keys of dicts within models_data dict
    model_versions = list({k for d in models_data.values() for k in d.keys()})

    # initialise filename
    base_filename = (
        f"time_scores_{model_versions[0]}_{parameter}"
        if len(model_versions) == 1
        else f"time_scores_{parameter}"
    )
    headers = [
        data["header"] for data in models_data[next(iter(models_data.keys()))].values()
    ]
    total_start_date, total_end_date = get_total_dates_from_headers(headers)
    # pylint: disable=line-too-long
    period_info = f"""Period: {total_start_date.strftime("%Y-%m-%d %H:%M")} - {total_end_date.strftime("%Y-%m-%d %H:%M")} | © MeteoSwiss"""  # noqa: E501
    # pylint: enable=line-too-long
    sup_title = f"{parameter}: " + period_info
    # plot regular scores
    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["regular_scores"],
        sup_title,
        models_data,
        debug=debug,
    )

    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["cat_scores"],
        sup_title,
        models_data,
        debug=debug,
    )
