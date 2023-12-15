#  pylint: skip-file
"""Parse raw data from ATAB files into data frame."""
# Standard library
import itertools
import re
from pprint import pprint

# Local
from .config.plot_settings import PlotSettings

invalid_ensemble_paramter = ["DD_10M", "PS", "PMSL"]


def _parse_inputs(
    debug,
    input_dir,
    model_versions,
    plot_params,
    plot_scores,
    plot_cat_params,
    plot_cat_thresh,
    plot_cat_scores,
    plot_ens_params,
    plot_ens_scores,
    plot_ens_cat_params,
    plot_ens_cat_thresh,
    plot_ens_cat_scores,
    plotcolors,
    plot_type,
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
    all_model_versions = re.split(r"[,/]", model_versions)
    model_directories = set([x.name for x in input_dir.iterdir() if x.is_dir()])
    if not set(all_model_versions).issubset(model_directories):
        not_in_dir = set(all_model_versions) - model_directories
        raise ValueError(
            f"""The model version inputs {list(not_in_dir)}
            do not exist in the directory {input_dir}."""
        )

    if plotcolors:
        color_list = plotcolors.split(",")
        if len(color_list) < len(all_model_versions):
            raise ValueError(
                f"""
            The input length --plotcolor is smaller than the
            number of models to plot ({len(color_list)} < {len(all_model_versions)})
            """
            )
        PlotSettings.modelcolors = color_list
    plot_models_setup = [
        model_combinations.split("/")
        for model_combinations in model_versions.split(",")
    ]
    plot_setup["model_versions"] = plot_models_setup

    # initialise empty dictionaries
    regular_params_dict = {}
    cat_params_dict = {}
    regular_ens_params_dict = {}
    ens_cat_params_dict = {}
    plot_setup["parameter"] = {}
    if plot_type in ["total", "time", "station", "daytime"]:
        if not any(
            [
                plot_params and plot_scores,
                plot_cat_params and plot_cat_scores and plot_cat_thresh,
            ]
        ):
            raise ValueError(
                f"Missing params, scores or thresholds for {plot_type} score plots."
            )
        # REGULAR PARAMETERS
        if plot_params and plot_scores:
            params = plot_params.split(",")
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
            cat_scores = plot_cat_scores.split(",")
            cat_threshs = plot_cat_thresh.split(":")
            cat_params_dict = {cat_param: [] for cat_param in cat_params}
            for param, threshs in zip(cat_params, cat_threshs):
                # append all scores with a threshold
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
    if plot_type == "ensemble":
        if not any(
            [
                plot_ens_params and plot_ens_scores,
                plot_ens_cat_params and plot_ens_cat_scores and plot_ens_cat_thresh,
            ]
        ):
            raise ValueError("Missing params, scores or thresholds for ensemble plots.")
        if plot_ens_params and plot_ens_scores:
            ens_params = plot_ens_params.split(",")
            for invalid_param in invalid_ensemble_paramter:
                if invalid_param in ens_params:
                    raise ValueError(
                        f"{invalid_param} us not a valid parameter for plot_ens_params."
                    )
            ens_scores = list()
            score_setups = [
                score_combinations.split("/")
                for score_combinations in plot_ens_scores.split(",")
            ]
            for score_set in score_setups:
                if "RANK" in score_set and len(score_set) > 1:
                    ens_scores.append(
                        [score for score in score_set if "RANK" not in score]
                    )
                    ens_scores.append(["RANK"])
                else:
                    ens_scores.append(score_set)

            regular_ens_params_dict = {param: [] for param in ens_params}
            for param in ens_params:
                regular_ens_params_dict[param].extend(ens_scores)

        if plot_ens_cat_params and plot_ens_cat_scores and plot_ens_cat_thresh:
            ens_cat_params = plot_ens_cat_params.split(",")
            ens_cat_scores = list()
            ens_cat_score_setups = [
                score_comb.split("/") for score_comb in plot_ens_cat_scores.split(",")
            ]
            for score_set in ens_cat_score_setups:
                if "REL_DIA" in score_set and len(score_set) > 1:
                    ens_cat_scores.append(
                        [score for score in score_set if "REL_DIA" not in score]
                    )
                    ens_cat_scores.append(["REL_DIA"])
                else:
                    ens_cat_scores.append(score_set)
            ens_cat_params_dict = {cat_param: [] for cat_param in ens_cat_params}
            for param, threshs in zip(ens_cat_params, plot_ens_cat_thresh.split(":")):
                param_thresh_combs = [
                    thresholds.split("/") for thresholds in threshs.split(",")
                ]
                for thresh_comb in param_thresh_combs:
                    for score_comb in ens_cat_scores:
                        _temp_scores = list()
                        for thresh, score in itertools.product(score_comb, thresh_comb):
                            _temp_scores.append(f"{thresh}({score})")
                        ens_cat_params_dict[param].append(_temp_scores)

    all_keys = (
        set(regular_params_dict)
        | set(cat_params_dict)
        | set(regular_ens_params_dict)
        | set(ens_cat_params_dict)
    )
    plot_setup["parameter"] = {
        key: {
            "regular_scores": regular_params_dict.get(key, []),
            "cat_scores": cat_params_dict.get(key, []),
            "regular_ens_scores": regular_ens_params_dict.get(key, []),
            "ens_cat_scores": ens_cat_params_dict.get(key, []),
        }
        for key in all_keys
    }
    if not plot_setup["parameter"]:
        raise IOError("Invalid Input: parameter and/or scores are missing.")

    if debug:
        print("Finally, the following parameter x score pairs will get plotted:")
        pprint(plot_setup)

    return plot_setup
