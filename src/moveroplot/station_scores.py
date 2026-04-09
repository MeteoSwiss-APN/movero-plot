# pylint: skip-file
# relevant imports for parsing pipeline
# Standard library
from datetime import datetime
from pathlib import Path

# Third-party
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.colors as mcolors

# relevant imports for plotting pipeline
import matplotlib.pyplot as plt
import numpy as np

from cartopy.mpl.gridliner import LATITUDE_FORMATTER
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER
from netCDF4 import Dataset

# First-party
from moveroplot.load_files import load_relevant_files
from moveroplot.plotting import get_total_dates_from_headers

# Local
# local
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import cat_station_score_range
from .utils.parse_plot_synop_ch import station_score_range
from .utils.scores_lists_settings import unit_number_scores, unitless_scores, _determine_cmap_and_bounds
from .utils.FBI_scores_settings import param_score_range_fbi, _forward, _inverse, _forward_spec,     _inverse_spec, fbi_custom_ticks

# Module-level cache for pre-rendered map background images.
# Key: (extent_tuple, topography_path_or_None), Value: (rgba_array, xlim, ylim)
_background_cache = {}


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


def _initialize_plots(labels: list, scores: list, plot_setup: dict, topography=None):
    num_cols = len(labels)
    num_rows = len(scores)
    figsize = _calculate_figsize(num_rows, num_cols, (7.3, 5), (0, 2))

    projection = ccrs.RotatedPole(pole_longitude=-170, pole_latitude=43)

    # Determine map extent from model version (same logic as before; last match wins)
    extent = None
    if "ch" in plot_setup["model_versions"][0][0]:
        extent = [5.8, 10.6, 45.75, 47.8]
    if "alps" in plot_setup["model_versions"][0][0]:
        extent = [0.7, 16.5, 42.3, 50]

    # Pre-render (or retrieve from cache) the map background image
    bg_rgba = bg_xlim = bg_ylim = None
    if extent is not None:
        bg_rgba, bg_xlim, bg_ylim = _get_cached_background(
            extent, topography, projection
        )

    fig, axes = plt.subplots(
        subplot_kw=dict(projection=projection),
        nrows=num_rows,
        ncols=num_cols,
        tight_layout=True,
        figsize=figsize,
        dpi=100,
        squeeze=False,
    )
    for ax in axes.ravel():
        if extent is not None:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
            # Stamp the cached background image onto every subplot
            assert bg_rgba is not None and bg_xlim is not None and bg_ylim is not None
            ax.imshow(
                bg_rgba,
                extent=[bg_xlim[0], bg_xlim[1], bg_ylim[0], bg_ylim[1]],
                origin='upper',
                interpolation='bilinear',
                zorder=9,
                transform=projection,
            )
        _add_gridlines(ax)
    fig.tight_layout(w_pad=8, h_pad=2, rect=(0.05, 0.05, 0.90, 0.90))
    plt.subplots_adjust(bottom=0.15)
    return fig, axes


def _add_plot_text(ax, data, score, ltr):
    unit=data["header"]["Unit"][0]
    [subplot_title] = data["header"]["Model version"]
    ax.set_title(f"{subplot_title}: {score}, LT: {ltr}")

    if score not in data["df"].index:
        return
    
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
    start_str = start_date.strftime("%Y-%m-%d %H:%M")
    end_str = end_date.strftime("%Y-%m-%d %H:%M")
    
    row = data["df"].loc[score]
    valid = row.dropna()
    # If all values are NaN, write custom text
    if valid.empty:
        plt.text(
            0.5,
            -0.03,
            f"""{start_str} to {end_str} -No valid data""",  # noqa: E501
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax.transAxes,
            fontsize=8,
        )
        return
    
    min_value = valid.min()
    min_station = valid.idxmin()
    max_value = valid.max()
    max_station = valid.idxmax()

    # Determine the unit suffix for the footer text
    if any(score.startswith(p) for p in unitless_scores):
        unit_suffix = ""
    elif any(score.startswith(p) for p in unit_number_scores):
        unit_suffix = " (Number)"
    else:
        unit_suffix = f" {unit}"

    plt.text(
        0.5,
        -0.03,
        f"{start_str} to {end_str} "
        f"-Min: {min_value}{unit_suffix} at station {min_station} "
        f"+Max: {max_value}{unit_suffix} at station  {max_station}",
        horizontalalignment="center",
        verticalalignment="center",
        transform=ax.transAxes,
        fontsize=8,
    )
    # pylint: enable=line-too-long


