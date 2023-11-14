# pylint: skip-file
# Standard library
from pathlib import Path
from pprint import pprint

# Third-party
import matplotlib.dates as md
import matplotlib.pyplot as plt
import numpy as np

# Local
# import datetime
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import cat_daytime_score_range
from .utils.parse_plot_synop_ch import daytime_score_range


# enter directory / read station_scores files / call plotting pipeline
def _daytime_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    """Read all ```ATAB``` files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>.

        Extract relevant information (parameters/scores)
        from these files into a dataframe.
        Rows --> Scores | Columns --> Stations |
        For each parameter, a separate station_scores File exists.

    Args:
        lt_ranges (list): lead time ranges, for which plots should be generated (i.e. 01-06, 07-12,...). part of the file name
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. time_scores)
        file_postfix (str): postfix of files (i.e. '.dat')
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd)
        output_dir (str): output directory (i.e. plots/)
        model_version (str): model_version of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        debug (bool): print further comments & debug statements

    """  # noqa: E501
    print("\n--- initialising daytime score pipeline")
    if not lt_ranges:
        lt_ranges = "19-24"
    print("KKKK ", plot_setup)
    for model_plots in plot_setup["model_versions"]:
        for parameter, scores in plot_setup["parameter"].items():
            return
    return
    for lt_range in lt_ranges:
        for parameter in plot_setup:
            # retrieve list of scores, relevant for current parameter
            scores = plot_setup[parameter]  # this scores is a list of lists

            # define file path to the current parameter (station_score atab file)
            file = f"{file_prefix}{lt_range}_{parameter}{file_postfix}"
            path = Path(f"{input_dir}/{model_version}/{file}")

            # check if the file exists
            if not path.exists():
                print(
                    f"""WARNING: No data file for parameter {parameter} could be found.
                    {path} does not exist."""
                )
                continue  # for the current parameter no file could be retrieved

            if debug:
                print(f"\nFilepath:\t{path}")

            # extract header & dataframe
            header = Atab(file=path, sep=" ").header
            df = Atab(file=path, sep=" ").data

            # > remove/replace missing values in dataframe with np.NaN
            df = df.replace(float(header["Missing value code"][0]), np.NaN)

            # > if there are columns (= scores), that only contain np.NaN, remove them
            # df = df.dropna(axis=1, how="all")

            # > check which relevant scores are available; extract those from df
            all_scores = df.columns.tolist()
            available_scores = ["hh"]
            multiplot_scores = {}
            for score in scores:
                if len(score) == 1:
                    if score[0] in all_scores:
                        available_scores.append(score[0])
                    else:  # warn that a relevant score was not available in dataframe
                        print(
                            f"""WARNING: Score {score[0]} not
                            available for parameter {parameter}."""
                        )
                if (
                    len(score) > 1
                ):  # # currently only 2-in-1 plots are currently possible
                    multiplot_scores[score[0]] = score[1]
                    for sc in score:
                        if sc in all_scores:
                            available_scores.append(sc)
                        else:
                            print(
                                f"""WARNING: Score {sc} not available
                                for parameter {parameter}."""
                            )

            df = df[available_scores]
            df = df.set_index("hh")

            if debug:
                print("\nFile header:")
                pprint(header)
                print("\nData:")
                pprint(df)
                print(
                    f"""Generating plot for {parameter} for
                    lt_range: {lt_range}. (File: {file})"""
                )

            # for each score in df, create one map
            _generate_daytime_plot(
                data=df,
                multiplots=multiplot_scores,
                lt_range=lt_range,
                variable=parameter,
                file=file,
                file_postfix=file_postfix,
                header_dict=header,
                output_dir=output_dir,
                grid=grid,
                debug=debug,
            )


# PLOTTING PIPELINE FOR DAYTIME SCORES PLOTS
# generator that gives time between start and end times with delta intervals
# inspired by: https://stackoverflow.com/questions/61733727/how-to-set-minutes-time-as-x-axis-of-a-matplotlib-plot-in-python  # noqa: E501
def deltatime(start, end, delta):
    current = start
    while current < end:
        yield current
        current += delta


def get_xaxis():
    # Standard library
    from datetime import datetime
    from datetime import timedelta

    # two random consecutive dates [date1, date2]
    dates = [("01/02/1991", "02/02/1991")]  # , '01/03/1991', '01/04/1991']

    # generate the list for each date between 00:00 on date1 to 00:00 on date2 hourly intervals  # noqa: E501
    datetimes = []
    for start, end in dates:
        startime = datetime.combine(
            datetime.strptime(start, "%d/%m/%Y"),
            datetime.strptime("0:00:00", "%H:%M:%S").time(),
        )
        endtime = datetime.combine(
            datetime.strptime(end, "%d/%m/%Y"),
            datetime.strptime("01:00:00", "%H:%M:%S").time(),
        )
        datetimes.append(
            [j for j in deltatime(startime, endtime, timedelta(minutes=60))]
        )

    # #flatten datetimes list
    datetimes = [datetime for day in datetimes for datetime in day]
    x = datetimes
    return x


