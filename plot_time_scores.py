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

from config.parse_plot_synop_ch import time_score_range



def generate_timeseries_plot(
    data,
    lt_range,
    variable,
    file,
    file_postfix,
    header_dict,
    domain,
    output_dir,
    verbose,
): 
    print(f"creating plots for file: {file}")
    pprint(data)
    # extract scores, which are available in the dataframe (data)
    # for each score
    scores = data.columns.tolist()
    scores.remove("datetime")
    scores.remove("lt_hh")
    scores.remove("lt_mm")
    
    # create lead_time_hours list, i.e. for lt_range 01-06, lt_hours = [1, 2, 3, 4, 5, 6]
    lt_hours = range(int(lt_range[:2]), int(lt_range[-2:])+1)

    # define limits for plot (start, end time specified in header)
    start = datetime.datetime.strptime(header_dict['Start time'][0] + ' ' + header_dict['Start time'][2], '%Y-%m-%d %H:%M')
    end = datetime.datetime.strptime(header_dict['End time'][0] + ' ' + header_dict['End time'][1], '%Y-%m-%d %H:%M') 
    unit = header_dict['Unit'][0]

    # define further plot properties
    grid = True

    # TODO: implement correct limits here!
    
    for score in scores:
        title = f"{variable}: {score}"    
        footer = f"Model: {header_dict['Model version'][0]} | Period: {header_dict['Start time'][0]} - {header_dict['End time'][0]} ({lt_range}) | © MeteoSwiss"
        # intialise figure/axes instance
        fig, ax = plt.subplots(1, 1, figsize=(245/10, 51/10), dpi=150, constrained_layout=False)
        
        ax.set_title(label=title)
        ax.set_xlim(start, end)
        ax.set_ylabel(f"{unit}")
        if grid:
            ax.grid(visible=True)

        if verbose:
            print(f"Extract dataframe for score: {score}")
            pprint(data)

        
        # x = pd.to_datetime(df_tmp["datetime"], format="%d.%m.%Y %H:%M")
        x = data['datetime'].values
        y = data[score].values
        ax.plot(x, [0]*len(x), color='grey', linestyle='--')

        # define limits for yaxis if available
        param = header_dict["Parameter"][0]
        
        if (param+"_min") in time_score_range.columns:
            lower_bound = time_score_range[param]["min"].loc[score]
            upper_bound = time_score_range[param]["max"].loc[score]
            print(f"found limits for {param}/{score} --> {lower_bound}/{upper_bound}")
            if lower_bound != upper_bound:
                ax.set_ylim(lower_bound, upper_bound)
            
        # label = f"{header_dict['Description'][0]} {header_dict['Description'][1]} {header_dict['Description'][2]}
        label = " ".join(header_dict['Description'])
        ax.plot(
                x,
                y,
                color='k',
                linestyle="-",
                label=label,
                )

        plt.suptitle(
            footer,
            x=0.125,
            y=0.06,
            horizontalalignment="left",
            verticalalignment="top",
            fontdict={
                "size": 6,
                "color": "k",
            },
        )
        # print(f"should save: ", f"{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.savefig(f"{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.close(fig)




    return