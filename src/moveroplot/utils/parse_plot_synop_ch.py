# pylint: disable=pointless-string-statement
"""Parse raw data from ATAB files.

#   The plot_synop_ch file contains the following look-up tables
    which can be imported from this file if necessary.
#   VERIFICATION PARAMETERS/SCORES:         CATEGORICAL PARAMETERS/SCORES:
#   > station_score_range                  > cat_station_score_range
#   > station_score_colortable             > cat_station_score_colortable
#   > time_score_range                     > cat_time_score_range
#   > daytime_score_range                  > cat_daytime_score_range
#   > total_score_range                    > cat_total_score_range
#
#   Change verbose to True, to check the dataframes and how they look.
"""
# pylint: enable=pointless-string-statement
# pylint: disable=using-constant-test
# Standard library
from pathlib import Path
from pprint import pprint

# Third-party
import pandas as pd

verbose = False
path = Path(__file__).with_name("plot_synop_ch")

# pylint: disable=unspecified-encoding
# open plot_synop_ch file
with open(path, "r") as f:
    lines = [line.strip() for line in f.readlines()]

# VERIFICATION SCORES; DATAFRAMES FOR SCORE RANGES AND COLOUR TABLE
# define the verification parameters / scores
verif_param = list(filter(None, lines[1].split(" ")))
verif_scores = list(
    filter(None, lines[3].split(" "))
)  # 12 different verification scores

if verbose:
    print(f"\nverification parameters: (#{len(verif_param)} params)\n", verif_param)
    print(f"\nverification scores: (#{len(verif_scores)} scores)\n", verif_scores)

# create 2D column names list
verif_param_range_cols = []
verif_params, verif_min_max = [], ["min", "max"] * len(verif_param)
for parameter in verif_param:
    verif_params.append(parameter)
    verif_params.append(parameter)
    verif_param_range_cols.append(parameter + "_min")
    verif_param_range_cols.append(parameter + "_max")
verif_columns = [verif_params, verif_min_max]

# create dataframe for station score ranges
if True:
    station_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=verif_param_range_cols,
        dtype=float,
        skiprows=5,
        nrows=len(verif_scores),
    )

    # add scores as column; use this column as index; rename all columns
    station_score_range["scores"] = verif_scores
    station_score_range = station_score_range.set_index("scores")
    station_score_range.columns = verif_columns  # type: ignore

    if verbose:
        print("\n Station Score Ranges")
        pprint(station_score_range)

# create dataframe for time score ranges
if True:
    time_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=verif_param_range_cols,
        dtype=float,
        skiprows=18,
        nrows=len(verif_scores),
    )

    time_score_range["scores"] = verif_scores
    time_score_range = time_score_range.set_index("scores")
    time_score_range.columns = verif_columns  # type: ignore

    if verbose:
        print("\n Time Score Ranges")
        pprint(time_score_range)

# create dataframe for daytime score ranges
if True:
    daytime_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=verif_param_range_cols,
        dtype=float,
        skiprows=31,
        nrows=len(verif_scores),
    )

    daytime_score_range["scores"] = verif_scores
    daytime_score_range = daytime_score_range.set_index("scores")
    daytime_score_range.columns = verif_columns  # type: ignore

    if verbose:
        print("\n Daytime Score Ranges")
        pprint(daytime_score_range)

# create dataframe for total score ranges
if True:
    total_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=verif_param_range_cols,
        dtype=float,
        skiprows=44,
        nrows=len(verif_scores),
    )

    total_score_range["scores"] = verif_scores
    total_score_range = total_score_range.set_index("scores")
    total_score_range.columns = verif_columns  # type: ignore

    if verbose:
        print("\n Total Score Ranges")
        pprint(total_score_range)

# create colour-table dataframe for the station scores (colour bar gradients)
if True:
    station_score_colortable = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=verif_param,
        dtype=str,
        skiprows=57,
        nrows=12,
    )

    station_score_colortable["scores"] = verif_scores
    station_score_colortable = station_score_colortable.set_index("scores")

    if verbose:
        print("\n Station Score Colour Table")
        pprint(station_score_colortable)
    # https://matplotlib.org/stable/tutorials/colors/colormaps.html
    # the mapping of the gradient indices happens here; I just picked the
    # colormaps, that seemed the most suitable. '_r' reverses the direction
    # of the gradient.
    # TODO: cmap 66, 67 need to be checked and replaced to be replaced.
    #       just included those not to have missing values

    # Create a dictionary to map scores to their respective colormaps
    color_map_dict = {
        "34": "jet",
        "48": "cubehelix",
        "52": "bwr",
        "53": "bwr_r",
        "54": "jet_r",
        "57": "jet_r",
        "58": "turbo",
        "59": "terrain",
        "60": "BrBG",
        "63": "Spectral",
        "64": "Spectral",
        "66": "Spectral",
        "67": "Spectral",
    }
    # Use the dictionary to replace scores with their respective colormaps
    station_score_colortable = station_score_colortable.replace(color_map_dict)


