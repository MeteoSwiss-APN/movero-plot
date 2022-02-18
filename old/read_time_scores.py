# relevant imports for parsing pipeline
from pathlib import Path
import numpy as np
from pprint import pprint
import pandas as pd

# local
from plot_time_scores import generate_timeseries_plot
from utils.atab import Atab


# time_scores01-06_CLCT.dat       time_scores07-12_DD_10M.dat      time_scores13-18_DD_10M.dat      time_scores19-24_DD_10M.dat      time_scores25-30_DD_10M.dat
# time_scores01-06_DD_10M.dat     time_scores07-12_FF_10M.dat      time_scores13-18_FF_10M.dat      time_scores19-24_FF_10M.dat      time_scores25-30_FF_10M.dat
# time_scores01-06_FF_10M.dat     time_scores07-12_PMSL.dat        time_scores13-18_PMSL.dat        time_scores19-24_PMSL.dat        time_scores25-30_PMSL.dat
# time_scores01-06_PMSL.dat       time_scores07-12_PS.dat          time_scores13-18_PS.dat          time_scores19-24_PS.dat          time_scores25-30_PS.dat
# time_scores01-06_PS.dat         time_scores07-12_T_2M.dat        time_scores13-18_T_2M.dat        time_scores19-24_T_2M.dat        time_scores25-30_T_2M.dat
# time_scores01-06_T_2M.dat       time_scores07-12_TD_2M.dat       time_scores13-18_TD_2M.dat       time_scores19-24_TD_2M.dat       time_scores25-30_TD_2M.dat
# time_scores01-06_TD_2M.dat      time_scores07-12_TOT_PREC12.dat  time_scores13-18_TOT_PREC12.dat  time_scores19-24_TOT_PREC12.dat  time_scores25-30_TOT_PREC12.dat
# time_scores01-06_TOT_PREC6.dat  time_scores07-12_TOT_PREC6.dat   time_scores13-18_TOT_PREC6.dat   time_scores19-24_TOT_PREC6.dat   time_scores25-30_TOT_PREC6.dat
# time_scores01-06_VMAX_10M6.dat  time_scores07-12_VMAX_10M6.dat   time_scores13-18_VMAX_10M6.dat   time_scores19-24_VMAX_10M6.dat   time_scores25-30_VMAX_10M6.dat
# time_scores07-12_CLCT.dat       time_scores13-18_CLCT.dat        time_scores19-24_CLCT.dat        time_scores25-30_CLCT.dat


def read_files(
    lt_ranges, parameters, file_prefix, file_postfix, input_dir, output_dir, season, domain, scores, verbose
) -> None:
    """ Read all ```ATAB``` files that are present in: data_dir/season/domain/<file_prefix><...><file_postfix>
        Extract relevant information (parameters/scores) from these files into a dataframe. 
        Rows --> Scores | Columns --> Stations | For each parameter, a separate station_scores File exists. 


    Args:
        lt_ranges (list): lead time ranges, for which plots should be generated (i.e. 01-06, 07-12,...). part of the file name
        parameters (list): parameters, for which plots should be generated (i.e. CLCT, DD_10M, FF_10M, PMSL,...). part of file name
        file_prefix (str): prefix of files (i.e. station_scores)
        file_postfix (str): postfix of files (i.e. '.dat')
        input_dir (str): directory to seasons (i.e. /scratch/osm/movero/wd) 
        output_dir (str): output directory (i.e. plots/)
        season (str): season of interest (i.e. 2021s4/)
        domain (str): domain of interest (i.e. C-1E_ch)
        scores (list): list of scores, for which plots should be generated
        verbose (bool): print further comments
    """
    for lt_range in lt_ranges:
        for parameter in parameters:
            # define file path (atab file)
            file = f"{file_prefix}{lt_range}_{parameter}{file_postfix}"
            path = Path(f"{input_dir}/{season}/{domain}/{file}")
            
            if verbose:
                print(f"Filepath:\t{path}") # dbg

            # extract header
            header = Atab(file=path, sep=" ").header
            if verbose:
                print("\nFile header:")
                pprint(header)
            
            if False: # check later, which information of the header is actually relevant for the plotting pipeline
                relevant_header_information = {
                    "Start time": header["Start time"],
                    "End time": header[
                        "End time"
                    ],  # i.e. ['2021-11-30', '2300', '', '+000'],
                    "Missing value code": header["Missing value code"][0],
                    "Model name": header["Model name"][0],
                    "Model version": header["Model version"][0],
                    "Parameter": header["Parameter"][0],
                    "Unit": header["Unit"][0],
                }
                # pprint(relevant_header_information) # dbg


            # extract dataframe
            df = Atab(file=path, sep=" ").data

            pprint(header)
            pprint(df)
            print(df.columns.tolist())
            return

            # change type of time columns to str, s.t. they can be combined to one datetime column afterwards
            data_types_dict = {'YYYY': str, 'MM':str, 'DD':str, 'hh':str, 'mm':str}
            df = df.astype(data_types_dict)

            # create datetime column (just called time) & drop unnecessary columns
            df['datetime'] = pd.to_datetime(df['YYYY'] + '-' + df['MM'] + '-' + df['DD'] + ' ' + df['hh'] + ':' + df['mm'])
            df.drop(['YYYY', 'MM', 'DD', 'hh', 'mm'], axis=1, inplace=True)



            # > check which relevant scores are available; extract those from df
            all_scores = df.columns.tolist() 
            available_scores = ["datetime", "lt_hh", "lt_mm"] # TODO: clarify w/ Pirmin if lt_mm column is actually relevant ?!
            for score in scores:
                if score in all_scores:
                    available_scores.append(score)
                else:  # warn that a relevant score was not available in dataframe
                    print(f"{score} not available in {file}")
            
            df = df[available_scores]

            # > remove/replace missing values in dataframe with np.NaN
            df = df.replace(
                float(header["Missing value code"][0]), np.NaN
            )

            # > if there are rows (= scores), that only conaint np.NaN, remove them
            df = df.dropna(how = "all")

            if verbose:
                print("\nDataframe after some cleaning up:")
                pprint(df)
                print(f"Generating plot for {parameter} for lt_range: {lt_range}. (File: {file})")
                # for each score in df, create one map
            
            generate_timeseries_plot(
                data=df,
                lt_range=lt_range,
                variable=parameter,
                file=file,
                file_postfix=file_postfix,
                header_dict=header,
                domain=domain,
                output_dir=output_dir,
                verbose=verbose,
            )
    return