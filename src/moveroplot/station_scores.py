# pylint: skip-file
# relevant imports for parsing pipeline
# Standard library
from datetime import datetime
from pathlib import Path

# Third-party
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors

# relevant imports for plotting pipeline
import matplotlib.pyplot as plt
import numpy as np

# class to add relief to map
# > taken from: https://stackoverflow.com/questions/37423997/cartopy-shaded-relief
from cartopy.io.img_tiles import GoogleTiles
from cartopy.mpl.gridliner import LATITUDE_FORMATTER
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER
from netCDF4 import Dataset

# First-party
from moveroplot.load_files import load_relevant_files

# Local
# local
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import cat_station_score_range
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


def _calculate_figsize(num_rows, num_cols, single_plot_size=(8, 6), padding=(2, 2)):
    """Calculate the figure size given the number of rows and columns of subplots.

    Args:
    - num_rows: Number of rows of subplots.
    - num_cols: Number of columns of subplots.
    - single_plot_size: A tuple (width, height) of the size of a single subplot.
    - padding: A tuple (horizontal_padding, vertical_padding) between plots.

    Returns:
    - tuple representing the figure size.

    """
    total_width = num_cols * single_plot_size[0] + (num_cols - 1) * padding[0]
    total_height = num_rows * single_plot_size[1] + (num_rows - 1) * padding[1]
    return (total_width, total_height)


def _initialize_plots(labels: list, scores: list, plot_setup: dict):
    num_cols = len(labels)
    num_rows = len(scores)
    figsize = _calculate_figsize(num_rows, num_cols, (7.3, 5), (0, 2))
    fig, axes = plt.subplots(
        subplot_kw=dict(
            projection=ccrs.RotatedPole(pole_longitude=-170, pole_latitude=43)
        ),
        nrows=num_rows,
        ncols=num_cols,
        tight_layout=True,
        figsize=figsize,
        dpi=100,
        squeeze=False,
    )
    for ax in axes.ravel():        
        if "ch" in plot_setup["model_versions"][0][0]:
            ax.set_extent([5.3, 11.2, 45.4, 48.2], crs=ccrs.PlateCarree())
        if "alps" in plot_setup["model_versions"][0][0]:
            ax.set_extent([0.7, 16.5, 42.3, 50], crs=ccrs.PlateCarree())
        _add_features(ax)
    fig.tight_layout(w_pad=8, h_pad=2, rect=(0.05, 0.05, 0.90, 0.90))
    plt.subplots_adjust(bottom=0.15)
    return fig, axes


def _add_plot_text(ax, data, score, ltr):
    [subplot_title] = data["header"]["Model version"]
    ax.set_title(f"{subplot_title}: {score}, LT: {ltr}")
    if score not in data["df"].index:
        return
    min_value = data["df"].loc[score].min()
    min_station = data["df"].loc[score].idxmin()
    max_value = data["df"].loc[score].max()
    max_station = data["df"].loc[score].idxmax()
    try:
        start_date = datetime.strptime(
            " ".join(data["header"]["Start time"][0:2]), "%Y-%m-%d %H:%M"
        )
        end_date = datetime.strptime(
            " ".join(data["header"]["End time"][0:2]), "%Y-%m-%d %H:%M"
        )
    except ValueError:
        start_date = datetime(9999, 1, 1, hour=0, minute=0)
        end_date = datetime(9999, 1, 1, hour=0, minute=0)
        print("Found invalid date format.")

    # pylint: disable=line-too-long
    plt.text(
        0.5,
        -0.03,
        f"""{start_date.strftime("%Y-%m-%d %H:%M")} to {end_date.strftime("%Y-%m-%d %H:%M")} -Min: {min_value} mm at station {min_station} +Max: {max_value} mm at station {max_station}""",  # noqa: E501
        horizontalalignment="center",
        verticalalignment="center",
        transform=ax.transAxes,
        fontsize=8,
    )
    # pylint: enable=line-too-long