# CATEGORICAL SCORES; DATAFRAMES FOR SCORE RANGES AND COLOUR TABLE

# define the verification parameters / scores
cat_param = list(filter(None, lines[70].split(" ")))

# categorical parameter range columns looks like:
# [*_min, *_max, CLCT_min  CLCT_max, ...]
# this list is necessary, when reading the min/max tables for the first time.
cat_param_range_cols = []

# pylint: disable=line-too-long
# for subcolumns in pandas, the columns need to be initialised
# w/ two sublists: columns_list = [[sublist_1][sublist_2]]
# i.e. cat_columns = [['*', '*', '*', 'CLCT', ...], ['scores', 'min', 'max', 'scores', ....]]  # noqa: E501
# cat_params is the first sublist, where each param is listed 3 times. once for each of its subcolumns  # noqa: E501
# cat_scores_min_max is the second sublist, --> ['scores', 'min', 'max']*len(cat_param)
# cat_columns_tmp is the list of columns for the concatenated dataframe
#  there is one separate column for: <param>+['_score', '_min', '_max']
# i.e. cat_columns_tmp = [*_scores, *_min, *_max, CLCT_scores, CLCT_min, CLCT_max,....]
# based on the concat. df, the final range df w/ three subcolumns
# (scores, min, max) can be constructed  # noqa: E501
# pylint: enable=line-too-long

cat_columns_tmp, cat_params, cat_scores_min_max = (
    [],
    [],
    ["scores", "min", "max"] * len(cat_param),
)

for parameter in cat_param:
    # the dataframe from the csv file, only has two columns per parameter (min/max).
    # these columns are listed in the cat_param_range_cols
    cat_param_range_cols.append(parameter + "_min")
    cat_param_range_cols.append(parameter + "_max")

    # the tmp df (after reading the csv and concatenating w/ index dataframe;
    # before creating subcolumns),
    # has three columns for each parameter: scores, min, max.
    # these are merged in a next step into columns w/ subcolumns
    cat_columns_tmp.append(parameter + "_scores")
    cat_columns_tmp.append(parameter + "_min")
    cat_columns_tmp.append(parameter + "_max")

    # for each subcolumn, the corresponding parameter
    # must be repeated once in for sublist 1 (as mentioned above)  # noqa: E501
    cat_params.append(parameter)
    cat_params.append(parameter)
    cat_params.append(parameter)

# finally, the columns for the categorical scores is:
cat_columns = [cat_params, cat_scores_min_max]

cat_scores = []  # the cat_scores (indices in the dfs) are variable (for each cat_param)
line = 72  # the first line containing categorical scores
end = line + len(
    cat_param
)  # for each categorical parameter, one line containing all corresponding scores
while line < 85:
    cat_scores.append(list(filter(None, lines[line].split(" "))))
    line += 1

if verbose:
    print(f"\ncategorical parameters: (#{len(cat_param)} params)\n", cat_param)
    print(f"\ncategorical scores: (#{len(cat_scores)} scores)\n", cat_scores)


# create a parameter-scores mapping dataframe.
# for each parameter, we have a different set of scores
param_score_indices_mapping = {}
for i, param in enumerate(cat_param):
    param_score_indices_mapping[param + "_scores"] = cat_scores[i]
cat_param_score_mapping_df = pd.DataFrame(data=param_score_indices_mapping)

# create dataframe for categorical station score ranges
if True:
    cat_station_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=cat_param_range_cols,
        dtype=float,
        skiprows=86,
        nrows=len(cat_scores[0]),
    )

    # concatenate the df, with all max/min values for each param.
    # and the df with the indices for each param
    cat_station_score_range = pd.concat(
        [cat_station_score_range, cat_param_score_mapping_df], axis=1
    )

    # order the columns:
    # ['param1_scores', 'param1_min', 'param1_max',
    # 'param2_scores', 'param2_min', 'param2_max',...]
    cat_station_score_range = cat_station_score_range[cat_columns_tmp]
    # now that the columns are in the correct order,
    # create subcolumns (scores, min, max) for each parameter
    cat_station_score_range.columns = cat_columns  # type: ignore
    if verbose:
        print("\n Categorical Station Score Ranges")
        pprint(cat_station_score_range)


