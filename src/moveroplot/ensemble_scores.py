"""Calculate ensemble scores from parsed data."""
# Standard library
import re
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Tuple

# Third-party
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# Local
from .config.plot_settings import PlotSettings
from .station_scores import _calculate_figsize

# pylint: disable=no-name-in-module
from .utils.atab import Atab


# pylint: disable=too-many-arguments,too-many-locals
def collect_relevant_files(
    input_dir, file_prefix, file_postfix, debug, model_plots, parameter, lt_ranges
):
    corresponding_files_dict = {}
    extracted_model_data = {}
    # for dbg purposes:
    files_list = []
    for model in model_plots:
        source_path = Path(f"{input_dir}/{model}")
        for file_path in source_path.glob(f"{file_prefix}*{parameter}{file_postfix}"):
            if file_path.is_file():
                ltr_match = re.search(r"(\d{2})-(\d{2})", file_path.name)
                if ltr_match:
                    lt_range = ltr_match.group()
                else:
                    raise IOError(
                        f"The filename {file_path.name} does not contain a LT range."
                    )

                in_lt_ranges = True
                if lt_ranges:
                    in_lt_ranges = lt_range in lt_ranges

                if in_lt_ranges:
                    # extract header & dataframe
                    loaded_atab = Atab(file=file_path, sep=" ")
                    header = loaded_atab.header
                    df = loaded_atab.data
                    # clean df
                    df = df.replace(float(header["Missing value code"][0]), np.NaN)
                    df.set_index(keys="Score", inplace=True)

                    # add information to dict
                    if lt_range not in corresponding_files_dict:
                        corresponding_files_dict[lt_range] = {}

                    corresponding_files_dict[lt_range][model] = {
                        "header": header,
                        "df": df,
                    }
                    # add path of file to list of relevant files
                    files_list.append(file_path)

    if debug:
        print(f"\nFor parameter: {parameter} these files are relevant:\n")
        pprint(files_list)

    extracted_model_data = corresponding_files_dict
    return extracted_model_data


def _ensemble_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    if not lt_ranges:
        lt_ranges = "07-12,13-18,19-24"
    for model_plots in plot_setup["model_versions"]:
        for parameter, scores in plot_setup["parameter"].items():
            model_data = {}
            model_data = collect_relevant_files(
                input_dir,
                file_prefix,
                file_postfix,
                debug,
                model_plots,
                parameter,
                lt_ranges,
            )
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
        dpi=500,
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
        index
        for index in list(data["df"]["Total"].index)
        if f"{prefix}{threshold}" in index
    ]
    return data["df"]["Total"][indices]


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
            custom_sup_title = f"RANK: {sup_title}"
            filename += "_RANK"
            for score_idx, score in enumerate(score_setup):
                fig, subplot_axes = _initialize_plots(
                    2 if len(models_data.keys()) > 1 else 1,
                    (len(models_data.keys()) + 1) // 2,
                )
                subplot_axes = subplot_axes.ravel()
                for ltr_idx, (ltr, model_data) in enumerate(models_data.items()):
                    filename += f"_{ltr}"
                    ax = subplot_axes[ltr_idx]
                    ax.set_xlabel("RANK")
                    ax.set_title(f"{parameter}, LT: {ltr}")
                    for model_idx, data in enumerate(model_data.values()):
                        model_plot_color = PlotSettings.modelcolors[model_idx]
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
                if len(models_data.keys()) > 2 and len(models_data.keys()) % 2 == 1:
                    subplot_axes[-1].axis("off")
        elif any("REL_DIA" in score for score in score_setup):
            fig, subplot_axes = _initialize_plots(
                len(score_setup), len(models_data.keys()), (6, 6)
            )
            for score_idx, score in enumerate(score_setup):
                filename += f"_{score}"
                print("SCORE ", score)
                threshold = re.search(r"\(.*?\)", score).group()
                for ltr_idx, (ltr, model_data) in enumerate(models_data.items()):
                    print("LTR LTR ", ltr)
                    ax = subplot_axes[score_idx][ltr_idx]
                    ax.set_ylabel("Observed Relative Frequency")
                    ax.set_xlabel("Forecast Probability")
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)
                    [unit] = model_data[next(iter(model_data.keys()))]["header"]["Unit"]
                    ax.set_title(f"{parameter} {threshold[1:-1]} {unit}, LT: {ltr}")
                    sample_subplot = _add_sample_subplot(fig, ax)

                    for model_idx, data in enumerate(model_data.values()):
                        model_plot_color = PlotSettings.modelcolors[model_idx]
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
            filename += f"_{'_'.join(models_data.keys())}"
        else:
            fig, subplot_axes = _initialize_plots(
                2 if len(score_setup) > 1 else 1,
                (len(score_setup) + 1) // 2,
            )
            subplot_axes = subplot_axes.ravel()
            fig.legend(
                models_color_lines,
                list(models_data[next(iter(models_data.keys()))].keys()),
                loc="upper right",
                ncol=1,
                frameon=False,
            )
            ltr_sorted = sorted(
                list(models_data.keys()), key=lambda x: int(x.split("-")[0])
            )
            x_int = list(range(len(ltr_sorted)))
            for score_idx, score in enumerate(score_setup):
                ax = subplot_axes[score_idx]
                filename += f"_{score}"
                for model_idx, model_name in enumerate(
                    models_data[next(iter(ltr_sorted))].keys()
                ):
                    model_plot_color = PlotSettings.modelcolors[model_idx]
                    y_values = [
                        models_data[ltr][model_name]["df"]["Total"].loc[score]
                        for ltr in ltr_sorted
                    ]
                    ax.plot(
                        x_int,
                        y_values,
                        color=model_plot_color,
                        marker="D",
                        fillstyle="none",
                    )

                ax.set_ylabel(f"{score}")
                ax.set_xticks(x_int, ltr_sorted)
                ax.set_title(f"{parameter}: {score}")
                ax.grid(which="major", color="#DDDDDD", linewidth=0.8)
                ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=0.5)
                ax.set_xlabel("Lead-Time Range (h)")

            if len(score_setup) > 2 and len(score_setup) % 2 == 1:
                subplot_axes[-1].axis("off")

        fig.suptitle(
            custom_sup_title,
            horizontalalignment="center",
            verticalalignment="top",
            fontdict={
                "size": 6,
                "color": "k",
            },
            bbox={"facecolor": "none", "edgecolor": "grey"},
        )

        fig.legend(
            models_color_lines,
            list(models_data[next(iter(models_data.keys()))].keys()),
            loc="upper right",
            ncol=1,
            frameon=False,
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
    model_plot_colors = PlotSettings.modelcolors
    model_versions = list(models_data[next(iter(models_data))].keys())
    custom_lines = [
        Line2D([0], [0], color=model_plot_colors[i], lw=2)
        for i in range(len(model_versions))
    ]

    # initialise filename
    base_filename = (
        f"ensemble_scores_{parameter}"
        if len(model_versions) == 1
        else f"ensemble_scores_{parameter}"
    )

    headers = [data["header"] for data in models_data[next(iter(models_data))].values()]
    total_start_date = min(
        datetime.strptime(header["Start time"][0], "%Y-%m-%d") for header in headers
    )

    total_end_date = max(
        datetime.strptime(header["End time"][0], "%Y-%m-%d") for header in headers
    )
    # pylint: disable=line-too-long
    sup_title = f"""{parameter}
    Period: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""  # noqa: E501
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
