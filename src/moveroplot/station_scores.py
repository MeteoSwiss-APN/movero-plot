# relevant imports for parsing pipeline
# Standard library
import pprint
import sys
from pathlib import Path

# Third-party
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# relevant imports for plotting pipeline
import matplotlib.pyplot as plt
import numpy as np

# class to add relief to map
# > taken from: https://stackoverflow.com/questions/37423997/cartopy-shaded-relief
from cartopy.io.img_tiles import GoogleTiles

# Local
# local
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import cat_station_score_colortable
from .utils.parse_plot_synop_ch import cat_station_score_range
from .utils.parse_plot_synop_ch import station_score_colortable
from .utils.parse_plot_synop_ch import station_score_range


class ShadedReliefESRI(GoogleTiles):
    # TODO: download image, place in resource directory and link to it
    # shaded relief
    def _image_url(self, tile):
        x, y, z = tile
        url = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}.jpg"
        ).format(z=z, y=y, x=x)
        return url


# enter directory / read station_scores files / call plotting pipeline
def _station_scores_pipeline(
    params_dict,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    season,
    model_version,
    relief,
    debug,
) -> None:
    """Read all ```ATAB``` files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>
        Extract relevant information (parameters/scores) from these files into a dataframe.
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists.


    Args:
        lt_ranges (list): lead time ranges, for which plots should be generated (i.e. 01-06, 07-12,...). part of the file name
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. station_scores)
        file_postfix (str): postfix of files (i.e. '.dat')
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd)
        output_dir (str): output directory (i.e. plots/)
        season (str): season of interest (i.e. 2021s4/)
        model_version (str): model_version of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        relief (bool): passed on to plotting pipeline - add relief to map if True
        debug (bool): print further comments
    """  # noqa: E501
    print("--- initialising station score pipeline")
    for lt_range in lt_ranges:
        for parameter in params_dict:
            # retrieve list of scores, relevant for current parameter
            scores = params_dict[parameter]  # this scores is a list of lists

            # define path to the file of the current parameter (station_score atab file)
            file = f"{file_prefix}{lt_range}_{parameter}{file_postfix}"
            path = Path(f"{input_dir}/{season}/{model_version}/{file}")

            # check if the file exists
            if not path.exists():
                print(
                    f"""WARNING: No data file for parameter {parameter} could be found.
                    {path} does not exist."""
                )
                continue  # no file could be retrieved for the current parameter

            if debug:
                print(f"\nFilepath:\t{path}")

            # extract header
            header = Atab(file=path, sep=" ").header
            relevant_header_information = {
                "Start time": header["Start time"],
                "End time": header[
                    "End time"
                ],  # i.e. ['2021-11-30', '2300', '', '+000'],
                "Missing value code": header["Missing value code"][0],
                "Model name": header["Model name"][0],
                "Model version": header["Model version"][0],
                "Parameter": header["Parameter"][0],
                "Unit": header["Unit"][0],
            }
            # pprint.pprint(relevant_header_information) # dbg

            # TODO: longitude gets parsed ugly --> check separator in atab.py
            # looks like this: ['7.56100', '', '', '', '', '', '', '8.60800',....]
            # should look like this: ['7.56100', '8.60800', ..]
            longitudes = list(filter(None, header["Longitude"]))
            latitudes = list(filter(None, header["Latitude"]))

            # extract dataframe
            df = Atab(file=path, sep=" ").data

            print(path)
            pprint(df)
            """
            # > rename the first column
            # TODO (in ATAB): split the first column based on number of characters and not based
            # on separator. get number of characters from header: Width of text label column: 14

            # alternatively:
            # get column names
            # get first column name
            # remove Score from first column name
            # keep rest and rename first column
            """  # noqa: E501
            df.rename(columns={"ScoreABO": "ABO"}, inplace=True)

            # > add longitude and latitude to df
            df.loc["lon"] = longitudes
            df.loc["lat"] = latitudes

            # > check which relevant scores are available; extract those from df
            all_scores = df.index.tolist()
            available_scores = ["lon", "lat"]  # this list, will be kept
            for score in scores:  # scores = [[score1], [score2],...]
                if score[0] in all_scores:
                    available_scores.append(score[0])
                else:  # warn that a relevant score was not available in dataframe
                    print(
                        f"""WARNING: Score {score[0]}
                        not available for parameter {parameter}."""
                    )

            # reduce dataframe, s.t. only relevant scores + lon/lat are kept
            df = df.loc[available_scores]

            # > remove/replace missing values in dataframe with np.NaN
            df = df.replace(
                float(relevant_header_information["Missing value code"]), np.NaN
            )
            """
            # > if there are rows (= scores), that only contain np.NaN, remove them
            # df = df.dropna(how="all")

            # if debug:
            #     print(f"Generating plot for {parameter} for lt_range: {lt_range}. (File: {file})")
            # for each score in df, create one map
            """  # noqa: E501
            _generate_map_plot(
                data=df,
                lt_range=lt_range,
                variable=parameter,
                file=file,
                file_postfix=file_postfix,
                header_dict=relevant_header_information,
                model_version=model_version,
                output_dir=output_dir,
                relief=relief,
                debug=debug,
            )