def _plot_and_save_scores(
    output_dir,
    parameter,
    plot_scores_setup,
    sup_title,
    ltr_models_data,
    plot_setup,
    topography=None,
    debug=False,
):
    for ltr, models_data in ltr_models_data.items():
        ltr_info = f"_{ltr}"
        model_info = (
            "" if len(models_data.keys()) > 1 else f"_{next(iter(models_data.keys()))}"
        )
        for scores in plot_scores_setup:
            filename = (
                f"station_scores_{parameter}{ltr_info}{model_info}")
            fig, subplot_axes = _initialize_plots(
                models_data.keys(), scores, plot_setup=plot_setup, topography=topography
            )
            for idx, score in enumerate(scores):
                filename += f"_{score}"
                for model_idx, data in enumerate(models_data.values()):
                    ax = subplot_axes[idx][model_idx]
                    ax.get_yaxis().get_major_formatter().set_useOffset(False)
                    _add_datapoints2(
                        fig=fig,
                        data=data["df"],
                        score=score,
                        ax=ax,
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
    topography=None,
):
    # flat list of unique keys of dicts within models_data dict
    headers = [
        data["header"] for data in models_data[next(iter(models_data.keys()))].values()
    ]
    total_start_date, total_end_date = get_total_dates_from_headers(headers)
    # pylint: disable=line-too-long
    period_info = f"""{total_start_date.strftime("%Y-%m-%d %H:%M")} - {total_end_date.strftime("%Y-%m-%d %H:%M")} | © MeteoSwiss"""  # noqa: E501
    # pylint: enable=line-too-long
    sup_title = f"{parameter}: " + period_info

    _plot_and_save_scores(
        output_dir,
        parameter,
        plot_scores["regular_scores"],
        sup_title,
        models_data,
        plot_setup,
        topography=topography,
        debug=False,
    )
    _plot_and_save_scores(
        output_dir,
        parameter,
        plot_scores["cat_scores"],
        sup_title,
        models_data,
        plot_setup,
        topography=topography,
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
    topography=None,
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
                topography=topography,
            )


def _station_score_transformation(df, header):
    df = df.replace(float(header["Missing value code"][0]), np.NaN)
    df.rename(columns={"ScoreABO": "ABO"}, inplace=True)
    df.loc["lon"] = list(filter(None, header["Longitude"]))
    df.loc["lat"] = list(filter(None, header["Latitude"]))
    return df


# PLOTTING PIPELINE FOR STATION SCORES PLOTS
def _add_gridlines(ax):
    """Add gridlines with formatted coordinate labels to a map axis."""
    gl = ax.gridlines(
        draw_labels=True, ls="--", lw=0.5, x_inline=False, y_inline=False, zorder=11
    )
    gl.top_labels = True
    gl.left_labels = True
    gl.bottom_labels = False
    gl.right_labels = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {"rotation": 0}
    gl.ylabel_style = {"rotation": 0}


