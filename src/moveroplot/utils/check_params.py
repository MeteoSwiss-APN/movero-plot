def check_params(param, verbose=False):
    # this list is compiled of all possible, generalised parameters, presend in the plot_synop_ch file.
    # this function compares a given input parameter (param) agains this list, and tries to map it to the
    # corresponding parameter.

    possible_params = [
        "*",
        "PMSL",
        "PS",
        "TD_2M*",
        "T_2M*",
        "CLCT",
        "DD*",
        "FF*",
        "TOT_PREC[36]",
        "TOT_PREC1",
        "TOT_PREC12",
        "VMAX*",
        "RELHUM_2M",
        "GLOB*",
        "DURSUN12",
        "DURSUN1",
    ]

    # if current param is not already a 'possible' parameter, iterate through the possible
    # parameters and find the correct match
    if param not in possible_params:
        # iterate through the list of 'possible' parameters and see if one of them
        # STARTS WITH the current parameter (i.e. GLOB* starts w/ GLOB)
        for possible_param in possible_params:
            if possible_param.startswith(param):
                if verbose:
                    print(f"{param} needs mapping\t\t-->\t{possible_param}")
                return possible_param

        # if none of the possible parameters start w/ current parameter,
        # split the current parameter. sep = '_'
        if "_" in param:
            if len(param.split("_")) > 2:  # i.e. param = T_2M_KAL --> tmp_param = T_2M
                tmp_param = param.split("_")[0] + "_" + param.split("_")[1]
            else:  # i.e. param = TD_2M --> tmp_param = TD
                tmp_param = param.split("_")[0]

            # again, iterate through the list of possible parameters and see if
            # one of them starts w/ the tmp_param (the first part of the current param)
            for possible_param in possible_params:
                if possible_param.startswith(tmp_param):
                    if verbose:
                        print(f"{param} needs mapping\t\t-->\t{possible_param}")
                    return possible_param

            else:
                # it might occur, that there are two separators in an actual param, but the matching
                # parameter in the possible params list only matches the first part. this is a special
                # case. i.e. FF_10M_KAL --> FF*; unlike T(D)_2M_KAL --> T(D)_2M.
                # thus split the tmp_param again and only proceed with the first part for the
                # matching procedure
                tmp_param = tmp_param.split("_")[0]
                for possible_param in possible_params:
                    if possible_param.startswith(tmp_param):
                        if verbose:
                            print(f"{param} needs mapping\t\t-->\t{possible_param}")
                        return possible_param

        else:
            if verbose:
                print(f"{param} needs mapping\t\t-->\t*")
            return "*"
    else:
        return param


def main():
    # run python <path/to/check_params.py> to see if the mapping works correctly.
    # add/remove parameters from actual_params for debugging & testing
    actual_params = [
        "TOT_PREC12",
        "TOT_PREC6",
        "TOT_PREC1",
        "CLCT",
        "GLOB",
        "DURSUN12",
        "DURSUN1",
        "T_2M",
        "T_2M_KAL",
        "TD_2M",
        "TD_2M_KAL",
        "RELHUM_2M",
        "FF_10M",
        "FF_10M_KAL",
        "VMAX_10M6",
        "VMAX_10M1",
        "DD_10M",
        "PS",
        "PMSL",
        "asdfasdf",
    ]
    for param in actual_params:
        param = check_params(param, True)
        # print(param)

    # param = check_params('TOT_PREC12')
    # print(param)


if __name__ == "__main__":
    main()
