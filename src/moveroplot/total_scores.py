"""Calculate Total score from parsed data."""
# Standard library
from pathlib import Path
from pprint import pprint
from datetime import datetime
from datetime import date
import re

# Third-party
import matplotlib.pyplot as plt
import numpy as np
from .config.plot_settings import PlotSettings

# Third-party
from matplotlib.lines import Line2D

# Local
# pylint: disable=no-name-in-module
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import total_score_range

# pylint: enable=no-name-in-module

plt.rcParams.update(
    {
        "axes.titlesize": "medium",
        "axes.labelsize": "small",
        "legend.title_fontsize": "small",
    }
)


def collect_relevant_files(
    input_dir, file_prefix, file_postfix, debug, model_plots, parameter, lt_ranges
):
    """Collect all data from each model.

    Args:
        file_prefix (str): prefix of files we're looking for (i.e. total_scores)
        file_postfix (str): postfix of files we're looking for (i.e. .dat)
        debug (bool): add debug messages command prompt
        source_path (Path): path to directory, where source files are
        parameter (str): parameter of interest

    Returns:
        dict: dictionary conrains all available lead time range dataframes for parameter
    # collect the files to this parameter in the corresponding files dict.
    # the keys in this dict are the available lead time ranges for the current parameter.

    """  # noqa: E501
    corresponding_files_dict = {}
    extracted_model_data = {}

    # for dbg purposes:
    files_list = []
    for model in model_plots:
        source_path = Path(f"{input_dir}/{model}")
        corresponding_files_dict = {}
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
                    corresponding_files_dict[lt_range] = {
                        # 'path':file_path,
                        "header": header,
                        "df": df,
                    }

                    # add path of file to list of relevant files
                    files_list.append(file_path)
        extracted_model_data[model] = corresponding_files_dict
    if debug:
        print(f"\nFor parameter: {parameter} these files are relevant:\n")
        pprint(files_list)

    # print("EXTRACTED MODEL DATA IN TOTAL SCORES ", extracted_model_data)
    return extracted_model_data


# enter directory / read total_scores files / call plotting pipeline
# pylint: disable=pointless-string-statement,too-many-arguments,too-many-locals
def _total_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    # pylint: disable=line-too-long
    """Read all ```ATAB``` files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>.

        Extract relevant information (parameters/scores) from these files into a dataframe.
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists.


    Args:
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. time_scores)
        file_postfix (str): postfix of files (i.e. '.dat')
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd)
        output_dir (str): output directory (i.e. plots/)
        model_versions (str): model_versions of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        debug (bool): print further comments & debug statements

    """  # noqa: E501
    # pylint: enable=line-too-long
    print("\n--- initialising total scores pipeline")
    # tmp; define debug = True, to show debug statements for total_scores only
    # debug = True
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
            _generate_total_scores_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )


# PLOTTING PIPELINE FOR TOTAL SCORES PLOTS
def _set_ylim(param, score, ax, debug):  # pylint: disable=unused-argument
    # define limits for yaxis if available
    regular_param = (param, "min") in total_score_range.columns
    regular_scores = score in total_score_range.index

    if regular_param and regular_scores:
        lower_bound = total_score_range[param]["min"].loc[score]
        upper_bound = total_score_range[param]["max"].loc[score]
        # if debug:
        #     print(
        #         f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
        # )
        if lower_bound != upper_bound:
            ax.set_ylim(lower_bound, upper_bound)

    # TODO: add computation of y-lims for cat & ens scores


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
    steps = len(x_ticks) // 5
    skip_indices = slice(None, None, steps) if steps > 0 else slice(None)
    ax.set_xticks(range(len(x_ticks))[skip_indices], x_ticks[skip_indices])
    print("LEN C C", len(x_ticks))
    # ax.tick_params(axis="x")
    ax.autoscale(axis="y")


def _clear_empty_axes_if_necessary(subplot_axes, idx):
    # remove empty ``axes`` instances
    if (idx + 1) % 4 != 0:
        [ax.axis("off") for ax in subplot_axes[(idx + 1) % 4 :]]


