"""Calculate total scores from parsed data."""
# Standard library
import re

# Third-party
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

# First-party
from moveroplot.config import plot_settings

# Local
from .load_files import load_relevant_files
from .plotting import get_total_dates_from_headers

# pylint: disable=no-name-in-module
from .utils.parse_plot_synop_ch import cat_total_score_range
from .utils.parse_plot_synop_ch import total_score_range
from .utils.set_ylims import set_ylim

# pylint: enable=no-name-in-module

plt.rcParams.update(
    {
        "axes.titlesize": "medium",
        "axes.labelsize": "small",
        "legend.title_fontsize": "small",
    }
)


def _total_score_transformation(df, header):
    df = df.replace(float(header["Missing value code"][0]), np.NaN)
    df.set_index(keys="Score", inplace=True)
    return df


# pylint: disable=too-many-arguments,too-many-locals
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
            model_data = load_relevant_files(
                input_dir,
                file_prefix,
                file_postfix,
                debug,
                model_plots,
                parameter,
                lt_ranges,
                ltr_first=False,
                transform_func=_total_score_transformation,
            )
            if not model_data:
                print(f"No matching files found with given ltr {lt_ranges}")
                return
            _generate_total_scores_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )


# PLOTTING PIPELINE FOR TOTAL SCORES PLOTS
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


def _clear_empty_axes_if_necessary(subplot_axes, idx):
    # remove empty ``axes`` instances
    if (idx + 1) % 4 != 0:
        for ax in subplot_axes[(idx + 1) % 4 :]:
            ax.axis("off")


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
    plt.tight_layout(w_pad=8, h_pad=3, rect=(0.05, 0.05, 0.90, 0.90))
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
    plt.close()


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
        print("Entering plot_and_save_scores.")
    filename = base_filename
    fig, subplot_axes = _initialize_plots(models_color_lines, models_data.keys())

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
            _save_figure(
                output_dir, filename, sup_title, fig, subplot_axes, current_plot_idx - 1
            )
            fig, subplot_axes = _initialize_plots(
                models_color_lines, models_data.keys()
            )
            filename = base_filename
            current_plot_idx += current_plot_idx % 4
        for model_idx, (key, data) in enumerate(models_data.items()):
            model_plot_color = plot_settings.modelcolors[key]
            # sorted lead time ranges
            ltr_sorted = sorted(list(data.keys()), key=lambda x: int(x.split("-")[0]))
            x_int = list(range(len(ltr_sorted)))

            # extract header from data & create title
            header = data[ltr_sorted[-1]]["header"]
            unit = header["Unit"][0]
            # get ax, to add plot to
            ax = subplot_axes[current_plot_idx % 4]
            y_label = ",".join(score_setup)
            ax.set_ylabel(f"{y_label.upper()} ({unit})")

            if len(score_setup) > 2:
                raise ValueError(
                    f"""Maximum two scores are allowed in one plot.
                    Got {len(score_setup)}"""
                )
            for score_idx, score in enumerate(score_setup):
                if model_idx == 0:
                    filename += f"{score}_"
                y_values = [data[ltr]["df"]["Total"].loc[score] for ltr in ltr_sorted]
                ax.plot(
                    x_int,
                    y_values,
                    color=model_plot_color,
                    linestyle=plot_settings.line_styles[score_idx],
                    marker="D",
                    fillstyle="none",
                    label=f"{score_setup[0].upper()}",
                )
                set_ylim(
                    param=parameter,
                    score_range=total_score_range,
                    cat_score_range=cat_total_score_range,
                    score=score_setup[0],
                    ax=ax,
                    y_values=[
                        data[ltr]["df"]["Total"].loc[score] for ltr in ltr_sorted
                    ],
                )
                # Add reference lines
                ymin, ymax = ax.get_ylim()
                if ymin <= 0 <= ymax:
                    ax.axhline(y=0, color="black",         linestyle="--", linewidth=0.5)
                if score.startswith("FBI"):
                    ax.axhline(y=1, color="black", linestyle="--", linewidth=0.5)

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
        full_figure = current_plot_idx > 0 and (current_plot_idx + 1) % 4 == 0
        last_plot = idx == len(plot_scores_setup) - 1
        if full_figure or last_plot:
            _save_figure(
                output_dir, filename, sup_title, fig, subplot_axes, current_plot_idx
            )
            fig, subplot_axes = _initialize_plots(
                models_color_lines, models_data.keys()
            )
            filename = base_filename

        current_plot_idx += 1


def _generate_total_scores_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    debug,
):
    """Generate Total Score Plots."""
    model_versions = list(models_data.keys())
    custom_lines = [
        Line2D([0], [0], color=plot_settings.modelcolors[model_version], lw=2)
        for model_version in model_versions
    ]

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
    total_start_date, total_end_date = get_total_dates_from_headers(headers)

    model_info = (
        ""
        if len(model_versions) > 1
        else f"Model: {headers[0]['Model version'][0]} | \n"
    )
    # pylint: disable=line-too-long
    period_info = f"""Period: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""  # noqa: E501
    # pylint: enable=line-too-long
    sup_title = model_info + period_info
    if debug:
        print("Try to generate total score plots.")
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