# create dataframe for categorical time score ranges
if True:
    cat_time_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=cat_param_range_cols,
        dtype=float,
        skiprows=105,
        nrows=len(cat_scores[0]),
    )

    # concatenate the df, with all max/min values for each param;
    # and the df with the indices for each param
    cat_time_score_range = pd.concat(
        [cat_time_score_range, cat_param_score_mapping_df], axis=1
    )
    """
    order the columns, s.t. they are:
    ['param1_scores', 'param1_min', 'param1_max', 'param2_scores',
    'param2_min', 'param2_max',...]
    """
    cat_time_score_range = cat_time_score_range[cat_columns_tmp]

    # now that the columns are in the correct order
    # create subcolumns (scores, min, max) for each parameter
    cat_time_score_range.columns = cat_columns  # type: ignore

    if verbose:
        print("\n Categorical Time Score Ranges")
        pprint(cat_time_score_range)


# create dataframe for categorical daytime score ranges
if True:
    cat_daytime_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=cat_param_range_cols,
        dtype=float,
        skiprows=124,
        nrows=len(cat_scores[0]),
    )

    # concatenate the df, with all max/min values for each param
    # and the df with the indices for each param
    cat_daytime_score_range = pd.concat(
        [cat_daytime_score_range, cat_param_score_mapping_df], axis=1
    )

    # order the columns, s.t. they are: ['param1_scores', 'param1_min',
    # 'param1_max', 'param2_scores', 'param2_min', 'param2_max',...]
    cat_daytime_score_range = cat_daytime_score_range[cat_columns_tmp]

    # now that the columns are in the correct order and
    # create subcolumns (scores, min, max) for each parameter
    cat_daytime_score_range.columns = cat_columns  # type: ignore

    if verbose:
        print("\n Categorical Dayime Score Ranges")
        pprint(cat_daytime_score_range)


# create dataframe for categorical total score ranges
if True:
    cat_total_score_range = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=cat_param_range_cols,
        dtype=float,
        skiprows=124,
        nrows=len(cat_scores[0]),
    )

    # concatenate the df, with all max/min values for each param;
    # and the df with the indices for each param
    cat_total_score_range = pd.concat(
        [cat_total_score_range, cat_param_score_mapping_df], axis=1
    )

    # order the columns, s.t. they are: ['param1_scores', 'param1_min', 'param1_max', $
    # 'param2_scores', 'param2_min', 'param2_max',...]
    cat_total_score_range = cat_total_score_range[cat_columns_tmp]

    # columns are in the correct order,
    # create subcolumns (scores, min, max) for each parameter
    cat_total_score_range.columns = cat_columns  # type: ignore

    if verbose:
        print("\n Categorical Total Score Ranges")
        pprint(cat_total_score_range)


# create colour-table dataframe for the categorical station scores
if True:
    sublist_1, sublist_2 = [], ["scores", "cmap"] * len(cat_param)
    tmp_colortable_columns = []
    tmp_concat_columns = []
    for param in cat_param:
        tmp_concat_columns.append(param + "_scores")
        tmp_concat_columns.append(param + "_cmap")
        tmp_colortable_columns.append(param + "_cmap")
        sublist_1.append(param)
        sublist_1.append(param)
    cat_colortable_columns = [sublist_1, sublist_2]

    cat_station_score_colortable = pd.read_csv(
        path,
        sep=r"\s+",  # noqa: W605
        names=tmp_colortable_columns,
        dtype=int,
        skiprows=162,
        nrows=len(cat_scores[0]),
    )

    # make df is of type str, s.t. the replacement works w/ strings.
    cat_station_score_colortable = cat_station_score_colortable.astype(str)

    # cat_station_score_colortable still has some 0
    # --> map either NaN or their appropriate cmap
    color_map_dict = {
        "34": "jet",
        "48": "cubehelix",
        "52": "bwr",
        "53": "bwr_r",
        "54": "jet_r",
        "57": "jet_r",
        "58": "turbo",
        "59": "terrain",
        "60": "BrBG",
        "63": "Spectral",
        "64": "Spectral",
    }
    cat_station_score_colortable = cat_station_score_colortable.replace(color_map_dict)

    # concat dataframes (colortable; parameter-score-indices)
    cat_station_score_colortable = pd.concat(
        [cat_station_score_colortable, cat_param_score_mapping_df], axis=1
    )
    # order the columns
    cat_station_score_colortable = cat_station_score_colortable[tmp_concat_columns]
    # create subcolumns
    cat_station_score_colortable.columns = cat_colortable_columns  # type: ignore

    if verbose:
        print("\n Categorical Station Score Colourtable")
        pprint(cat_station_score_colortable)