# PLOTTING PIPELINE FOR STATION SCORES PLOTS
def _add_features(ax):
    """Add features to map.
    # # point cartopy to the folder containing the shapefiles for the features on the map
    # earth_data_path = Path("src/pytrajplot/resources/")
    # assert (
    #     earth_data_path.exists()
    # ), f"The natural earth data could not be found at {earth_data_path}"
    # # earth_data_path = str(earth_data_path)
    # cartopy.config["pre_existing_data_dir"] = earth_data_path
    # cartopy.config["data_dir"] = earth_data_path

    # add grid & labels to map
    """  # noqa: E501
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        draw_labels=True,
        linewidth=0.5,
        color="k",
        alpha=0.3,
        linestyle="-.",
        rasterized=True,
    )  # define grid line properties
    gl.top_labels = False
    gl.right_labels = False

    ax.add_feature(cfeature.LAND, rasterized=True, color="white")  # color="#FFFAF0"
    ax.add_feature(cfeature.COASTLINE, alpha=0.5, rasterized=True)
    ax.add_feature(cfeature.BORDERS, linestyle="--", alpha=1, rasterized=True)
    ax.add_feature(cfeature.OCEAN, rasterized=True)
    ax.add_feature(cfeature.LAKES, alpha=0.5, rasterized=True)
    ax.add_feature(cfeature.RIVERS, alpha=0.5, rasterized=True)
    ax.add_feature(
        cartopy.feature.NaturalEarthFeature(
            category="physical",
            name="lakes_europe",
            scale="10m",
            rasterized=True,
        ),
        alpha=0.5,
        rasterized=True,
        color="#97b6e1",
    )

    return


def _add_datapoints(data, score, ax, min, max, unit, param, debug=False):
    cat_score = False
    print(f"plotting:\t{param}/{score}")
    # check param, before trying to assign cmap to it

    # i.e. param = TD_2M_KAL
    param = check_params(param, debug)
    # i.e. param = TD_2M*

    print("Station Score Colortable")
    pprint(station_score_colortable)
    print("Note: Index = Scores")

    print("Cat Station Score Colortable")
    pprint(cat_station_score_colortable)

    # RESOLVE CORRECT PARAMETER
    try:  # try to get the cmap from the regular station_score_colortable
        cmap = station_score_colortable[param][score]

    # if a KeyError occurs, the current parameter
    # doesn't match the columns of the station_score_colourtable df AND/OR
    # because the score is not present in the station_score_colourtable df.
    except KeyError:
        if score not in station_score_colortable.index.tolist():
            if score in cat_station_score_colortable[param]["scores"].values:
                cat_score = True
                if debug:
                    print(
                        f"""{score} ∉  station score colortable.
                        {score} ∈  categorical station score colortable."""
                    )
                index = cat_station_score_colortable[
                    cat_station_score_colortable[param]["scores"] == score
                ].index.values[0]
                cmap = cat_station_score_colortable[param]["cmap"].iloc[index]
            else:
                print(f"{score} not known - check again.")
                sys.exit(123)

        elif not cat_score:
            try:
                cmap = station_score_colortable[param][score]
            except KeyError:
                print("Dont know this parameter and score combination.")

    # define limits for colour bar
    if not cat_score:
        lower_bound = station_score_range[param]["min"].loc[score]
        upper_bound = station_score_range[param]["max"].loc[score]
    if cat_score:
        # get the index of the current score
        index = cat_station_score_range[
            cat_station_score_range[param]["scores"] == score
        ].index.values[0]
        lower_bound = cat_station_score_range[param]["min"].iloc[index]
        upper_bound = cat_station_score_range[param]["max"].iloc[index]

    # if both are equal (i.e. 0), take the min/max values as limits
    if lower_bound == upper_bound:
        lower_bound = min
        upper_bound = max

    # print(param, score, lower_bound, upper_bound) # dbg
    tmp = False
    for name, info in data.iteritems():
        lon, lat, value = float(info.lon), float(info.lat), float(info[score])
        # add available datapoints
        if not np.isnan(value):
            tmp = True
            sc = ax.scatter(
                x=lon,
                y=lat,
                marker="o",
                c=value,
                vmin=lower_bound,
                vmax=upper_bound,
                cmap=cmap,
                rasterized=True,
                transform=ccrs.PlateCarree(),
            )

            if False:  # add the short name of the stations as well
                ax.text(
                    x=lon - 0.025,
                    y=lat - 0.007,
                    s=name,
                    color="k",
                    fontsize=3,
                    transform=ccrs.PlateCarree(),
                    rasterized=True,
                )

    if tmp:
        cbar = plt.colorbar(sc, ax=ax)
        cbar.set_label(unit, rotation=270, labelpad=15)
        return

    else:
        return


