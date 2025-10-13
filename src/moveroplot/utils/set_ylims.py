"""Set the y-axis limits for the given parameter and score."""


def set_ylim(
    param, score, score_range, cat_score_range, ax, y_values
):  # pylint: disable=unused-argument
    # Find the actual parameter
    actual_param_candidates = [col[0] for col in score_range.columns if col[0] != "*"]

    if param in ["TOT_PREC3", "TOT_PREC6"]:
        actual_param = "TOT_PREC[36]"
    elif any(param == c for c in actual_param_candidates):
        actual_param = next(c for c in actual_param_candidates if param == c)
    elif any(
        param in c or c.replace("*", "") in param for c in actual_param_candidates
    ):
        actual_param = next(
            c
            for c in actual_param_candidates
            if param in c or c.replace("*", "") in param
        )
    else:
        actual_param = None

    # First, check for actual_param in score_range (MultiIndex columns)
    if actual_param in score_range.columns and score in score_range.index:
        # Extract the 'min' and 'max' columns for the given param
        min_col = (actual_param, "min")
        max_col = (actual_param, "max")

        lower_bound = score_range.loc[score, min_col]
        upper_bound = score_range.loc[score, max_col]

    # Second, check for actual_param in cat_score_range (Simple column structure)
    elif actual_param in cat_score_range.columns:
        # Filter for the given score in the categorial score range (score is not the index, but a column)
        filtered = cat_score_range[actual_param][
            cat_score_range[actual_param]["scores"] == score
        ]

        if not filtered.empty:
            lower_bound = filtered["min"].values[0]
            upper_bound = filtered["max"].values[0]

        # Put zero if score not found
        else:
            lower_bound = 0
            upper_bound = 0

    # Put zero if param not found
    else:
        lower_bound = 0
        upper_bound = 0

    # Get the data range
    y_values_min, y_values_max = min(y_values), max(y_values)

    # Get the current plotting limits
    lower_bound_before, upper_bound_before = ax.get_ylim()

    # If the limits have not been set, or the data range exceeds the set limits,
    # or the limits from the plot are set larger already, reset to auto
    if (
        (lower_bound == 0 and upper_bound == 0)
        or (y_values_min <= lower_bound and y_values_max >= upper_bound)
        or (lower_bound_before < lower_bound and upper_bound_before > upper_bound)
    ):
        ax.autoscale(axis="y")

    # If current data limit is below lower_bound or
    # if the lower_bound_before is below the lower_bound
    elif (y_values_min <= lower_bound) or (lower_bound_before < lower_bound):
        ax.autoscale(axis="y")
        ax.set_ylim(None, upper_bound)

    # If current data limit is above upper_bound or
    # if the upper_bound_before is above the upper_bound
    elif (y_values_max >= upper_bound) or (upper_bound_before > upper_bound):
        ax.autoscale(axis="y")
        ax.set_ylim(lower_bound, None)

    else:
        ax.autoscale(axis="y")
        ax.set_ylim(lower_bound, upper_bound)
