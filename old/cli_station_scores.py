"""
    New plotting pipeline for atab files to replace the IDL MOVERO Map Plots
    Author: Michel Zeller
    Date:   24.01.2022
"""

import click
from pathlib import Path

# Local
from read_station_scores import read_files


@click.command()
@click.option("--input_dir", type=click.Path(exists=True), default=Path('/scratch/osm/movero/wd'), help='Specify input directory.')
@click.option("--output_dir", type=str, default=Path('plots'), help='Specify output directory. Def: plots')
@click.option("--season", type=click.Choice([
    "2020s4",
    "2021s1",
    "2021s2", 
    "2021s3", 
    "2021s4",
]
), multiple=False, default="2021s4", help='Specify the season of interest. Def: 2021s4')
@click.option("--lt_ranges", type=click.Choice([
    "01-06",
    "07-12", 
    "13-18", 
    "19-24", 
    "25-30"
]
), multiple=True, default=("19-24",), help='Specify the lead time ranges of interest. Def: 19-24')
@click.option("--domain", type=click.Choice([
    "C-1E_ch",
    "C-1E_alps",
],
case_sensitive=False
), multiple=False, default="C-1E_ch", help='Specify the domain of interest. Def: C-1E_ch')
@click.option("--scores", type=click.Choice([
    "ME", 
    "MMOD", 
    "MAE", 
    "STDE", 
    "RMSE", 
    "COR", 
    "NOBS", 
    "FBI",
    "MF", 
    "POD",
    "FAR",
    "THS",
    "ETS"
],
case_sensitive=False
), multiple=True, help='Specify the scores of interest.')
@click.option("--parameters", type=click.Choice([
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
],
case_sensitive=False
), multiple=True, help='Specify the parameters of interest.')
@click.option("--prefix", type=str, default='station_scores', help='Specify file prefix. Def: station_scores')
@click.option("--postfix", type=str, default='.dat', help='Specify output directory. Def: .dat')
@click.option("--relief", type=bool, is_flag=True, help='Add relief to map.')
@click.option("--verbose", type=bool, is_flag=True, help='Add comments to command prompt.')

def main(
    *,
    input_dir: Path,
    output_dir: Path,
    season: str,
    lt_ranges: tuple, 
    domain: str,
    scores: tuple,
    parameters: tuple,
    prefix: str,
    postfix: str,
    relief:bool,
    verbose:bool,
) -> None:
    """ CREATE MOVERO STATION SCORES PLOTS
        Example: (default call; also runs if no flags get passed since they're all default values)
        python cli_station_scores.py --input_dir /scratch/osm/movero/wd --season 2020s4 --lt_ranges 19-24 --domain C-1E_ch --

    """
    # create output directory if it doesn't exist already
    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # dbg - s.t. i don't have to add all these flags the whole time, 
    # i just hard-code the parameters which have multiple options here
    # and use the default path to data for the time being.
    # /scratch/osm/movero/wd/2021s4/C-1E_ch/station_scores<lt_range>_<parameter>.dat

    # lt_ranges = (
    #     "01-06",
    #     "07-12", 
    #     "13-18", 
    #     "19-24", 
    #     "25-30"
    # )

    # if no parameter has been specified; use these
    if not parameters:
        parameters = (
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
        )


    if not scores:
        scores = (
            "ME", 
            "MMOD", 
            "MAE", 
            "STDE", 
            "RMSE", 
            "COR", 
            "NOBS", 
            "FBI",
            "MF", 
            "POD",
            "FAR",
            "THS",
            "ETS"
            )


    # iterate directory, create cleaned df, call plotting pipeline, save plots
    read_files(
        lt_ranges,
        parameters,
        prefix,
        postfix,
        input_dir,
        output_dir,
        season,
        domain,
        scores,
        relief,
        verbose,
    )

    return


if __name__ == "__main__":
    main()