def _add_geographic_features(ax, topography=None):
    """Add geographic features (coastlines, borders, water bodies, topography) to a map axis."""
    ax.add_feature(cfeature.COASTLINE, alpha=0.5, rasterized=True, zorder=10)
    ax.add_feature(
        cfeature.BORDERS, linestyle="--", alpha=1, rasterized=True, zorder=10
    )
    ax.add_feature(cfeature.OCEAN, rasterized=True, zorder=10)
    ax.add_feature(cfeature.LAKES, alpha=0.5, rasterized=True, zorder=10)
    ax.add_feature(cfeature.RIVERS, alpha=0.5, rasterized=True, zorder=10)
    ax.add_feature(
        cfeature.NaturalEarthFeature(
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
    if topography:
        topo_file = Path(topography)
        if not topo_file.is_file():
            print(
                f"Warning: --topography file '{topography}' not found, "
                "skipping topography plotting."
            )
            return
        try:
            icon_ch1_eps_topo = Dataset(str(topo_file))
            ax.contourf(
                icon_ch1_eps_topo["x_1"][:].data,
                icon_ch1_eps_topo["y_1"][:].data,
                icon_ch1_eps_topo["HSURF"][0, ...].data,
                cmap="gray_r",
                levels=np.arange(0, 6000, 300),
            )
        except Exception as exc:  # pylint: disable=broad-except
            print(
                f"Warning: Failed to read topography file '{topo_file}': "
                f"{exc}. Skipping topography plotting."
            )


def _get_cached_background(extent, topography, projection):
    """Get or render a cached RGBA background image with all geographic features.

    Returns:
        Tuple of (rgba_array, xlim, ylim) where xlim/ylim are in the native
        projection coordinates.

    """
    cache_key = (tuple(extent), topography)
    if cache_key in _background_cache:
        return _background_cache[cache_key]

    print("  Pre-rendering map background (cached for subsequent plots)...")
    # Render at generous resolution; will be resampled into each subplot
    render_dpi = 150
    render_figsize = (14, 10)

    fig_temp = plt.figure(figsize=render_figsize, dpi=render_dpi)
    ax_temp = fig_temp.add_axes((0, 0, 1, 1), projection=projection)
    ax_temp.set_extent(extent, crs=ccrs.PlateCarree())  # type: ignore[union-attr]

    _add_geographic_features(ax_temp, topography)

    fig_temp.canvas.draw()
    renderer = fig_temp.canvas.get_renderer()  # type: ignore[attr-defined]

    # The GeoAxes enforces its own aspect ratio. Crop the RGBA buffer to the actual axes pixel region
    # so the image maps 1-to-1 onto (xlim, ylim) without squeezing.
    bbox = ax_temp.get_window_extent(renderer)
    full_rgba = np.array(fig_temp.canvas.buffer_rgba())  # type: ignore[attr-defined]
    h = full_rgba.shape[0]
    # buffer_rgba has origin at top-left; bbox at bottom-left -> flip y
    x0, x1 = int(bbox.x0), int(bbox.x1)
    y0, y1 = h - int(bbox.y1), h - int(bbox.y0)
    rgba = full_rgba[y0:y1, x0:x1].copy()

    xlim = ax_temp.get_xlim()
    ylim = ax_temp.get_ylim()
    plt.close(fig_temp)

    _background_cache[cache_key] = (rgba, xlim, ylim)
    return rgba, xlim, ylim


def _add_datapoints2(fig, data, score, ax, unit, param):
    # Workaround since check_params does not work for ATHD_S
    param = "ATHD_S" if param[0] == "ATHD_S" else check_params(param[0])
    if param is None:
        param = "*"

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
            param_score_range = param_score_range_fbi(param)

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

    norm = None
    if score.startswith("FBI"):
        if param.startswith("CLCT"):
            norm = mcolors.FuncNorm((_forward_spec, _inverse_spec),
                vmin=param_score_range["min"], vmax=param_score_range["max"]
            )
        else:
            norm = mcolors.FuncNorm((_forward, _inverse),
                vmin=param_score_range["min"], vmax=param_score_range["max"]
            )

    sc = ax.scatter(
        x=list(plot_data.loc["lon"]),
        y=list(plot_data.loc["lat"]),
        marker="o",
        c=list(plot_data.loc[score]),
        vmin=param_score_range["min"] if norm is None else None,
        vmax=param_score_range["max"] if norm is None else None,
        cmap=cmap,
        norm=norm,
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
        custom_ticks = fbi_custom_ticks(param)
        cbar.set_ticks(custom_ticks)
        cbar.ax.set_yticklabels([str(tick) for tick in custom_ticks])
    # Plot bar label
    if any(score.startswith(p) for p in unitless_scores):
        cbar.set_label(f"{score}")
    elif any(score.startswith(p) for p in unit_number_scores):
        cbar.set_label(f"{score}, (Number)")
    else:
        cbar.set_label(f"{score}, ({unit})")
    ax.scatter(
        x=list(nan_data.loc["lon"]),
        y=list(nan_data.loc["lat"]),
        marker=".",
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
    # Plot bar label
    if any(score.startswith(p) for p in unitless_scores):
        cbar.set_label(f"{score}")
    elif any(score.startswith(p) for p in unit_number_scores):
        cbar.set_label(f"{score} (Number)")
    else:
        cbar.set_label(f"{score} ({unit})")


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