def _add_text(
    ax,
    variable,
    score,
    header_dict,
    lt_range,
    min_value,
    max_value,
    min_station,
    max_station,
):
    """Add footer and title to plot."""
    footer = f"""Model: {header_dict['Model version']} |
    Period: {header_dict['Start time'][0]} - {header_dict['End time'][0]}
     ({lt_range}) | Min: {min_value} {header_dict['Unit']}
     @ {min_station} | Max: {max_value} {header_dict['Unit']} @ {max_station}
     | © MeteoSwiss"""

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

    title = f"{variable}: {score}"
    ax.set_title(title, fontsize=15, fontweight="bold")

    return ax


def _generate_map_plot(
    data,
    lt_range,
    variable,
    file,
    file_postfix,
    header_dict,
    model_version,
    output_dir,
    relief,
    debug,
):
    """Generate Map Plot."""
    # output_dir = f"{output_dir}/stations_scores"
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # extract scores, which are available in the dataframe (data)
    # for each score, create one map
    scores = data.index.tolist()
    scores.remove("lon")
    scores.remove("lat")

    for score in scores:
        min_value = data.loc[score].min()
        max_value = data.loc[score].max()

        # TODO: get column name from min/max and remove for loop below
        # incomplete_df.T.idxmin()

        # determine the station, where the min/max occurs
        for station, value in data.loc[score].items():
            if value == min_value:
                min_station = station
            if value == max_value:
                max_station = station

        # plotting pipeline
        fig = plt.figure(figsize=(16, 9), dpi=500)
        if relief:
            ax = plt.axes(projection=ShadedReliefESRI().crs)
        else:
            ax = plt.axes(projection=ccrs.PlateCarree())

        # make sure, aspect ratio of map & figure match
        ax.set_aspect("auto")

        # cut map to model_version (taken from pytrajplot)
        if "ch" in model_version:
            ax.set_extent([5.3, 11.2, 45.4, 48.2])
        if "alps" in model_version:
            ax.set_extent([0.7, 16.5, 42.3, 50])

        if relief:
            # add relief
            ax.add_image(ShadedReliefESRI(), 8)

        # add features/datapoints & text
        _add_features(ax=ax)
        _add_datapoints(
            data=data,
            score=score,
            ax=ax,
            min=min_value,
            max=max_value,
            unit=header_dict["Unit"],
            param=header_dict["Parameter"],
        )
        _add_text(
            ax=ax,
            variable=variable,
            score=score,
            header_dict=header_dict,
            lt_range=lt_range,
            min_value=min_value,
            max_value=max_value,
            min_station=min_station,
            max_station=max_station,
        )

        # save and clear figure
        print(f"saving:\t\t{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.savefig(f"{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.close(fig)

    return