def _plot_and_save_scores(
    output_dir,
    base_filename,
    parameter,
    plot_scores_setup,
    sup_title,
    ltr_models_data,
    plot_setup,
    debug=False,
):
    for ltr, models_data in ltr_models_data.items():
        ltr_info = f"_{ltr}"
        model_info = (
            "" if len(models_data.keys()) > 1 else f"_{next(iter(models_data.keys()))}"
        )
        for scores in plot_scores_setup:
            filename = base_filename + ltr_info + model_info
            fig, subplot_axes = _initialize_plots(models_data.keys(), scores, plot_setup=plot_setup)
            for idx, score in enumerate(scores):
                filename += f"_{score}"
                for model_idx, data in enumerate(models_data.values()):
                    ax = subplot_axes[idx][model_idx]
                    _add_datapoints2(
                        fig=fig,
                        data=data["df"],
                        score=score,
                        ax=ax,
                        min=-10,
                        max=10,
                        unit=data["header"]["Unit"][0],
                        param=data["header"]["Parameter"],
                    )

                    _add_plot_text(ax, data, score, ltr)

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
            plt.close()


def _generate_station_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    plot_setup,
    debug,
):
    # initialise filename
    base_filename = f"station_scores_{parameter}"
    sup_title = f"PARAMETER: {parameter}"

    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["regular_scores"],
        sup_title,
        models_data,
        plot_setup,
        debug=False,
    )
    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["cat_scores"],
        sup_title,
        models_data,
        plot_setup,
        debug=False,
    )


# enter directory / read station_scores files / call plotting pipeline
# type: ignore
def _station_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    """Read all ```ATAB``` files that are present in: data_dir/season/model_version/<file_prefix><...><file_postfix>.

        Extract relevant information (parameters/scores) from these files into a dataframe.
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists.


    Args:
        lt_ranges (list): lead time ranges, for which plots should be generated (i.e. 01-06, 07-12,...). part of the file name
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. station_scores)
        file_postfix (str): postfix of files (i.e. ".dat")
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd)
        output_dir (str): output directory (i.e. plots/)
        model_version (str): model_version of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        relief (bool): passed on to plotting pipeline - add relief to map if True
        debug (bool): print further comments

    """  # noqa: E501
    print("--- initialising station score pipeline")

    if not lt_ranges:
        lt_ranges = "19-24"
    for model_plots in plot_setup["model_versions"]:
        for parameter, scores in plot_setup["parameter"].items():
            model_data = load_relevant_files(
                input_dir,
                file_prefix,
                file_postfix,
                debug,
                model_plots,
                parameter,
                lt_ranges,
                ltr_first=True,
                transform_func=_station_score_transformation,
            )
            if not model_data:
                print(f"No matching files found with given ltr {lt_ranges}")
                return
            _generate_station_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                plot_setup=plot_setup,
                debug=debug,
            )


def _station_score_transformation(df, header):
    df = df.replace(float(header["Missing value code"][0]), np.NaN)
    df.rename(columns={"ScoreABO": "ABO"}, inplace=True)
    df.loc["lon"] = list(filter(None, header["Longitude"]))
    df.loc["lat"] = list(filter(None, header["Latitude"]))
    return df


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
    gl = ax.gridlines(draw_labels=True, ls="--", lw=0.5, x_inline=False, y_inline=False, zorder=11)
    gl.top_labels = True
    gl.left_labels = True
    gl.bottom_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {"rotation": 0}
    gl.ylabel_style = {"rotation": 0}

    ax.add_feature(cfeature.COASTLINE, alpha=0.5, rasterized=True, zorder=10)
    ax.add_feature(
        cfeature.BORDERS, linestyle="--", alpha=1, rasterized=True, zorder=10
    )
    ax.add_feature(cfeature.OCEAN, rasterized=True, zorder=10)
    ax.add_feature(cfeature.LAKES, alpha=0.5, rasterized=True, zorder=10)
    ax.add_feature(cfeature.RIVERS, alpha=0.5, rasterized=True, zorder=10)
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
        zorder=10,
    )
    # ax.add_image(ShadedReliefESRI(), 8)

    # add ICON-CH1-EPS topography on COSMO-1E grid
    icon_ch1_eps_topo = Dataset("/users/oprusers/osm/opr/data/topo_i1e_on_c1e_grid.nc")
    ax.contourf(
        icon_ch1_eps_topo["x_1"][:].data,
        icon_ch1_eps_topo["y_1"][:].data,
        icon_ch1_eps_topo["HSURF"][0, ...].data,
        cmap="gray_r",
        levels=np.arange(0, 8400, 400),
        extend="both",
        alpha=0.4,
    )


