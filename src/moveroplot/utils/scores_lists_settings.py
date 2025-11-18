#In this file are established divisions within lists in smaller lists with the same requirements, which are then used in the scores files
from matplotlib.colors import LinearSegmentedColormap
from .parse_plot_synop_ch import station_score_colortable, cat_station_score_colortable, verif_param, verif_scores, station_score_range, cat_station_score_range, cat_param

import numpy as np

#Define lists to use in the scores files to determine to which
#scores not assign a unit, and to which scores assign 'Number' as unit
unitless_scores=['FBI', 'MF', 'COR', 'OF', 'POD', 'FAR', 'THS', 'ETS', 'ACC', 'TSS', 'HSS']
unit_number_scores=['N', 'NMOD', 'NOBS']

#Determine color map and range of the color bar for station scores
def _determine_cmap_and_bounds(
    param,
    score,
    plot_data,
    param_score_range,
):
    #Set ranges
    if score in ["NOBS"]:
        param_score_range["min"] = 0
        param_score_range["max"] = np.ceil(plot_data.max())
    elif score.startswith(("MOBS")):
        param_score_range = station_score_range[param].loc["MMOD"]
    elif score.startswith("OF"):
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
    elif any(p.startswith(param)  or p.startswith(param) for p in verif_param) and score in verif_scores:
        param_score_range = station_score_range[param].loc[score]

    #Set cmap
    if score.startswith(("MMOD", "MOBS")):
        if param.startswith(("FF", "VMAX")):
            colors = [
                (0.027, 0.078, 0.976),
                (0.078, 0.286, 0.941),
                (0.098, 0.451, 0.878),
                (0.247, 0.631, 0.710),
                (0.529, 0.765, 0.510),
                (0.804, 0.882, 0.463),
                (0.984, 0.820, 0.373),
                (0.980, 0.631, 0.263),
                (0.961, 0.392, 0.369),
                (0.906, 0.000, 0.820),
                (0.961, 0.549, 0.871),
                (0.976, 0.753, 0.922),
                (0.996, 0.941, 0.945),
            ]
            cmap = LinearSegmentedColormap.from_list("wind_cmap", colors, N=256)
        elif param.startswith(("CLCT", "ATHD_S")):
            colors = [
                (0.949, 0.404, 0.235),
                (0.969, 0.549, 0.310),
                (0.980, 0.725, 0.396),
                (0.984, 0.855, 0.514),
                (0.996, 0.996, 0.714),
                (0.906, 0.906, 0.886),
                (0.737, 0.737, 0.757),
                (0.561, 0.561, 0.596),
                (0.329, 0.318, 0.376),
            ]
            cmap = LinearSegmentedColormap.from_list("cmap_glob", colors, N=256)
        elif param.startswith(("GLOB", "DURSUN")):
            colors = [
                (0.329, 0.318, 0.376),
                (0.561, 0.561, 0.596),
                (0.737, 0.737, 0.757),
                (0.906, 0.906, 0.886),
                (0.996, 0.996, 0.714),
                (0.984, 0.855, 0.514),
                (0.980, 0.725, 0.396),
                (0.969, 0.549, 0.310),
                (0.949, 0.404, 0.235),
            ]
            cmap = LinearSegmentedColormap.from_list("cmap_glob", colors, N=256)
        elif param.startswith(("PMSL", "PS", "TD_2M", "T_2M", "DD", "TOT_PREC", "RELHUM_2M")):
            cmap = station_score_colortable[param].loc["MMOD"]
        else:
            cmap = "viridis"
    elif any(p.startswith(param)  or param.startswith(p) for p in verif_param) and score in verif_scores:
        cmap = station_score_colortable[param].loc[score]
    elif any(p.startswith(param)  or param.startswith(p) for p in cat_param) and any(s.startswith(score)  or score.startswith(s) for s in cat_station_score_colortable[param].scores):
        table = cat_station_score_colortable[param]
        cmap = table.loc[table["scores"] == score, "cmap"].iloc[0]
    # Go to default if param is None or no option specified here
    else:
        cmap = "viridis"
    return cmap, param_score_range
