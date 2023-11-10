#  pylint: skip-file
"""Parse raw data from ATAB files into data frame."""
# Standard library
from pprint import pprint
import re
from .config.plot_settings import PlotSettings


def _parse_inputs(
    debug,
    input_dir,
    model_versions,
    plot_params,
    plot_scores,
    plot_cat_params,
    plot_cat_thresh,
    plot_cat_scores,
    plotcolors,
):
    """Parse the user input flags.

    Args:
        debug (bool): Add debug statements to command prompt.
        model_versions (str): string of models (i.e. "C-1E_ch,C-1E-CTR_ch")
        plot_params (str): string w/ regular plot parameters.
                           i.e. "TOT_PREC12,TOT_PREC6,TOT_PREC1"
        plot_scores (str): strint w/ regular plot scores.
                           i.e. "ME,MMOD/MOBS,MAE".
                           Scores separated by '/' beon the same plot.
        plot_cat_params (str): string w/ categorical plot parameters. Separated by comma.
        plot_cat_thresh (str): string w/ categorical scores. i.e. "FBI,MF,POD"
        plot_cat_scores (str): string w/ categorical scores thresholds.
                               For each cat_score, there is a list of thresholds.
                               These 'sublists' are separated from one another w/ ':'.
                               I.e. "0.1,1,10:0.2,1,5:0.2,0.5,2"
        plot_ens_params (str): string w/ ens plot parameters. Separated by comma.
        plot_ens_thresh (str): string w/ ens scores. Separated by comma.
        plot_ens_scores (str): string w/ ens scores thresholds. Separated by coma.

    Returns:
        dict: Dictionary w/ all relevant parameters as keys.
        Each key is assigned a list of lists containing the corresponding scores.

    """  # noqa: E501
    print("--- parsing user inputs")
    if debug:
        print("-------------------------------------------------------------")

    plot_setup = dict()

    # Check if the model versions are in the input dir
    all_model_versions = re.split(r'[,/]', model_versions)
    model_directories = set([x.name for x in input_dir.iterdir() if x.is_dir()])
    if not set(all_model_versions).issubset(model_directories):
        not_in_dir = set(all_model_versions) - model_directories
        raise ValueError(
            f"""The model version inputs {list(not_in_dir)} do not exist in the directory {input_dir}."""
        )
    
    if plotcolors:
        color_list = plotcolors.split(",")
        if len(color_list) < len(all_model_versions):
            raise ValueError(f"""
            The input length --plotcolor is smaller than the number of models to plot ({len(color_list)} < {len(all_model_versions)})
            """)
        PlotSettings.modelcolors = color_list
    plot_models_setup = [model_combinations.split("/") for model_combinations in model_versions.split(",")]
    plot_setup["model_versions"] = plot_models_setup

    # initialise empty dictionaries
    regular_params_dict = {}
    cat_params_dict = {}

    plot_setup["parameter"] = None

    # REGULAR PARAMETERS
    if plot_params and plot_scores:
        params = plot_params.split(",")
        # TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,
        # TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,
        # FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
        scores = plot_scores.split(",")  # ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS
        regular_params_dict = {param: [] for param in params}
        for param in params:
            for score in scores:
                if "/" in score:
                    regular_params_dict[param].append(score.split("/"))
                else:
                    regular_params_dict[param].append([score])
        if debug:
            print("Regular Parameter Dict: ")
            pprint(regular_params_dict)

    # CATEGORICAL PARAMETERS
    if plot_cat_params and plot_cat_scores and plot_cat_thresh:
        cat_params = plot_cat_params.split(",")
        # categorical parameters: TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,
        # T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
        cat_scores = plot_cat_scores.split(
            ","
        )  # categorical scores: FBI,MF,POD,FAR,THS,ETS
        cat_threshs = plot_cat_thresh.split(":")
        print("PPPP ", plot_cat_params, plot_cat_scores, cat_scores)
        # categorical thresholds: 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,
        # 25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
        cat_params_dict = {cat_param: [] for cat_param in cat_params}
        for param, threshs in zip(cat_params, cat_threshs):
            # append all scores with a threshold in their name to current to parameter
            thresholds = threshs.split(",")
            for threshold in thresholds:
                for score in cat_scores:
                    if "/" in score:
                        cat_params_dict[param].append(
                            [x + f"({threshold})" for x in score.split("/")]
                        )
                    else:
                        cat_params_dict[param].append([f"{score}({threshold})"])

        if debug:
            print("Categorical Parameter Dict: ")
            pprint(cat_params_dict)
    plot_setup["parameter"] = {
        key: {
            "regular_scores": regular_params_dict.get(key, []),
            "cat_scores": cat_params_dict.get(key, []),
        }
        for key in regular_params_dict
    }

    if not plot_setup["parameter"]:
        raise IOError("Invalid Input: parameter and/or scores are missing.")

    if debug:
        print("Finally, the following parameter x score pairs will get plotted:")
        pprint(plot_setup)

    return plot_setup
