"""Calculate ensemble scores from parsed data."""
# Standard library
import re
from typing import Tuple

# Third-party
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# First-party
from moveroplot.config import plot_settings
from moveroplot.load_files import load_relevant_files
from moveroplot.plotting import get_total_dates_from_headers

# Local
from .station_scores import _calculate_figsize
from.utils.unitless_scores_lists import unit_number_scores, unitless_scores

# pylint: disable=no-name-in-module


def _ensemble_score_transformation(df, header):
    df = df.replace(float(header["Missing value code"][0]), np.NaN)
    df.set_index(keys="Score", inplace=True)
    return df


# pylint: disable=too-many-arguments,too-many-locals
def _ensemble_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    print("\n--- initialising ensemble score pipeline")
    if not lt_ranges:
        lt_ranges = "07-12,13-18,19-24"
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
                transform_func=_ensemble_score_transformation,
            )
            if not model_data:
                print(f"No matching files found with given ltr {lt_ranges}")
                return
            _generate_ensemble_scores_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )


def _initialize_plots(
    num_rows: int, num_cols: int, single_figsize: Tuple[int, int] = (8, 4)
):
    figsize = _calculate_figsize(
        num_rows, num_cols, single_figsize, (1, 1)
    )  # (10, 6.8)
    fig, axes = plt.subplots(
        nrows=num_rows,
        ncols=num_cols,
        tight_layout=True,
        figsize=figsize,
        dpi=100,
        squeeze=False,
    )
    fig.tight_layout(w_pad=6, h_pad=4, rect=(0.05, 0.05, 0.90, 0.85))
    plt.subplots_adjust(bottom=0.15)
    return fig, axes


def _add_sample_subplot(fig, ax):
    box = ax.get_position()
    width = box.width
    height = box.height
    l, b, h, w = 0.8, 0.025, 0.3, 0.2
    w *= width
    h *= height
    inax_position = ax.transAxes.transform([l, b])
    transformed_fig = fig.transFigure.inverted()
    infig_position = transformed_fig.transform(inax_position)
    sub_plot = fig.add_axes([*infig_position, w, h])
    sub_plot.set_xticks([])
    sub_plot.set_title("N")
    return sub_plot


def _add_boundary_line(ax, points):
    ax.plot(
        [0, 1],
        points,
        color="black",
        fillstyle="none",
        linestyle="--",
        alpha=0.2,
    )


def _get_bin_values(data: dict, prefix: str, threshold: str):
    indices = [
        index for index in data["df"]["Total"].index if f"{prefix}{threshold}" in index
    ]
    return data["df"]["Total"][indices]


def _set_suptitle(fig, sup_title):
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

