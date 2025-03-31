"""Set the y-axis limits for the given parameter and score."""

def set_ylim(param, score, score_range, cat_score_range, ax, y_values):  # pylint: disable=unused-argument
    
    
    # Find the actual parameter
    actual_param = None
    for col in score_range.columns:
        if col[0] != "*":
            if param in col[0] or col[0].replace('*', '') in param:
                actual_param = col[0]
    if not actual_param:
        for col in cat_score_range.columns:
            if col[0] != "*":
                if param in col[0] or col[0].replace('*', '') in param:
                    actual_param = col[0]

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
        filtered = cat_score_range[actual_param][cat_score_range[actual_param]["scores"] == score]

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
            
    # Check the data range and return to default if outside of the range
    y_values_min, y_values_max = min(y_values), max(y_values)

    # If the data range exceeds the set limits, reset to auto
    if y_values_min < lower_bound or y_values_max > upper_bound:
        ax.set_ylim(auto=True)
    else:
        ax.set_ylim(lower_bound, upper_bound)