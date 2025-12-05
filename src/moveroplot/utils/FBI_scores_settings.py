import numpy as np

# Set ranges for specific parameters under the FBI score
def param_score_range_fbi(param):
    return(
        {"min": 0.3, "max": 3}
        if param.startswith(("CLCT"))
        else {"min": 0.1, "max": 10}
    )

# fractions of the color bar (in [0,1])
t0, t1, t2, t3, t4 = 0.0, 0.25, 0.5, 0.75, 1.0

# Forward and inverse functions valid for most parameters
def _forward(x):
    """
    Maps [vmin, 0.5] and [2, vmax] logarithmically bended to [0, 0.25] and [0.75, 1.0] and maps [0.5, 1.0] and [1.0, 2.0] linearly bended to [0.25, 0.5] and [0.5, 0.75]
    """
    vmin = 0.1
    vmax = 10
    log_high_min = np.log10(2.0)
    log_high_max = np.log10(vmax)
    range_high_log = log_high_max - log_high_min
    x = np.asarray(x, dtype=float)
    y = np.empty_like(x, dtype=float)

    # masks for the 4 intervals
    m1 = x <= 0.5
    m2 = (x > 0.5) & (x <= 1.0)
    m3 = (x > 1.0) & (x <= 2.0)
    m4 = x > 2.0

    # 1) lower log
    y[m1] = (
        ((((np.log10(((x[m1]-vmin)*2.0+(0.5-x[m1])*vmax)/(0.5-vmin))-log_high_min) /      range_high_log) * (t1))*(-1))+t1
    )

    # 2) left linear
    y[m2] = (
        ((x[m2] - 0.5)*t2+(1-x[m2])*t1) / (1.0 - 0.5)
    )

    # 3) right linear
    y[m3] = (
        ((x[m3] - 1.0)*t3+(2.0-x[m3])*t2) / (2.0 - 1.0)
    )

    # 4) higher log
    y[m4] = (
        ((np.log10(x[m4]) - log_high_min) / range_high_log) * (t4 -   t3) + t3
    )
    return y

def _inverse(y):
    """Reverts the map [0,1] → x in (vmin–vmax)."""
    vmin = 0.1
    vmax = 10
    log_high_min = np.log10(2.0)
    log_high_max = np.log10(vmax)
    range_high_log = log_high_max - log_high_min
    y = np.asarray(y, dtype=float)
    x = np.empty_like(y, dtype=float)

    # same 4 intervals but in the normalized space
    n1 = y <= t1
    n2 = (y > t1) & (y <= t2)
    n3 = (y > t2) & (y <= t3)
    n4 = y > t3

    # 1) inverse lower log
    x[n1] = (((10**(
        ((((y[n1] - t1)/ ((-1)*(t1)))* range_high_log) )  + log_high_min))*(0.5-vmin)-0.5*vmax+2.0*vmin)/(2.0-vmax)
    )

    # 2) inverse left linear
    x[n2] = (
        (y[n2]*(1.0-0.5)+(0.5*t2-t1))/(t2-t1)
    )

    # 3) inverse right linear
    x[n3] = (
        (y[n3]*(2.0-1.0)+(t3-2.0*t2))/(t3-t2)
    )

    # 4) inverse higher log
    x[n4] = 10 ** (
        ((y[n4] - t3) / (t4 - t3)) * range_high_log + log_high_min
    )
    return x

# Forward and inverse functions valid for parameters "CLCT", "T_2M", "TD_2M"
def _forward_spec(x):
    """
    Maps [vmin, 0.75] and [1.5, vmax] logarithmically bended to [0, 0.25] and [0.75, 1.0] and maps [0.75, 1.0] and [1.0, 1.5] linearly bended to [0.25, 0.5] and [0.5, 0.75]
    """
    vmin = 0.3
    vmax = 3
    log_high_min = np.log10(1.5)
    log_high_max = np.log10(vmax)
    range_high_log = log_high_max - log_high_min
    x = np.asarray(x, dtype=float)
    y = np.empty_like(x, dtype=float)

    # masks for the 4 intervals
    m1 = x <= 0.75
    m2 = (x > 0.75) & (x <= 1.0)
    m3 = (x > 1.0) & (x <= 1.5)
    m4 = x > 1.5

    # 1) lower log
    y[m1] = (
        ((((np.log10(((x[m1]-vmin)*1.5+(0.75-x[m1])*vmax)/(0.75-vmin))-log_high_min) /      range_high_log) * (t1))*(-1))+t1
    )

    # 2) left linear
    y[m2] = (
        ((x[m2] - 0.75)*t2+(1-x[m2])*t1) / (1.0 - 0.75)
    )

    # 3) right linear
    y[m3] = (
        ((x[m3] - 1.0)*t3+(1.5-x[m3])*t2) / (1.5 - 1.0)
    )

    # 4) higher log
    y[m4] = (
        ((np.log10(x[m4]) - log_high_min) / range_high_log) * (t4 -   t3) + t3
    )
    return y

def _inverse_spec(y):
    """Reverts the map [0,1] → x in (vmin–vmax)."""
    vmin = 0.3
    vmax = 3
    log_high_min = np.log10(1.5)
    log_high_max = np.log10(vmax)
    range_high_log = log_high_max - log_high_min
    y = np.asarray(y, dtype=float)
    x = np.empty_like(y, dtype=float)

    # same 4 intervals but in the normalized space
    n1 = y <= t1
    n2 = (y > t1) & (y <= t2)
    n3 = (y > t2) & (y <= t3)
    n4 = y > t3

    # 1) inverse lower log
    x[n1] = (((10**(
        ((((y[n1] - t1)/ ((-1)*(t1)))* range_high_log) )  + log_high_min))*(0.75-vmin)-0.75*vmax+1.5*vmin)/(1.5-vmax)
    )

    # 2) inverse left linear
    x[n2] = (
        (y[n2]*(1.0-0.75)+(0.75*t2-t1))/(t2-t1)
    )

    # 3) inverse right linear
    x[n3] = (
        (y[n3]*(1.5-1.0)+(t3-1.5*t2))/(t3-t2)
    )

    # 4) inverse higher log
    x[n4] = 10 ** (
        ((y[n4] - t3) / (t4 - t3)) * range_high_log + log_high_min
    )
    return x

# Set ticks for specific parameters under the FBI score
def fbi_custom_ticks(param):
    return(
        [0.3, 0.5, 0.75, 0.9, 1, 1.2, 1.5, 2, 3]
        if param.startswith(("CLCT"))
        else [0.1, 0.3, 0.5, 0.75, 1, 1.5, 2, 4, 6, 8, 10]
    )