def _initialize_plots(lines: list[Line2D], labels: list):
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(
        nrows=2, ncols=2, tight_layout=True, figsize=(10, 10), dpi=200
    )
    fig.legend(
        lines,
        labels,
        loc="upper right",
        ncol=1,
        frameon=False,
    )
    plt.tight_layout(w_pad=8, h_pad=3, rect=[0.05, 0.05, 0.90, 0.90])
    return fig, [ax0, ax1, ax2, ax3]


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
    fig, subplot_axes = _initialize_plots(models_color_lines, models_data.keys())
    for idx, score_setup in enumerate(plot_scores_setup):
        for model_idx, data in enumerate(models_data.values()):
            model_plot_color = PlotSettings.modelcolors[model_idx]
            # sorted lead time ranges
            ltr_sorted = sorted(list(data.keys()), key=lambda x: int(x.split("-")[0]))
            x_int = list(range(len(ltr_sorted)))

            # extract header from data & create title
            header = data[ltr_sorted[-1]]["header"]
            unit = header["Unit"][0]
            # get ax, to add plot to
            ax = subplot_axes[idx % 4]
            # ax.set_xlim(x_int[0], x_int[-1])
            y_label = ",".join(score_setup)
            ax.set_ylabel(f"{y_label.upper()} ({unit})")

            if len(score_setup) > 2:
                raise ValueError(
                    f"Maximum two scores are allowed in one plot. Got {len(score_setup)}"
                )
            for score_idx, score in enumerate(score_setup):
                if model_idx == 0:
                    filename += f"{score}_"
                _set_ylim(param=parameter, score=score_setup[0], ax=ax, debug=debug)
                y_values = [data[ltr]["df"]["Total"].loc[score] for ltr in ltr_sorted]
                ax.plot(
                    x_int,
                    y_values,
                    color=model_plot_color,
                    linestyle=PlotSettings.line_styles[score_idx],
                    marker="D",
                    fillstyle="none",
                    label=f"{score_setup[0].upper()}",
                )

            # Generate a legend if two scores in one subplot
            if len(score_setup) > 1:
                sub_plot_legend = ax.legend(
                    score_setup,
                    loc="upper right",
                    markerscale=0.9,
                    bbox_to_anchor=(1.35, 1.05),
                )
                # make lines in the legend always black
                for line in sub_plot_legend.get_lines():
                    line.set_color("black")

        # customise grid, title, xticks, legend of current ax
        _customise_ax(
            parameter=parameter,
            scores=score_setup,
            x_ticks=ltr_sorted,
            grid=True,
            ax=ax,
        )

        # save filled figure & re-set necessary for next iteration
        full_figure = idx > 0 and (idx + 1) % 4 == 0
        last_plot = idx == len(plot_scores_setup) - 1
        if full_figure or last_plot:
            _save_figure(output_dir, filename, sup_title, fig, subplot_axes, idx)
            fig, subplot_axes = _initialize_plots(
                models_color_lines, models_data.keys()
            )
            filename = base_filename


def _generate_total_scores_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    debug,
):
    """Generate Total Scores Plot."""
    model_plot_colors = PlotSettings.modelcolors
    model_versions = list(models_data.keys())
    custom_lines = [
        Line2D([0], [0], color=model_plot_colors[i], lw=2)
        for i in range(len(model_versions))
    ]
    # get correct parameter, i.e. if parameter=T_2M_KAL --> param=T_2M*
    param = check_params(param=parameter, verbose=False)

    # initialise filename
    base_filename = (
        f"total_scores_{model_versions[0]}_{parameter}_"
        if len(model_versions) == 1
        else f"total_scores_{parameter}_"
    )

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

    # plot regular scores
    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["regular_scores"],
        sup_title,
        models_data,
        custom_lines,
        debug=False,
    )
    # plot categorial scores
    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["cat_scores"],
        sup_title,
        models_data,
        custom_lines,
        debug=False,
    )
