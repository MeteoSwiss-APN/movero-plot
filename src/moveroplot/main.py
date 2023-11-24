# pylint: disable=line-too-long,pointless-string-statement
"""Parse the command which hitherto produced all verification plots.

This ensures, that the change in workflow is minimal.
Author: Michel Zeller
Date:   17.02.2022


Status of merging the former plot_synop command with IDL here.
❌ --> no longer necessary. IDL specific or resolved otherwise. (see config directory)
✅ --> implemented (as closely as possible)
⭕ --> not yet implemented - not sure about it.
🔰 --> additional new input flag

plot_synop
✅ --debug
✅ --domain=155,95,189,117
❌ --scaling_file=/users/kaufmann/movero/config/plot_synop/plot_synop_ch
❌ --const_file=/scratch/osm/movero/wd/2021s4/mod_data/C-1E-CTR_ch/mod_const_C-1E-CTR.txt
❌ --const_type=blk_table
❌ --ct_file=/users/kaufmann/movero/idl/colors1.tbl
✅ --lt_ranges=19-24,67-72
❌ --linecolors=
✅ --plot_params=TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,
      T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,
      FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
✅ --plot_cat_params=TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,
      T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
✅ --plot_ens_params=
✅ --plot_cat_thresh=0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,
     25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
✅ --plot_ens_thresh=
✅ --plot_scores=ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS
✅ --plot_cat_scores=FBI,MF/OF,POD,FAR,THS,ETS
✅ --plot_ens_scores= C-1E-CTR_ch
🔰 --input_dir
🔰 --output_dir
🔰 --relief

# Example Command: (ugly)
python plot_synop.py C-1E-CTR_ch --plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL --plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS --plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 --plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20 --plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS

# Example Command: (short)
python plot_synop.py C-1E-CTR_ch --plot_params TOT_PREC12 --plot_scores ME --plot_cat_params VMAX_10M1 --plot_cat_thresh 5,12.5,20 --plot_cat_scores THS,ETS
python plot_synop.py C-1E_ch --plot_params CLCT --plot_scores MMOD/MOBS
"""  # noqa: E501
# Standard library
from pathlib import Path
from typing import Optional

# Third-party
from click import Context

# Local
from .daytime_scores import _daytime_scores_pipeline

# local
from .parse_inputs import _parse_inputs
from .station_scores import _station_scores_pipeline
from .time_scores import _time_scores_pipeline
from .total_scores import _total_scores_pipeline
from .ensemble_scores import _ensemble_scores_pipeline


# pylint: enable=line-too-long
# pylint: disable=unused-argument,too-many-locals
# pylint: disable=too-many-arguments,pointless-string-statement
def main(
    ctx: Context,
    *,
    # legacy inputs
    model_versions: str,
    debug: bool,
    lt_ranges: tuple,
    # Parameters / Scores / Thresholds
    plot_params: Optional[str],
    plot_scores: Optional[str],
    plot_cat_params: Optional[str],
    plot_cat_thresh: Optional[str],
    plot_cat_scores: Optional[str],
    plot_ens_params: Optional[str],
    plot_ens_scores: Optional[str],
    plot_ens_cat_params: Optional[str],
    plot_ens_cat_thresh: Optional[str],
    plot_ens_cat_scores: Optional[str],
    # new inputs
    input_dir: Path,
    output_dir: Optional[str],
    relief: bool,
    grid: bool,
    colors: Optional[str],
):
    """Entry Point for the MOVERO Plotting Pipeline.

    The only input argument is the RUN argument.
    Pass this along with any number of options.
    These usually have a default value or are not necessary.

    Example Command: (to generate all plots for C-1E-CTR_ch)

    python plot_synop.py C-1E-CTR_ch

    --plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,
                    GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,
                    TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,
                    FF_10M_KAL,VMAX_10M6,VMAX_10M1,
                    DD_10M,PS,PMSL

    --plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS

    --plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,
                    T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,
                    FF_10M_KAL,VMAX_10M6,VMAX_10M1

    --plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,
                      6.5:0,15,25:0,15,25:-5,5,15:-5,
                      5,15:2.5,5,10:2.5,5,10:5,12.5,
                      20:5,12.5,20

    --plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS
    """  # noqa: E501
    # -1. DEFINE PLOTS
    station_scores = False
    time_scores = False
    daytime_scores = False
    total_scores = False
    ensemble_scores = True

    if not Path(output_dir).exists():
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    # 0. PARSE USER INPUT
    plot_setup = _parse_inputs(
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
        colors,
    )

    # 1. INITIALISE STATION SCORES PLOTTING PIPELINE
    if station_scores:
        _station_scores_pipeline(
            plot_setup=plot_setup,
            lt_ranges=lt_ranges,
            file_prefix="station_scores",
            file_postfix=".dat",
            input_dir=input_dir,
            output_dir=output_dir,
            debug=debug,
        )
    # 2. INITIALISE TIME SERIES PLOTTING PIPELINE
    if time_scores:
        _time_scores_pipeline(
            plot_setup=plot_setup,
            lt_ranges=lt_ranges,
            file_prefix="time_scores",
            file_postfix=".dat",
            input_dir=input_dir,
            output_dir=output_dir,
            debug=debug,
        )
    # 3. INITIALISE DYURNAL CYCLE PLOTTING PIPELINE
    if daytime_scores:
        _daytime_scores_pipeline(
            plot_setup=plot_setup,
            lt_ranges=lt_ranges,
            file_prefix="daytime_scores",
            file_postfix=".dat",
            input_dir=input_dir,
            output_dir=output_dir,
            debug=debug,
        )
    # 4. INITIALIS TOTAL SCORES PLOTTING PIPELINE
    if total_scores:
        _total_scores_pipeline(
            plot_setup=plot_setup,
            lt_ranges=lt_ranges,
            file_prefix="total_scores",
            file_postfix=".dat",
            input_dir=input_dir,
            output_dir=output_dir,
            debug=debug,
        )

    if ensemble_scores:
        _ensemble_scores_pipeline(
            plot_setup=plot_setup,
            lt_ranges=lt_ranges,
            file_prefix="total_scores",
            file_postfix=".dat",
            input_dir=input_dir,
            output_dir=output_dir,
            debug=debug,
        )
    print("\n--- Done.")
