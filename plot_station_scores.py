# relevant imports for plotting pipeline
import matplotlib.pyplot as plt
import numpy as np
import cartopy
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# local
from config.parse_plot_synop_ch import station_score_range
from config.parse_plot_synop_ch import station_score_colortable

# class to add relief to map
# > taken from: https://stackoverflow.com/questions/37423997/cartopy-shaded-relief
from cartopy.io.img_tiles import GoogleTiles
class ShadedReliefESRI(GoogleTiles):
    # shaded relief
    def _image_url(self, tile):
        x, y, z = tile
        url = (
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}.jpg"
        ).format(z=z, y=y, x=x)
        return url

def add_features(ax):
    """Add features to map."""
    # # point cartopy to the folder containing the shapefiles for the features on the map
    # earth_data_path = Path("src/pytrajplot/resources/")
    # assert (
    #     earth_data_path.exists()
    # ), f"The natural earth data could not be found at {earth_data_path}"
    # # earth_data_path = str(earth_data_path)
    # cartopy.config["pre_existing_data_dir"] = earth_data_path
    # cartopy.config["data_dir"] = earth_data_path

    # add grid & labels to map
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

    ax.add_feature(cfeature.LAND, rasterized=True, color="#FFFAF0")
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


def add_datapoints(data, score, ax, min, max, unit, param):

    # TODO: take the correct cmap form the colour_df
    cmap = station_score_colortable[param][score]

    # define limits for colour bar
    lower_bound = station_score_range[param]["min"].loc[score]
    upper_bound = station_score_range[param]["max"].loc[score]

    # if both are equal (i.e. 0), take the min/max values as limits
    if lower_bound == upper_bound:
        lower_bound = min
        upper_bound = max

    # print(param, score, lower_bound, upper_bound) # dbg
    tmp = False
    for (name, info) in data.iteritems():
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

            if True:  # add the short name of the stations as well
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


def add_text(
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
    footer = f"Model: {header_dict['Model version']} | Period: {header_dict['Start time'][0]} - {header_dict['End time'][0]} ({lt_range}) | Min: {min_value} {header_dict['Unit']} @ {min_station} | Max: {max_value} {header_dict['Unit']} @ {max_station} | © MeteoSwiss"

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


def generate_map_plot(
    data,
    lt_range,
    variable,
    file,
    file_postfix,
    header_dict,
    domain,
    output_dir,
    relief,
    verbose,
):
    """Generate Map Plot."""

    # extract scores, which are available in the dataframe (data)
    # for each score, create one map
    scores = data.index.tolist()
    scores.remove("lon")
    scores.remove("lat")

    for score in scores:

        if verbose:
            print(f"Plotting score:\t{score}")

        # create new dataframe, which only contains the lon/lat/score rows for all stations
        plot_quantities = ["lon", "lat", score]
        data_tmp = data.loc[plot_quantities]

        min_value = data_tmp.loc[score].min()
        max_value = data_tmp.loc[score].max()
        
        for station, value in data_tmp.loc[score].items():
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

        # cut map to domain (taken from pytrajplot)
        if domain == 'C-1E_ch':
            ax.set_extent([5.3, 11.2, 45.4, 48.2]) 
        if domain == 'C-1E_alps':
            ax.set_extent([0.7, 16.5, 42.3, 50])

        if relief:
            # add relief
            ax.add_image(ShadedReliefESRI(), 8)

        # add features/datapoints & text
        add_features(ax=ax)
        add_datapoints(
            data=data_tmp,
            score=score,
            ax=ax,
            min=min_value,
            max=max_value,
            unit=header_dict["Unit"],
            param=header_dict["Parameter"],
        )
        add_text(
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
        plt.savefig(f"{output_dir}/{file.split(file_postfix)[0]}_{score}.png")
        plt.close(fig)

    return