def _add_datapoints2(fig, data, score, ax, min, max, unit, param, debug=False):
    # dataframes have two different structures

    # Workaround since check_params does not work for ATHD_S
    param = "ATHD_S" if param[0] == "ATHD_S" else check_params(param[0])

    if param in station_score_range.columns and score in station_score_range.index:
        param_score_range = station_score_range[param].loc[score]
    elif (
        param in cat_station_score_range.columns
        and score in cat_station_score_range[param].set_index("scores").index
    ):
        param_score_range = (
            cat_station_score_range[param].set_index("scores").loc[score]
        )
    else:
        # Set default range for the FBI score that is not defined in the lookup table
        if score.startswith("FBI"):
            param_score_range = (
                {"min": 0.3, "max": 3}
                if param.startswith("CLCT")
                else {"min": 0.1, "max": 10}
            )

        # Set default range for all other scores that are not defined in the lookup table
        else:
            param_score_range = {"min": None, "max": None}

    if score not in data.index:
        return

    plot_data = data.loc[["lon", "lat", score]].astype(float)
    nan_data = plot_data.loc[:, plot_data.isna().any()]
    plot_data = plot_data.dropna(axis="columns")

    cmap, param_score_range = _determine_cmap_and_bounds(
        param, score, plot_data.loc[score], param_score_range
    )

    if score.startswith("FBI"):
        norm = mcolors.TwoSlopeNorm(
            vmin=param_score_range["min"], vmax=param_score_range["max"], vcenter=1
        )

    sc = ax.scatter(
        x=list(plot_data.loc["lon"]),
        y=list(plot_data.loc["lat"]),
        marker="o",
        c=list(plot_data.loc[score]),
        vmin=param_score_range["min"] if not score.startswith("FBI") else None,
        vmax=param_score_range["max"] if not score.startswith("FBI") else None,
        cmap=cmap,
        norm=norm if score.startswith("FBI") else None,
        edgecolors="black",
        linewidth=0.4,
        rasterized=True,
        zorder=80,
        transform=ccrs.PlateCarree(),
    )
    if len(plot_data.loc[score]) != 0:
        max_idx = plot_data.loc[score].idxmax()
        min_idx = plot_data.loc[score].idxmin()
        ax.scatter(
            x=[plot_data[max_idx].loc["lon"]],
            y=[plot_data[max_idx].loc["lat"]],
            marker="+",
            color="black",
            s=80,
            zorder=100,
            transform=ccrs.PlateCarree(),
        )
        ax.scatter(
            x=[plot_data[min_idx].loc["lon"]],
            y=[plot_data[min_idx].loc["lat"]],
            marker="_",
            color="black",
            s=80,
            zorder=100,
            transform=ccrs.PlateCarree(),
        )
    cax = fig.add_axes(
        [
            ax.get_position().x1 + 0.005,
            ax.get_position().y0,
            0.008,
            ax.get_position().height,
        ]
    )
    cbar = plt.colorbar(sc, cax=cax)

    # Only modify ticks for the FBI case
    if score.startswith("FBI"):
        custom_ticks = (
            [0.3, 0.5, 0.7, 0.9, 1, 2, 3]
            if param.startswith("CLCT")
            else [0.1, 0.3, 0.5, 0.7, 0.9, 1, 2, 4, 6, 8, 10]
        )
        cbar.set_ticks(custom_ticks)
        cbar.ax.set_yticklabels([str(tick) for tick in custom_ticks])

    cbar.set_label(unit, rotation=270, labelpad=10)
    ax.scatter(
        x=list(nan_data.loc["lon"]),
        y=list(nan_data.loc["lat"]),
        rasterized=True,
        transform=ccrs.PlateCarree(),
        facecolors="none",
        edgecolors="black",
        linewidth=0.5,
    )