def _generate_daytime_plot(
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
    """Generate Daytime Plot."""
    # output_dir = f"{output_dir}/daytime_scores"
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"creating plots for file: {file}")

    # extract scores, which are available in the dataframe (data)
    scores = data.columns.tolist()

    # Standard library
    from datetime import datetime
    from datetime import timedelta

    # two random consecutive dates [date1, date2]
    start_time = datetime.combine(
        datetime.strptime("01/02/1991", "%d/%m/%Y"),
        datetime.strptime("00:00:00", "%H:%M:%S").time(),
    )
    end_time = datetime.combine(
        datetime.strptime("02/02/1991", "%d/%m/%Y"),
        datetime.strptime("00:00:00", "%H:%M:%S").time(),
    )

    # define x-axis only once. list of datetimes from date1 00:00 - date2 00:00
    x = get_xaxis()

    # check, which timestamps are actually necessary
    available_times = data.index.tolist()
    available_x = []
    for available_time in available_times:
        available_x.append(x[available_time])
    first_point = available_x[0]
    last_point = available_x[-1]
    available_x.insert(0, last_point - timedelta(hours=24))
    available_x.append(first_point + timedelta(hours=24))

    unit = header_dict["Unit"][0]

    # define further plot properties
    grid = True

    score_to_skip = None
    for score in scores:
        if score == score_to_skip:
            continue

        param = header_dict["Parameter"][0]
        param = check_params(param=param, verbose=debug)
        print(f"plotting:\t{param}/{score}")

        multiplt = False
        title = f"{variable}: {score}"
        footer = f"""Model: {header_dict['Model version'][0]} |
                    Period: {header_dict['Start time'][0]} -
                    {header_dict['End time'][0]} ({lt_range}) | © MeteoSwiss"""

        # initialise figure/axes instance
        fig, ax = plt.subplots(
            1, 1, figsize=(1660 / 100, 1100 / 100), dpi=150, tight_layout=True
        )

        ax.set_xlim(start_time, end_time)
        ax.set_ylabel(f"{score.upper()} ({unit})")

        # TODO: retrieve ymin/ymax from correct tables in plot_synop
        # and set ax.set_ylim(ymin,ymax)

        if grid:
            ax.grid(which="major", color="#DDDDDD", linewidth=0.8)
            ax.grid(which="minor", color="#EEEEEE", linestyle=":", linewidth=0.5)
            ax.minorticks_on()

        if debug:
            print(f"Extract dataframe for score: {score}")
            pprint(data)

        y = data[score].values.tolist()

        if score in multiplots.keys():
            y2 = data[multiplots[score]].values.tolist()
            multiplt = True
            score_to_skip = multiplots[score]
            title = f"{variable}: {score}/{multiplots[score]}"
            ax.set_ylabel(f"{score.upper()}/{multiplots[score].upper()} ({unit})")

        # plot dashed line @ 0
        ax.plot(x, [0] * len(x), color="grey", linestyle="--")

        # define limits for yaxis if available
        regular_param = (param, "min") in daytime_score_range.columns
        regular_score = score in daytime_score_range.index
        cat_score = not regular_score

        if regular_param and regular_score:
            lower_bound = daytime_score_range[param]["min"].loc[score]
            upper_bound = daytime_score_range[param]["max"].loc[score]
            if debug:
                print(
                    f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
                )
            if lower_bound != upper_bound:
                ax.set_ylim(lower_bound, upper_bound)

        if cat_score:
            # get the index of the current score
            index = cat_daytime_score_range[
                cat_daytime_score_range[param]["scores"] == score
            ].index.values[0]
            # get min/max value
            lower_bound = cat_daytime_score_range[param]["min"].iloc[index]
            upper_bound = cat_daytime_score_range[param]["max"].iloc[index]
            if debug:
                print(
                    f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}"
                )
            if lower_bound != upper_bound:
                ax.set_ylim(lower_bound, upper_bound)

        label = f"{score.upper()}"
        if not multiplt:
            # pre-/append first and last values to the scores lists
            first_y, last_y = y[0], y[-1]
            y.insert(0, last_y)
            y.append(first_y)

            ax.plot(
                available_x,
                y,
                color="k",
                marker="o",
                linestyle="-",
                label=label,
            )
        if multiplt:
            # pre-/append first and last values to the scores lists
            first_y, last_y = y[0], y[-1]
            y.insert(0, last_y)
            y.append(first_y)
            first_y2, last_y2 = y2[0], y2[-1]
            y2.insert(0, last_y2)
            y2.append(first_y2)

            # change title, y-axis label, filename here, for the multiplot case
            ax.plot(
                available_x,
                y,
                color="red",
                linestyle="-",
                marker="o",
                label=label,
            )
            label = f"{multiplots[score].upper()}"
            ax.plot(
                available_x,
                y2,
                color="k",
                linestyle="-",
                marker="o",
                label=label,
            )

        # From the SO:https://stackoverflow.com/questions/42398264/matplotlib-xticks-every-15-minutes-starting-on-the-hour  # noqa: E501
        # Set time format and the interval of ticks (every n minutes)
        xformatter = md.DateFormatter("%H:%M")
        xlocator = md.MinuteLocator(interval=360)
        # Set xtick labels to appear every n minutes
        ax.xaxis.set_major_locator(xlocator)
        # Format xtick labels as HH:MM
        plt.gcf().axes[0].xaxis.set_major_formatter(xformatter)

        plt.legend()

        plt.suptitle(
            footer,
            x=0.03,
            y=0.957,
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