# pylint: disable=too-many-branches,too-many-statements
def _plot_and_save_scores(
    output_dir,
    base_filename,
    parameter,
    plot_scores_setup,
    sup_title,
    models_data,
    models_color_lines,
    debug=False,
):
    if debug:
        print("Plotting ensemble scores.")
    for score_setup in plot_scores_setup:
        custom_sup_title = sup_title
        filename = base_filename
        if "RANK" in score_setup:
            [score] = score_setup
            custom_sup_title = f"RANK: {sup_title}"
            for ltr, model_data in models_data.items():
                fig, subplot_axes = _initialize_plots(1, 1)
                filename = f"{base_filename}_RANK_{ltr}"
                [ax] = subplot_axes.ravel()
                ax.set_xlabel("RANK")
                ax.set_title(f"{parameter}, LT: {ltr}")
                for model_idx, data in enumerate(model_data.values()):
                    model_key = list(models_data[ltr].keys())[model_idx]
                    model_plot_color = plot_settings.modelcolors[model_key]
                    model_ranks = sorted(
                        [
                            index
                            for index in data["df"]["Total"].index
                            if "RANK" in index
                        ],
                        key=lambda x: int("".join(filter(str.isdigit, x))),
                    )
                    ranks = data["df"]["Total"][model_ranks].reset_index(drop=True)
                    ax.bar(
                        np.arange(len(model_ranks)) + model_idx * 0.25,
                        ranks,
                        width=0.25,
                        color=model_plot_color,
                    )
                _set_suptitle(
                    fig,
                    custom_sup_title,
                )
                fig.legend(
                    all_handles,
                    all_labels,
                    loc="upper right",
                    ncol=1,
                    frameon=True,
                )

                fig.savefig(f"{output_dir}/{filename}.png")
                plt.close()
        elif any("REL_DIA" in score for score in score_setup):
            [score] = score_setup
            threshold = re.search(r"\(.*?\)", score).group()
            for ltr, model_data in models_data.items():
                fig, subplot_axes = _initialize_plots(1, 1, (6.7, 6))
                [ax] = subplot_axes.ravel()
                filename = f"{base_filename}_{score}_{ltr}"
                ax.set_ylabel("Observed Relative Frequency")
                ax.set_xlabel("Forecast Probability")
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_aspect("equal")
                [unit] = model_data[next(iter(model_data.keys()))]["header"]["Unit"]
                ax.set_title(f"{parameter} {threshold[1:-1]} {unit}, LT: {ltr}")
                sample_subplot = _add_sample_subplot(fig, ax)

                for model_idx, data in enumerate(model_data.values()):
                    model_key = list(models_data[ltr].keys())[model_idx]
                    model_plot_color = plot_settings.modelcolors[model_key]
                    fbin_values = _get_bin_values(data, "FBIN", threshold)
                    obin_values = _get_bin_values(data, "OBIN", threshold)
                    nbin_values = _get_bin_values(data, "NBIN", threshold)
                    of_value = _get_bin_values(data, "OF", threshold)
                    ax.plot(
                        fbin_values,
                        obin_values,
                        color=model_plot_color,
                        marker="D",
                        fillstyle="none",
                    )

                    sample_subplot.bar(
                        np.arange(len(nbin_values)) + model_idx * 0.25,
                        nbin_values,
                        width=0.25,
                        color=model_plot_color,
                    )

                _add_boundary_line(ax, [0, 1])
                _add_boundary_line(ax, [of_value, of_value])
                _add_boundary_line(
                    ax,
                    [
                        (1 - np.tan(np.pi / 8)) * of_value,
                        of_value + (1 - of_value) * np.tan(np.pi / 8),
                    ],
                )
                sample_subplot.set_yticks(np.round([max(nbin_values)], -3))
                _set_suptitle(
                    fig,
                    custom_sup_title,
                )
                fig.legend(
                    all_handles,
                    all_labels,
                    loc="center right",
                    ncol=1,
                    frameon=True,
                )
                fig.savefig(f"{output_dir}/{filename}.png")
                plt.close()
        else:
            fig, subplot_axes = _initialize_plots(
                2 if len(score_setup) > 1 else 1,
                (len(score_setup) + 1) // 2,
            )
            subplot_axes = subplot_axes.ravel()

            model_names = list(models_data[next(iter(models_data.keys()))].keys())
            all_handles = list(models_color_lines)
            all_labels  = list(model_names)

            ltr_sorted = sorted(
                list(models_data.keys()), key=lambda x: int(x.split("-")[0])
            )
            x_int = list(range(len(ltr_sorted)))
            for score_idx, score in enumerate(score_setup):
                print(
                    "SCORE IN ENS ",
                    score,
                    models_data.keys(),
                    [models_data[ltr].keys() for ltr in ltr_sorted],
                )
                ax = subplot_axes[score_idx]
                ax.get_yaxis().get_major_formatter().set_useOffset(False)
                filename += f"_{score}"
                for model_idx, model_name in enumerate(
                    models_data[next(iter(ltr_sorted))].keys()
                ):
                    model_plot_color = plot_settings.modelcolors[model_name]
                    y_values = [
                        models_data[ltr][model_name]["df"]["Total"].loc[score]
                        if model_name in models_data[ltr].keys()
                        else None
                        for ltr in ltr_sorted
                    ]
                    filtered_x_int = [
                        x for x, y in zip(x_int, y_values) if y is not None
                    ]
                    filtered_y_values = [y for y in y_values if y is not None]
                    ax.plot(
                        filtered_x_int,
                        filtered_y_values,
                        color=model_plot_color,
                        marker="D",
                        fillstyle="none",
                        label=model_name,
                    )

                #ax.setylabel
                sample_ltr = next(iter(models_data))
                sample_model = next(iter(models_data[sample_ltr]))
                unit = models_data[sample_ltr][sample_model]["header"]["Unit"][0]

                if any(s.startswith(u) for s in score_setup for u in unitless_scores):
                    ax.set_ylabel(score)
                elif any(s.startswith(u) for s in score_setup for u in
                         unit_number_scores):
                    ax.set_ylabel(f"{score}, (Number)")
                else:
                    ax.set_ylabel(f"{score}, ({unit})")
                ax.set_xticks(x_int, ltr_sorted)
                ax.set_title(f"{parameter}: {score}")
                ax.grid(which="major", color="#DDDDDD", linewidth=0.8)
                ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=0.5)
                ax.set_xlabel("Lead-Time Range (h)")

                ymin, ymax = ax.get_ylim()
                if ymin <= 0 <= ymax:
                    ax.axhline(y=0, color="black",         linestyle="--", linewidth=0.5)
                if "OUTLIERS" in score:
                    #This part of the loop adds dotted lines that indicate the optimal value for each model
                    headers = [data["header"] for data in models_data[next(iter(models_data))].values()]
                    for h in headers:
                        rows_dict = {h["Model name"][0]: int(h["EPS info"][0])}
                        model_name = list(rows_dict.keys())[0] + "_ch"
                        model_plot_color =plot_settings.modelcolors[model_name]
                        n=list(rows_dict.values())[0]
                        ax.axhline(y=2/(n+1), color=model_plot_color, label=model_name, linestyle="--", linewidth=0.8)
                    #this part of the loop adds a black dotted line to the legend of the OUTLIER plots to represent the optimal value lines
                    outlier_handles = [Line2D([], [], linestyle="--", linewidth=0.8, color="black")]
                    outlier_labels  = ["Optimal value"]
                    all_handles += outlier_handles
                    all_labels  += outlier_labels


            if len(score_setup) > 2 and len(score_setup) % 2 == 1:
                subplot_axes[-1].axis("off")

            fig.legend(
                all_handles,
                all_labels,
                loc="upper right",
                ncol=1,
                frameon=True,
            )

            _set_suptitle(
                fig,
                custom_sup_title,
            )
            fig.savefig(f"{output_dir}/{filename}.png")
            plt.close()


def _generate_ensemble_scores_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    debug,
):
    """Generate Ensemble Score Plots."""
    model_versions = list(models_data[next(iter(models_data))].keys())
    custom_lines = [
        Line2D([0], [0], color=plot_settings.modelcolors[model_version], lw=2)
        for model_version in model_versions
    ]

    # initialise filename
    base_filename = f"ensemble_scores_{parameter}"

    headers = [data["header"] for data in models_data[next(iter(models_data))].values()]
    total_start_date, total_end_date = get_total_dates_from_headers(headers)
    # pylint: disable=line-too-long
    sup_title = f"""{parameter}: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""  # noqa: E501
    # pylint: enable=line-too-long
    if debug:
        print("Generating ensemble plots.")
    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["regular_ens_scores"],
        sup_title,
        models_data,
        custom_lines,
        debug=False,
    )

    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["ens_cat_scores"],
        sup_title,
        models_data,
        custom_lines,
        debug=False,
    )
