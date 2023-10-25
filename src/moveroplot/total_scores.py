# IMPORTS
# Standard library
from pathlib import Path

# Third-party
import matplotlib.pyplot as plt
import numpy as np

# Local
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import total_score_range

plt.rcParams.update(
    {
        "axes.titlesize": "medium",
        "axes.labelsize": "small",
        "legend.title_fontsize": "small",
    }
)
# Standard library
from pprint import pprint  # noqa: E402


def collect_relevant_files(file_prefix, file_postfix, debug, source_path, parameter):
    """Collect all files corresponding to current parameter in 'corresponding_files_dict'.  # noqa: E501
    Args:
        file_prefix (str): prefix of files we're looking for (i.e. total_scores)
        file_postfix (str): postfix of files we're looking for (i.e. .dat)
        debug (bool): add debug messages command prompt
        source_path (Path): path to directory, where source files are
        parameter (str): parameter of interest

    Returns:
        dict: dictionary containing all available lead time range (ltr) dataframes for parameter
    # collect the files to this parameter in the corresponding files dict.
    # the keys in this dict are the available lead time ranges for the current parameter.
    """  # noqa: E501
    corresponding_files_dict = {}

    # for dbg purposes:
    files_list = []
    for file_path in source_path.glob(f"{file_prefix}*{parameter}{file_postfix}"):
        if file_path.is_file():
            # check, that the corresponding path belongs to a file
            # and not to a sub-directory
            # lt_range = key for corresponding_files_dict
            # TODO:change here, if ltr is longer than 5 chars
            lt_range = file_path.name[
                len(file_prefix) : len(file_prefix) + 5  # noqa: E203
            ]
            # extract header & dataframe
            header = Atab(file=file_path, sep=" ").header
            df = Atab(file=file_path, sep=" ").data

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
    if debug:
        print(f"\nFor parameter: {parameter} these files are relevant:\n")
        pprint(files_list)
        print(
            f"""\nThese files have been parsed & combined in the 'corresponding_files_dict'.
            Each key (lt-range) has a subdict with two keys: {corresponding_files_dict['19-24'].keys()}\n"""  # noqa: E501
        )

    return corresponding_files_dict


