"""Calculate ensemble scores from parsed data."""
# Standard library
import re
from datetime import datetime
from pathlib import Path
from pprint import pprint

# Third-party
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

# Local
from .config.plot_settings import PlotSettings
from .total_scores import _customise_ax
from .total_scores import _save_figure
from .total_scores import _set_ylim

# pylint: disable=no-name-in-module
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import total_score_range

ens_plot_function_dict = {
    "OUTLIERS": None,
    "RPS": None,
    "RPS_REF": None,
    "RPSS": None,
    "RANK": None,
    "REL": None,
    "RES": None,
    "BS": None,
    "BS_REF": None,
    "BSS": None,
    "BSSD": None,
    "REL_DIA": None,
}


def memoize(func):
    cache = {}

    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    return wrapper


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
                    loaded_Atab = Atab(file=file_path, sep=" ")

                    header = loaded_Atab.header
                    df = loaded_Atab.data
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
    print("PLOT SETUP ", plot_setup)
    if not lt_ranges:
        lt_ranges = "19-24,13-18"
        # lt_ranges = "19-24"
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
            print("MODELS DATA ", model_data[next(iter(model_data.keys()))].keys())
            _generate_ensemble_scores_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )


def num_sort(test_string):
    return list(map(int, re.findall(r"\d+", test_string)))[0]


from .station_scores import _calculate_figsize


