# IMPORTS
from pathlib import Path
import matplotlib.pyplot as plt

# import datetime
from .utils.atab import Atab
import numpy as np
from pprint import pprint
import pandas as pd
import datetime as dt
from ipdb import set_trace as dbg


from .utils.parse_plot_synop_ch import time_score_range, cat_time_score_range
from .utils.check_params import check_params


# enter directory / read station_scores files / call plotting pipeline
def _time_scores_pipeline(
    params_dict,
    lt_ranges,
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
    """
    print(f"\n--- initialising time score pipeline")
    for lt_range in lt_ranges:
        for parameter in params_dict:
            # retrieve list of scores, relevant for current parameter
            scores = params_dict[parameter]  # this scores is a list of lists

            # define file path to the file correpsonding to the current parameter (station_score atab file)
            file = f"{file_prefix}{lt_range}_{parameter}{file_postfix}"
            path = Path(f"{input_dir}/{season}/{model_version}/{file}")

            # check if the file exists
            if not path.exists():
                print(
                    f"--- WARNING: No data file for parameter {parameter} could be found. {path} does not exist."
                )
                continue  # go the the next parameter, since for the current parameter no file could be retrieved

            if debug:
                print(f"\nFilepath:\t{path}")

            # extract header & dataframe
            header = Atab(file=path, sep=" ").header
            df = Atab(file=path, sep=" ").data

            # change type of time columns to str, s.t. they can be combined to one datetime column afterwards
            data_types_dict = {"YYYY": str, "MM": str, "DD": str, "hh": str, "mm": str}
            df = df.astype(data_types_dict)

            # TODO: optimise this - it is inefficient and ugly.
            # create datetime column (just called time) & drop unnecessary columns
            df["timestamp"] = pd.to_datetime(
                df["YYYY"]
                + "-"
                + df["MM"]
                + "-"
                + df["DD"]
                + " "
                + df["hh"]
                + ":"
                + df["mm"]
            )

            # dbg()
            # df['timestamp_new'] = [' '.join([x + '-' + y + '-' + z + ' ' + q + ':' + r]) for x, y, z, q, r in zip(df['YYYY'], df['MM'], df['DD'], df['hh'], df['mm'])]
            # df['timestamp_new'] = pd.to_datetime(df['timestamp_new'])
            # df['timestamp_new_2'] = pd.to_datetime([' '.join([x + '-' + y + '-' + z + ' ' + q + ':' + r]) for x, y, z, q, r in zip(df['YYYY'], df['MM'], df['DD'], df['hh'], df['mm'])])
            # df['timestamp'] = pd.to_datetime([' '.join([x + '-' + y + '-' + z + ' ' + q + ':' + r]) for x, y, z, q, r in zip(df['YYYY'], df['MM'], df['DD'], df['hh'], df['mm'])])
            # dbg()

            df.drop(
                ["YYYY", "MM", "DD", "hh", "mm", "lt_hh", "lt_mm"], axis=1, inplace=True
            )

            # > remove/replace missing values in dataframe with np.NaN
            df = df.replace(float(header["Missing value code"][0]), np.NaN)

            # > if there are columns (= scores), that only conaint np.NaN, remove them
            # df = df.dropna(axis=1, how="all")

            # > check which relevant scores are available; extract those from df
            all_scores = df.columns.tolist()
            available_scores = [
                "timestamp"
            ]  # this list is the columns, that should be kept
            multiplot_scores = {}
            for score in scores:  # scores = [[score1], [score2/score3], [score4],...]
                if len(score) == 1:
                    if score[0] in all_scores:
                        available_scores.append(score[0])
                    else:  # warn that a relevant score was not available in dataframe
                        print(
                            f"--- WARNING: Score {score[0]} not available for parameter {parameter}."
                        )
                if (
                    len(score) > 1
                ):  # if TWO scores are plotted on one plot# currently only 2-in-1 plots are possible
                    # MMOD/MOBS --> MMOD:MOBS
                    multiplot_scores[score[0]] = score[1]
                    for sc in score:
                        if sc in all_scores:
                            available_scores.append(sc)
                        else:
                            print(
                                f"--- WARNING: Score {sc} not available for parameter {parameter}."
                            )

            df = df[available_scores]

            if False:
                print("\nFile header:")
                pprint(header)
                print("\nData:")
                pprint(df)

            if debug:
                print(
                    f"Generating plot for {parameter} for lt_range: {lt_range}. (File: {file})"
                )
            # for each score in df, create one map
            _generate_timeseries_plot(
                data=df,
                multiplots=multiplot_scores,  # { MMOD : MOBS }
                lt_range=lt_range,
                variable=parameter,
                file=file,
                file_postfix=file_postfix,
                header_dict=header,
                output_dir=output_dir,
                grid=grid,
                debug=debug,
            )


############################################################################################################################
######################################### PLOTTING PIPELINE FOR TIME SCORES PLOTS ##########################################
############################################################################################################################


def _generate_timeseries_plot(
    data,
    multiplots,
    lt_range,
    variable,
    file,
    file_postfix,
    header_dict,
    output_dir,
    grid,
    debug,
):
    """Generate Timeseries Plot."""
    # output_dir = f"{output_dir}/time_scores"
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    # print(f"creating plots for file: {file}")
    # extract scores, which are available in the dataframe (data)
    # for each score
    scores = data.columns.tolist()
    scores.remove("timestamp")

    # define limits for plot (start, end time specified in header)
    start = dt.datetime.strptime(
        header_dict["Start time"][0] + " " + header_dict["Start time"][2],
        "%Y-%m-%d %H:%M",
    )
    end = dt.datetime.strptime(
        header_dict["End time"][0] + " " + header_dict["End time"][1], "%Y-%m-%d %H:%M"
    )
    unit = header_dict["Unit"][0]

    # this variable, remembers if a score has been added to another plot.
    # for example in the multiplots dict, when plotting MMOD, MOBS will also be added to the plot
    # and does not need to be plotted again.
    score_to_skip = None
    for score in scores:
        if score == score_to_skip:
            continue

        param = header_dict["Parameter"][0]
        # param = TD_2M_KAL
        param = check_params(
            param=param, verbose=debug
        )  # TODO: replace param w/ variable
        # param = TD_2M*
        print(f"plotting:\t{param}/{score}")

        multiplt = False
        title = f"{variable}: {score}"  # the variable 'variable' is the full parameter name.
        footer = f"Model: {header_dict['Model version'][0]} | Period: {header_dict['Start time'][0]} - {header_dict['End time'][0]} ({lt_range}) | © MeteoSwiss"
        # intialise figure/axes instance
        fig, ax = plt.subplots(
            1, 1, figsize=(245 / 10, 51 / 10), dpi=150, tight_layout=True
        )

        ax.set_xlim(start, end)
        ax.set_ylabel(f"{score.upper()} ({unit})")

        if grid:
            ax.grid(visible=True)

        if debug:
            print(f"Extract dataframe for score: {score}")
            pprint(data)

        x = data["timestamp"].values
        y = data[score].values

        if score in multiplots.keys():
            y2 = data[multiplots[score]].values
            multiplt = True
            score_to_skip = multiplots[score]
            title = f"{variable}: {score}/{multiplots[score]}"
            ax.set_ylabel(f"{score.upper()}/{multiplots[score].upper()} ({unit})")

        # plot dashed line @ 0
        ax.plot(x, [0] * len(x), color="grey", linestyle="--")

        # define limits for yaxis if available
        regular_param = (param, "min") in time_score_range.columns
        regular_score = score in time_score_range.index
        cat_score = not regular_score

        if regular_param and regular_score:
            lower_bound = time_score_range[param]["min"].loc[score]
            upper_bound = time_score_range[param]["max"].loc[score]
            if debug:
                print(
                    f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
                )
            if lower_bound != upper_bound:
                ax.set_ylim(lower_bound, upper_bound)

        if cat_score:
            # get the index of the current score
            index = cat_time_score_range[
                cat_time_score_range[param]["scores"] == score
            ].index.values[0]
            # get min/max value
            lower_bound = cat_time_score_range[param]["min"].iloc[index]
            upper_bound = cat_time_score_range[param]["max"].iloc[index]
            if debug:
                print(
                    f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
                )
            if lower_bound != upper_bound:
                ax.set_ylim(lower_bound, upper_bound)

        label = f"{score.upper()}"
        if not multiplt:
            ax.plot(
                x,
                y,
                color="k",
                linestyle="-",
                label=label,
            )
        if multiplt:
            ax.plot(
                x,
                y,
                color="red",
                linestyle="-",
                label=label,
            )
            label = f"{multiplots[score].upper()}"
            ax.plot(
                x,
                y2,
                color="k",
                linestyle="-",
                label=label,
            )
            # change title, y-axis label, filename here, for the multiplot case

        plt.legend()

        plt.suptitle(
            footer,
            x=0.0215,
            y=0.908,
            horizontalalignment="left",
            verticalalignment="top",
            fontdict={
                "size": 6,
                "color": "k",
            },
        )
        ax.set_title(label=title)

        print(f"saving:\t\t{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.savefig(f"{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.close(fig)

    return
