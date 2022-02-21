"""
This file intends to parse the command, which hitherto produced all verification plots.
This ensures, that the change in workflow is minimal.
Author: Michel Zeller
Date:   17.02.2022
"""
from pathlib import Path
from pprint import pprint
import click

# local
from station_scores import station_scores_pipeline

"""
Status of merging the former plot_synop command with IDL here. 
❌ --> no longer necessary. IDL specific or resovled otherwise. (see config directory)
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
✅ --plot_params=TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL 
✅ --plot_cat_params=TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 
✅ --plot_ens_params= 
✅ --plot_cat_thresh=0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20 
✅ --plot_ens_thresh= 
✅ --plot_scores=ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS 
✅ --plot_cat_scores=FBI,MF,POD,FAR,THS,ETS 
✅ --plot_ens_scores= C-1E-CTR_ch
🔰 --input_dir
🔰 --output_dir
🔰 --relief

# Example Command: (ugly)
python plot_synop.py --plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL --plot_scores ME,MMOD,MAE,STDE,RMSE,COR,NOBS --plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 --plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20 --plot_cat_scores FBI,MF,POD,FAR,THS,ETS
"""



import click
@click.command()
@click.option("--debug", type=bool, is_flag=True, help='Add debug comments to command prompt.')
@click.option("--domain", type=click.Choice([
    "C-1E_ch",
    "C-1E_alps",
],
case_sensitive=False
), multiple=False, default="C-1E_ch", help='Specify the domain of interest. Def: C-1E_ch')
@click.option("--lt_ranges", type=click.Choice([
    "01-06",
    "07-12", 
    "13-18", 
    "19-24", 
    "25-30"
]
), multiple=True, default=("19-24",), help='Specify the lead time ranges of interest. Def: 19-24')
@click.option("--plot_params", type=str, help='Specify parameters to plot.')
# TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL 
@click.option("--plot_scores", type=str, help='Specify scores to plot.')
# ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS 
@click.option("--plot_cat_params", type=str, help='Specify categorical parameters to plot.')
# TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 
@click.option("--plot_cat_thresh", type=str, help='Specify categorical scores thresholds to plot.')
# 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20  
@click.option("--plot_cat_scores", type=str, help='Specify categorical scores to plot.')
# FBI,MF,POD,FAR,THS,ETS
@click.option("--plot_ens_params", type=str, help='Specify ens parameters to plot.')        # TODO: figure out what ens params are
@click.option("--plot_ens_thresh", type=str, help='Specify ens scores thresholds to plot.') # TODO: figure out what ens thresh are
@click.option("--plot_ens_scores", type=str, help='Specify ens scores thresholds to plot.') # TODO: figure out what ens scores are
# C-1E-CTR_ch
# 🔰 new options for plot_synop call
@click.option("--input_dir", type=click.Path(exists=True), default=Path('/scratch/osm/movero/wd'), help='Specify input directory.')
@click.option("--output_dir", type=str, default=Path('plots'), help='Specify output directory. Def: plots')
@click.option("--relief", type=bool, is_flag=True, help='Add relief to map.')
@click.option("--season", type=click.Choice([
    "2020s4",
    "2021s1",
    "2021s2", 
    "2021s3", 
    "2021s4",
]
), multiple=False, default="2021s4", help='Specify the season of interest. Def: 2021s4')

def main(
    *,
    # legacy inputs
    debug: bool,
    domain: str,
    lt_ranges:tuple,
    # Parameters / Scores / Thresholds
    plot_params:str,
    plot_scores:str,
    plot_cat_params:str,
    plot_cat_thresh:str,
    plot_cat_scores:str,
    plot_ens_params:str,
    plot_ens_thresh:str,
    plot_ens_scores:str,
    # new inputs
    input_dir: Path,
    output_dir:str,
    relief:bool,
    season:str,
):
##### 0. PARSE USER INPUT ##################################################################################################################################################################
    if debug:
        print('---------------------------------------------------------------------------------------------------------------------------')
    multiplots = set([])

    # REGULAR PARAMETERS
    params = plot_params.split(',') # TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
    scores = plot_scores.split(',') # ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS     
    regular_params_dict = {param: [] for param in params}
    for param in params:
        for score in scores:
            if '/' in score:
                multiplots.add(score)
                regular_params_dict[param].append(f"{score.split('/')[0]}")
                regular_params_dict[param].append(f"{score.split('/')[1]}")
            else:
                regular_params_dict[param].append(f"{score.split('/')[0]}")

    # CATEGORICAL PARAMETERS
    cat_params = plot_cat_params.split(',')  # categorical parameters: TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
    cat_scores = plot_cat_scores.split(',')  # categorical scores: FBI,MF,POD,FAR,THS,ETS
    cat_threshs = plot_cat_thresh.split(':') # categorical thresholds: 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
    cat_params_dict = {cat_param: [] for cat_param in cat_params}
    for param, threshs in zip(cat_params, cat_threshs):
        # first append all scores w/o thresholds to parameter
        for score in plot_scores.split(','):     
            if '/' in score:
                multiplots.add(score)
                cat_params_dict[param].append(f"{score.split('/')[0]}")
                cat_params_dict[param].append(f"{score.split('/')[1]}")    
            else: 
                cat_params_dict[param].append(f"{score}")

        # afterwards append all scores that have a threshold in their name to current to parameter
        thresholds = threshs.split(',')
        for threshold in thresholds:
            for score in cat_scores:     
                if '/' in score:
                    multiplots.add(score)
                    cat_params_dict[param].append(f"{score.split('/')[0]}({threshold})")
                    cat_params_dict[param].append(f"{score.split('/')[1]}({threshold})")    
                else: 
                    cat_params_dict[param].append(f"{score}({threshold})")


    # ENV PARAMATERS (TODO)

    # merge the dictionaries
    params_dict = regular_params_dict | cat_params_dict # merges the right dict into the left and is assigned to new dict
    if debug:
        print(f"The following parameter x score pairs will get plotted:")
        pprint(params_dict)
        print(f"The following parameters will be on combined plots:")
        print(multiplots)
        print('---------------------------------------------------------------------------------------------------------------------------')

##### 1. INITIALISE STATION SCORES PLOTTING PIPELINE########################################################################################################################################       
    station_scores_pipeline(
        params_dict=params_dict,
        lt_ranges=lt_ranges,
        file_prefix='station_scores', 
        file_postfix = '.dat',
        input_dir=input_dir,
        output_dir=output_dir,
        season=season,
        domain=domain,
        relief=relief,
        verbose=debug
    )


    return

if __name__ == "__main__":
    main()