def _initialize_plots(labels: list, scores: list, lines: list[Line2D]):
    num_cols = 1
    num_rows = len(scores)
    figsize = _calculate_figsize(num_rows, num_cols, (8, 4), (2, 2))  # (10, 6.8)
    fig, axes = plt.subplots(
        nrows=num_rows,
        ncols=num_cols,
        tight_layout=True,
        figsize=figsize,
        dpi=500,
        squeeze=False,
    )
    print("LABELS ", labels)
    fig.legend(
        lines,
        labels,
        loc="upper right",
        ncol=1,
        frameon=False,
    )
    fig.tight_layout(w_pad=8, h_pad=4, rect=[0.05, 0.05, 0.90, 0.90])
    plt.subplots_adjust(bottom=0.15)
    return fig, axes.ravel()


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
    filename = base_filename
    print("MODEL COLOR LINES ", len(models_color_lines))
    for idx, score_setup in enumerate(plot_scores_setup):
        print(
            "SCORE SETUP ",
            score_setup,
            models_data.keys(),
            models_data[next(iter(models_data.keys()))].keys(),
        )
        print("SUP TITLE ", sup_title)
        fig, subplot_axes = _initialize_plots(
            list(models_data[next(iter(models_data.keys()))].keys()),
            score_setup,
            models_color_lines,
        )
        print("SCORE SETUP ", score_setup)
        if "RANK" in score_setup:
            for score_idx, score in enumerate(score_setup):
                filename = base_filename
                fig, subplot_axes = _initialize_plots(
                    list(models_data[next(iter(models_data.keys()))].keys()),
                    list(models_data.keys()),
                    models_color_lines,
                )

                for ltr_idx, (ltr, model_data) in enumerate(models_data.items()):
                    filename += f"_{ltr}"
                    ax = subplot_axes[ltr_idx]
                    for model_idx, (model_version, data) in enumerate(
                        model_data.items()
                    ):
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
                        ax.set_xlabel(f"RANK, LT: {ltr}")
                        print("MODE RANKS ", model_ranks)
                        ax.bar(
                            np.arange(len(model_ranks)) + model_idx * 0.25,
                            ranks,
                            width=0.25,
                            color=model_plot_color,
                        )

                    fig.suptitle(
                        f"RANK: {sup_title}",
                        horizontalalignment="center",
                        verticalalignment="top",
                        fontdict={
                            "size": 6,
                            "color": "k",
                        },
                        bbox={"facecolor": "none", "edgecolor": "grey"},
                    )

                fig.savefig(f"{output_dir}/{filename}_RANK.png")
        elif any(["REL_DIA" in score for score in score_setup]):
            for score_idx, score in enumerate(score_setup):
                filename = base_filename
                fig, subplot_axes = _initialize_plots(
                    list(models_data[next(iter(models_data.keys()))].keys()),
                    list(models_data.keys()),
                    models_color_lines,
                )
                threshold = re.search(r"\(.*?\)", score).group()
                for ltr_idx, (ltr, model_data) in enumerate(models_data.items()):
                    filename += f"_{ltr}"
                    ax = subplot_axes[ltr_idx]
                    ax.plot(
                        np.arange(0, 1.1, 0.1),
                        np.arange(0, 1.1, 0.1),
                        color="black",
                        fillstyle="none",
                        linestyle="--",
                        alpha=0.2,
                    )
                    ax.set_ylabel("Observed Relative Frequency")
                    ax.set_xlabel(f"Forecast Probability, LT: {ltr}")
                    ax.set_xlim(0, 1)
                    ax.set_ylim(0, 1)

                    box = ax.get_position()
                    width = box.width
                    height = box.height
                    l, b, h, w = 0.8, 0.025, 0.3, 0.2
                    w *= width
                    h *= height
                    inax_position = ax.transAxes.transform([l, b])
                    transFigure = fig.transFigure.inverted()
                    infig_position = transFigure.transform(inax_position)
                    ax2 = fig.add_axes([*infig_position, w, h])

                    [unit] = model_data[next(iter(model_data.keys()))]["header"]["Unit"]
                    for model_idx, (model_version, data) in enumerate(
                        model_data.items()
                    ):
                        model_plot_color = PlotSettings.modelcolors[model_idx]
                        FBIN_indices = [
                            index
                            for index in list(data["df"]["Total"].index)
                            if f"FBIN{threshold}" in index
                        ]
                        OBIN_indices = [
                            index
                            for index in list(data["df"]["Total"].index)
                            if f"OBIN{threshold}" in index
                        ]
                        NBIN_indices = [
                            index
                            for index in list(data["df"]["Total"].index)
                            if f"NBIN{threshold}" in index
                        ]
                        OF_indices = [
                            index
                            for index in list(data["df"]["Total"].index)
                            if f"OF{threshold}" in index
                        ]
                        FBIN_values = data["df"]["Total"][FBIN_indices]
                        OBIN_values = data["df"]["Total"][OBIN_indices]
                        NBIN_values = data["df"]["Total"][NBIN_indices]
                        OF_value = data["df"]["Total"][OF_indices]
                        ax.plot(
                            FBIN_values,
                            OBIN_values,
                            color=model_plot_color,
                            marker="D",
                            fillstyle="none",
                        )

                        ax2.bar(
                            np.arange(len(NBIN_values)) + model_idx * 0.25,
                            NBIN_values,
                            width=0.25,
                            color=model_plot_color,
                        )

                    ax.plot(
                        np.arange(0, 1.1, 0.1),
                        [OF_value] * 11,
                        color="black",
                        fillstyle="none",
                        linestyle="--",
                        alpha=0.2,
                    )

                    bisect_zero = (1 - np.tan(np.pi / 8)) * OF_value
                    bisect_one = bisect_zero + np.tan(np.pi / 8)
                    print("OSJKJC ", bisect_one, bisect_zero)
                    ax.plot(
                        [0, 1],
                        [
                            (1 - np.tan(np.pi / 8)) * OF_value,
                            OF_value + (1 - OF_value) * np.tan(np.pi / 8),
                        ],
                        color="black",
                        fillstyle="none",
                        linestyle="--",
                        alpha=0.2,
                    )
                    ax.set_title(f"{parameter} {threshold[1:-1]} {unit}")

                    ax2.set_xticks([])
                    ax2.set_title("N")
                    ax2.set_yticks(np.round([max(NBIN_values)], -3))

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
                fig.savefig(f"{output_dir}/{filename}_REL_DIA.png")

        else:
            filename = base_filename
            fig, subplot_axes = _initialize_plots(
                list(models_data[next(iter(models_data.keys()))].keys()),
                score_setup,
                models_color_lines,
            )
            ltr_sorted = sorted(
                list(models_data.keys()), key=lambda x: int(x.split("-")[0])
            )
            x_int = list(range(len(ltr_sorted)))
            print("LTR LTR LTR ", ltr_sorted, x_int)
            for score_idx, score in enumerate(score_setup):
                ax = subplot_axes[score_idx]
                filename += f"_{score}"
                for ltr_idx, (ltr, model_data) in enumerate(models_data.items()):
                    # print("MMMM ", model_data)
                    pass
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
                print(ltr_sorted)
                ax.set_xticks(x_int, ltr_sorted)

                ax.set_title(f"{parameter}: {score}")

                ax.grid(which="major", color="#DDDDDD", linewidth=0.8)
                ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=0.5)
                ax.set_xlabel("Lead-Time Range (h)")

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
    print("HEADERS ", total_end_date, total_start_date)
    '''
    headers = [
        data[sorted(list(data.keys()), key=lambda x: int(x.split("-")[0]))[-1]][
            "header"
        ]
        for data in models_data.values()
    ]
    total_start_date = min(
        datetime.strptime(header["Start time"][0], "%Y-%m-%d") for header in headers
    )

    total_end_date = max(
        datetime.strptime(header["End time"][0], "%Y-%m-%d") for header in headers
    )

    model_info = (
        ""
        if len(model_versions) > 1
        else f"Model: {headers[0]['Model version'][0]} | \n"
    )

    sup_title = (
        model_info
        + f"""Period: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""
    )
    '''
    sup_title = f"""{parameter}\nPeriod: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""

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