def _add_datapoints(data, score, ax, min, max, unit, param, debug=False):
    print(f"plotting:\t{param}/{score}")
    # check param, before trying to assign cmap to it

    print("Station Score Colortable")
    # pprint(station_score_colortable)
    print("Note: Index = Scores")

    # print("Cat Station Score Colortable")
    # print(data.loc[["lon", "lat", score]])
    lower_bound = station_score_range[param[0], "min"][score]
    upper_bound = station_score_range[param[0], "max"][score]

    sc = ax.scatter(
        x=list(data.loc["lon"].astype(float)),
        y=list(data.loc["lat"].astype(float)),
        marker="o",
        c=list(data.loc[score].astype(float)),
        vmin=lower_bound,
        vmax=upper_bound,
        rasterized=True,
        transform=ccrs.PlateCarree(),
    )

    cbar = plt.colorbar(sc, ax=ax, orientation="vertical", fraction=0.046, pad=0.04)
    cbar.set_label(unit, rotation=270, labelpad=15)


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
    footer = f"""Model: {header_dict["Model version"]} |
    Period: {header_dict["Start time"][0]} - {header_dict["End time"][0]} | Min: {min_value} {header_dict["Unit"]}
     @ {min_station} | Max: {max_value} {header_dict["Unit"]} @ {max_station}
     | © MeteoSwiss"""  # noqa: E501

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

    title = f"{variable}: {score}, LT: {lt_range}"
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
        fig = plt.figure(figsize=(14.7, 10), dpi=100)
        if relief:
            ax = plt.axes(projection=ShadedReliefESRI().crs)
        else:
            ax = plt.axes(
                projection=ccrs.RotatedPole(pole_longitude=-170, pole_latitude=43)
            )

        # make sure, aspect ratio of map & figure match
        ax.set_aspect("auto")

        # cut map to model_version (taken from pytrajplot)
        if "ch" in model_version:
            ax.set_extent([5.3, 11.2, 45.4, 48.2], crs=ccrs.PlateCarree())
        if "alps" in model_version:
            ax.set_extent([0.7, 16.5, 42.3, 50], crs=ccrs.PlateCarree())

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


def _determine_cmap_and_bounds(
    param,
    score,
    plot_data,
    param_score_range,
):
    """Set cmap depending on param and score and and plotting bounds for some variables."""
        
    # Colormaps that depend on parameter and score
    if param.startswith(("T_2M", "FF", "VMAX", "DD", "PS", "PMSL")) and score.startswith(("ME", "FBI")):
        cmap = "RdBu_r"

    elif param.startswith(("CLCT", "GLOB", "ATHD_S")) and score.startswith(("ME", "FBI")):
        cmap = "PuOr"
        
    elif param.startswith(("DURSUN")) and score.startswith(("ME", "FBI")):
        cmap = "PuOr_r"

    elif param.startswith(("TOT_PREC", "RELHUM", "TD")) and score.startswith(("ME", "FBI")):
        cmap = "BrBG"
        
    elif param.startswith(("TOT_PREC")) and score.startswith(("MMOD", "MOBS")):
        cmap = "YlGnBu"
        param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("CLCT", "ATHD_S")) and score.startswith(("MMOD", "MOBS")):
        cmap = "cividis_r"
        # Workaround as ATHD_S is not in utils/plot_synop_ch
        if param != "ATHD_S":
            param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("GLOB", "DURSUN")) and score.startswith(("MMOD", "MOBS")):
        cmap = "cividis"
        param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("T_2M")) and score.startswith(("MMOD", "MOBS")):
        cmap = "coolwarm"
        param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("TD_2M", "RELHUM_2M")) and score.startswith(("MMOD", "MOBS")):
        cmap = "coolwarm_r"
        param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("FF", "VMAX", "PS", "PMSL")) and score.startswith(("MMOD", "MOBS")):
        cmap = "cool"
        param_score_range = station_score_range[param].loc["MMOD"]
        
    elif param.startswith(("DD")) and score.startswith(("MMOD", "MOBS")):
        cmap = "hsv"
        param_score_range = station_score_range[param].loc["MMOD"]     

    elif score in ["MAE", "STDE", "RMSE"]:
        cmap = "Spectral_r"

    elif score in ["COR"]:
        cmap = "Spectral"

    elif score in ["NOBS"]:
        cmap = "Spectral"
        param_score_range["min"] = 0
        param_score_range["max"] = np.ceil(plot_data.max())

    elif score.startswith(("MF", "POD", "FAR", "THS", "ETS")):
        cmap = "Spectral"

    elif score.startswith("OF"):
        cmap = "Spectral"

        # Only set range of OF to range of MF if it is defined in lookup table
        if (
            score.replace("OF", "MF")
            in cat_station_score_range[param].set_index("scores").index
        ):
            param_score_range = (
                cat_station_score_range[param]
                .set_index("scores")
                .loc[score.replace("OF", "MF")]
            )
        else:
            param_score_range = {"min": None, "max": None}
            
    # Go to default if param is None or no option specified here
    else:
        cmap = "viridis"

    return cmap, param_score_range
