# Standard library
from pprint import pprint


def _parse_inputs(
    debug,
    plot_params,
    plot_scores,
    plot_cat_params,
    plot_cat_thresh,
    plot_cat_scores,
    plot_ens_params,
    plot_ens_thresh,
    plot_ens_scores,
):
    """Parse the user input flags.

    Args:
        debug (bool): Add debug statements to command prompt.
        plot_params (str): Long string w/ regular plot parameters. Separated by comma. I.e. "TOT_PREC12,TOT_PREC6,TOT_PREC1"
        plot_scores (str): Long strint w/ regular plot scores. Separated by comma. I.e. "ME,MMOD/MOBS,MAE". (Scores separated by '/' belong on the same plot.)
        plot_cat_params (str): Long string w/ categorical plot parameters. Separated by comma.
        plot_cat_thresh (str): Long string w/ categorical scores. Separated by comma. I.e. "FBI,MF,POD"
        plot_cat_scores (str): Long string w/ categorical scores thresholds. For each cat_score, there is a list of thresholds.
                               These 'sublists' are separated from one another w/ ':'. I.e. "0.1,1,10:0.2,1,5:0.2,0.5,2"
        plot_ens_params (str): Long string w/ ens plot parameters. Separated by comma.
        plot_ens_thresh (str): Long string w/ ens scores. Separated by comma.
        plot_ens_scores (str): Long string w/ ens scores thresholds. Separated by coma.

    Returns:
        dict: Dictionary w/ all relevant parameters as keys. Each key is assigned a list of lists containing the corresponding scores (&thresholds).

    """  # noqa: E501
    print("--- debugging user inputs")
    if debug:
        print("-------------------------------------------------------------")
    # initialise empty dictionaries
    regular_params_dict = None
    cat_params_dict = None
    ens_params_dict = None

    # REGULAR PARAMETERS
    if plot_params and plot_scores:
        params = plot_params.split(
            ","
        )  # TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL  # noqa: E501
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
        cat_params = plot_cat_params.split(
            ","
        )  # categorical parameters: TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1  # noqa: E501
        cat_scores = plot_cat_scores.split(
            ","
        )  # categorical scores: FBI,MF,POD,FAR,THS,ETS
        cat_threshs = plot_cat_thresh.split(
            ":"
        )  # categorical thresholds: 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20  # noqa: E501
        cat_params_dict = {cat_param: [] for cat_param in cat_params}
        for param, threshs in zip(cat_params, cat_threshs):
            # first append all scores w/o thresholds to parameter
            for score in plot_scores.split(","):
                if "/" in score:
                    cat_params_dict[param].append(score.split("/"))
                else:
                    cat_params_dict[param].append([score])

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

    # ENV PARAMETERS (TODO)
    if plot_ens_params and plot_ens_scores and plot_ens_thresh:
        ens_params_dict = {}
        print("extend code here to create a end-dict.")

    # merge the dictionaries if the exist
    # regular & categorical parameters together
    if regular_params_dict and cat_params_dict:
        params_dict = (
            regular_params_dict | cat_params_dict
        )  # merges the right dict into the left and is assigned to new dict
    # TODO: cover more cases, for the various possible combinations of dictionaries

    # only regular parameters
    elif regular_params_dict and not cat_params_dict and not ens_params_dict:
        params_dict = regular_params_dict

    elif cat_params_dict and not regular_params_dict and not ens_params_dict:
        params_dict = cat_params_dict

    if debug:
        print("Finally, the following parameter x score pairs will get plotted:")
        pprint(params_dict)
    return params_dict
