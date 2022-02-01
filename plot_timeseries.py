"""Plot variables of various measurement devices over time."""

# Standard library
import datetime
from datetime import datetime as dt
from pprint import pprint

# Third-party
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.units as munits
import numpy as np
import pandas as pd

converter = mdates.ConciseDateConverter()
munits.registry[np.datetime64] = converter
munits.registry[datetime.date] = converter
munits.registry[datetime.datetime] = converter

# Local
from ..utils.stations import sdf
from ..utils.utils import colour_dict
from ..utils.utils import linestyle_dict
from ..utils.utils import save_fig
from ..utils.variables import vdf


def create_plot(
    multi_axes,
    data,
    var,
    start,
    end,
    datatypes,
    outpath,
    grid,
    devices,
    loc,
    appendix,
    verbose,
):
    # TODO: complete this docstring
    """Create timeseries plot.

    Args:
        multi_axes (bool): plot 2 yaxis if True
        data (dict): dictionary, containing one dataframe for each device
        var (tuple): list of variables (w/ same unit) to be added to plot
        start (datetime obj): start time
        end (datetime obj): end time
        datatypes (tuple): list of output data types
        outpath (str): output folder path
        grid (bool): add grid to plot or not
        devices (list): list of devices
        loc (str): abbreviation of station name (location)
        appendix (bool): add appendix to output name
        verbose (bool): print 'extra' statements during computation

    """
    # general
    fig, left_ax = plt.subplots(1, 1, figsize=(8, 5), constrained_layout=True)
    if multi_axes:
        right_ax = left_ax.twinx()
    if grid:
        # align ticks by implementing ideas from:
        # https://stackoverflow.com/questions/20243683/matplotlib-align-twinx-tick-marks
        left_ax.grid(visible=True)
        right_ax.grid(visible=True)
    left_ax.set_xlim(start, end)
    title = f"Station: {sdf[loc].long_name} | Period: {dt.strftime(start, '%d %b %H:%M')} - {dt.strftime(end, '%d %b %H:%M')}"
    left_ax.set_title(label=title)
    left_unit, right_unit = "", ""

    # plotting
    colour_index = 0
    for i, device in enumerate(devices):
        # 1) retrieve df
        df = data[device]
        # df = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")
        if verbose:
            print(i, device)
            pprint(df)

        # x-axis information: dates/timestamps
        dates = pd.to_datetime(df["timestamp"], format="%Y-%m-%d %H:%M:%S")

        # check if there are more than one variable in this dataframe
        if verbose:
            if len(df.columns) > 2:
                print(
                    f"There are more than one variable ({len(df.columns)}) in the df for: {device}"
                )
            else:
                print(
                    f"There is only one variable ({len(df.columns)}) in the df for: {device}"
                )

        # iterate over the c
        for (variable, columnData) in df.iteritems():
            if variable == "timestamp":
                continue

            # extract current variable
            variable = vdf[variable]
            unit = variable.unit
            var_short = variable.short_name
            y = columnData.values
            label = f"{var_short}: {device}"

            # define unit for the left axes
            if not left_unit:
                left_unit = unit
                left_ax.set_ylabel(f"{left_unit}")

            # define unit for the right axes
            if (not right_unit) and (unit is not left_unit):
                right_unit = unit
                right_ax.set_ylabel(f"{right_unit}")

            # choose correct axes for the current variable and plot data
            if unit == left_unit:
                left_ax.plot(
                    dates,
                    y,
                    color=colour_dict[colour_index],
                    linestyle="-",
                    label=label,
                )
            if unit == right_unit:
                right_ax.plot(
                    dates,
                    y,
                    color=colour_dict[colour_index],
                    linestyle="-",
                    label=label,
                )

            colour_index += 1

    # add legends
    h1, l1 = left_ax.get_legend_handles_labels()
    h2, l2 = right_ax.get_legend_handles_labels()
    left_ax.legend(h1 + h2, l1 + l2)
    filename = f"ts_{start.day}{start.hour}_{end.day}{end.hour}"
    save_fig(filename, datatypes, outpath, fig=fig)
    plt.clf()
    return