# enter directory / read total_scores files / call plotting pipeline
def _total_scores_pipeline(
    params_dict,
    plot_scores,
    plot_params,
    plot_cat_scores,
    plot_cat_params,
    plot_cat_thresh,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    season,
    model_version,
    grid,
    debug,
) -> None:
    """Read all ```ATAB``` files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>
        Extract relevant information (parameters/scores) from these files into a dataframe.
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists.


    Args:
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
    print("\n--- initialising total scores pipeline")
    # tmp; define debug = True, to show debug statements for total_scores only
    debug = True

    source_path = Path(f"{input_dir}/{season}/{model_version}")
    for parameter in params_dict:
        corresponding_files_dict = collect_relevant_files(
            file_prefix, file_postfix, debug, source_path, parameter
        )

        # pass dict to plotting pipeline
        _generate_total_scores_plot(
            data=corresponding_files_dict,
            parameter=parameter,
            plot_scores=plot_scores,
            plot_params=plot_params,
            plot_cat_scores=plot_cat_scores,
            plot_cat_params=plot_cat_params,
            plot_cat_thresh=plot_cat_thresh,
            # TODO: add ens params/thresh/scores
            output_dir=output_dir,
            grid=grid,
            debug=debug,
        )
    return


# PLOTTING PIPELINE FOR TOTAL SCORES PLOTS


def _set_ylim(param, score, ax, debug):
    # define limits for yaxis if available
    regular_param = (param, "min") in total_score_range.columns
    regular_score = score in total_score_range.index

    if regular_param and regular_score:
        lower_bound = total_score_range[param]["min"].loc[score]
        upper_bound = total_score_range[param]["max"].loc[score]
        # if debug:
        #     print(
        #         f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
        # )
        if lower_bound != upper_bound:
            ax.set_ylim(lower_bound, upper_bound)

    # TODO: add computation of y-lims for cat & ens scores

    return


def _customise_ax(parameter, score, x_ticks, grid, ax):
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
    ax.set_title(f"{parameter}: {score}")
    ax.set_xlabel("Lead-Time Range (h)")
    ax.legend(fontsize=6)
    ax.set_xticks(range(len(x_ticks)), x_ticks)
    return


def _clear_empty_axes(subplot_axes, idx):
    # remove empty ``axes`` instances
    i = 1
    while (idx % 4 + i) < 4:
        ax = subplot_axes[idx % 4 + i]
        ax.axis("off")
        i += 1
    return


def _save_figure(output_dir, filename):
    print(f"---\t\tsaving: {output_dir}/{filename[:-1]}.png")
    plt.savefig(f"{output_dir}/{filename[:-1]}.png")
    plt.clf()
    return


def _generate_total_scores_plot(
    data,
    parameter,
    plot_params,
    plot_scores,
    plot_cat_scores,
    plot_cat_params,
    plot_cat_thresh,
    output_dir,
    grid,
    debug,
):
    """Generate Total Scores Plot."""
    if debug:
        print("--- starting plotting pipeline")
        print("---\t1) map parameter (i.e. TD_2M_KAL --> TD_2M*)")

    # get correct parameter, i.e. if parameter=T_2M_KAL --> param=T_2M*
    param = check_params(
        param=parameter, verbose=False
    )  # TODO: change False back to debug

    if debug:
        print("---\t2) check if output_dir exists (& create it if necessary)")
    # check (&create) output directory for total scores plots
    # output_dir = f"{output_dir}/total_scores"
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    if debug:
        print("---\t3) initialise figure with a 2x2 subplots grid")
    # create 2x2 subplot grid
    fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(
        nrows=2, ncols=2, tight_layout=True, figsize=(10, 10), dpi=200
    )

    subplot_axes = {
        0: ax0,
        1: ax1,
        2: ax2,
        3: ax3,
    }  # hash map to access correct axes later on

    # ltr_unsorted  ->  unsorted lead time ranges
    # ltr_sorted    ->  sorted lead time ranges (used for x-tick-labels later on )
    ltr_unsorted, ltr_sorted = list(data.keys()), []
    ltr_start_times_sorted = sorted([int(lt.split("-")[0]) for lt in ltr_unsorted])
    for idx, ltr_start in enumerate(ltr_start_times_sorted):
        for ltr in ltr_unsorted:
            if ltr.startswith(str(ltr_start).zfill(2)):
                ltr_sorted.insert(idx, ltr)

    # re-name & create x_int list, s.t. np.arrays are plottet against each other
    x_ticks = ltr_sorted
    x_int = list(range(len(ltr_sorted)))

    if debug:
        print("---\t4) create x-axis")
        print("---\t\tUnsorted ltr list:\t\t{ltr_unsorted}")
        print("---\t\tSorted ltr start times list:\t{ltr_start_times_sorted}")
        print("---\t\tSorted ltr list (= x-ticks):\t{ltr_sorted}")
        print("---\t\tx_int =\t\t\t\t{x_int}")

    # extract header from data & create title
    header = data[ltr_sorted[-1]]["header"]
    footer = f"""Model: {header['Model version'][0]} |
    Period: {header['Start time'][0]} - {header['End time'][0]} | © MeteoSwiss"""
    unit = header["Unit"][0]

    # initialise filename
    filename = f"total_scores_{parameter}_"

    # scores = params_dict[parameter] # this is a list of lists

    # REGULAR SCORES PLOTTING PIPELINE
    if debug:
        print(
            """---\t5) plot REGULAR parameter/scores
            (Because, regular & categorical scores
            should not be mixed on the same figure.)"""
        )

    if plot_scores and plot_params:
        regular_scores = plot_scores.split(",")
        # the idx of a score, maps the score to the corresponding subplot axes instance
        for idx, score in enumerate(regular_scores):
            # if debug:
            #     print(f"--- plotting:\t{param}/{score}")

            multiplt = False

            # save filled figure & re-set necessary for next iteration
            if idx > 0 and idx % 4 == 0:
                # add title to figure
                plt.suptitle(
                    footer,
                    horizontalalignment="center",
                    verticalalignment="top",
                    fontdict={
                        "size": 6,
                        "color": "k",
                    },
                    bbox=dict(
                        facecolor="none",
                        edgecolor="grey",
                    ),
                )
                _save_figure(output_dir=output_dir, filename=filename)
                fig, ((ax0, ax1), (ax2, ax3)) = plt.subplots(
                    nrows=2, ncols=2, tight_layout=True, figsize=(10, 10), dpi=200
                )
                subplot_axes = {0: ax0, 1: ax1, 2: ax2, 3: ax3}
                # reset filename
                filename = f"total_scores_{parameter}_"

            # get ax, to add plot to
            ax = subplot_axes[idx % 4]
            ax.set_xlim(x_int[0], x_int[-1])
            ax.set_ylabel(f"{score.upper()} ({unit})")

            # plot two scores on one sub-plot
            if "/" in score:
                multiplt = True
                scores = score.split("/")
                filename += f"{scores[0]}_{scores[1]}_"
                _set_ylim(param=param, score=scores[0], ax=ax, debug=debug)

                # get y0, y1 from dfs
                if debug and idx == 0:
                    print(
                        f"""---\t6) collect the data corresponding to {score}
                        from all dataframes in the data dict in y-list"""
                    )
                    print("---\t7) plot y-list against x_int")
                y0, y1 = [], []
                for ltr in ltr_sorted:
                    y0.append(data[ltr]["df"]["Total"].loc[scores[0]])
                    y1.append(data[ltr]["df"]["Total"].loc[scores[1]])

                # plot y0, y1
                ax.plot(
                    x_int,
                    y0,
                    color="red",
                    linestyle="-",
                    marker="^",
                    fillstyle="none",
                    label=f"{scores[0].upper()}",
                )
                ax.plot(
                    x_int,
                    y1,
                    color="k",
                    linestyle="-",
                    marker="D",
                    fillstyle="none",
                    label=f"{scores[1].upper()}",
                )

            # plot single score on sub-plot
            if not multiplt:
                filename += f"{score}_"
                _set_ylim(param=param, score=score, ax=ax, debug=debug)

                y = []
                # extract y from different dfs
                for ltr in ltr_sorted:
                    ltr_score = data[ltr]["df"]["Total"].loc[score]
                    y.append(ltr_score)

                ax.plot(
                    x_int,
                    y,
                    color="k",
                    linestyle="-",
                    marker="D",
                    fillstyle="none",
                    label=f"{score.upper()}",
                )

            # customise grid, title, xticks, legend of current ax
            _customise_ax(
                parameter=parameter, score=score, x_ticks=x_ticks, grid=True, ax=ax
            )

            # save figure, if this is the last score
            if idx == len(regular_scores) - 1:
                # add title to figure
                plt.suptitle(
                    footer,
                    horizontalalignment="center",
                    verticalalignment="top",
                    fontdict={
                        "size": 6,
                        "color": "k",
                    },
                    bbox=dict(
                        facecolor="none",
                        edgecolor="grey",
                    ),
                )
                # clear empty subplots
                _clear_empty_axes(subplot_axes=subplot_axes, idx=idx)
                # save & clear figure
                _save_figure(output_dir=output_dir, filename=filename)

    # CATEGORICAL SCORES PLOTTING PIPELINE
    # remark: include thresholds for categorical scores
    if debug:
        print(
            """---\t10) repeat plotting pipeline for categorical
            params/scores/thresh combinations"""
        )

    print(plot_cat_params)
    print(plot_cat_scores)
    print(plot_cat_thresh)
    print(plot_cat_params and plot_cat_scores and plot_cat_thresh)

    if plot_cat_params and plot_cat_scores and plot_cat_thresh:
        print("--- should now create total scores plots for all cat params/scores")
        cat_params = plot_cat_params.split(",")
        """
        categorical parameters:
        # TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,
        # T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,
        # FF_10M_KAL,VMAX_10M6,VMAX_10M1
        """
        cat_scores = plot_cat_scores.split(
            ","
        )  # categorical scores: FBI,MF,POD,FAR,THS,ETS
        cat_threshs = plot_cat_thresh.split(":")  # categorical thresholds:
        # 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20  # noqa: E501
        cat_params_dict = {cat_param: [] for cat_param in cat_params}
        for param, threshs in zip(cat_params, cat_threshs):
            # first append all scores w/o thresholds to parameter
            for score in plot_scores.split(","):
                if "/" in score:
                    cat_params_dict[param].append(score.split("/"))
                else:
                    cat_params_dict[param].append([score])
            # append all scores that have a threshold in their name to current to parameter  # noqa: E501
            thresholds = threshs.split(",")
            for threshold in thresholds:
                for score in cat_scores:
                    if "/" in score:
                        cat_params_dict[param].append(
                            [x + f"({threshold})" for x in score.split("/")]
                        )

                    else:
                        cat_params_dict[param].append([f"{score}({threshold})"])

        if True:
            print("Categorical Parameter Dict: ")
            pprint(cat_params_dict)

    # TODO: implement the total scores pipeline for categorical scores as well

    # ENSEMBLE SCORES PLOTTING PIPELINE
    # remark: include thresholds for categorical scores
    print(
        """---\t11) repeat plotting pipeline for ensemble
        params/scores/thresh combinations"""
    )
    # TODO: implement the total scores pipeline for categorical scores as well

    return
