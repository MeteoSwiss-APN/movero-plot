# MOVERO PLOTS
## 0. GENERAL
> **_Task_**: Replace the IDL plot scripts for the verification plots with Python scripts. 
> There is a number of different plots, which need to be created. For each type of plot a number of scripts is necessary. 



2. Time Series of verification scores
![](https://i.imgur.com/xXSLJ4l.png =320x230)

3. Diurnal cycle of verification scores
![](https://i.imgur.com/swlWBA2.png =320x230)

4. Total scores depending on lead-time ranges
![](https://i.imgur.com/ZLYzobQ.png =320x230)


5. numeric values of total scores
![](https://i.imgur.com/sAUZPIU.png =80x230)


### 0.1 `plot_synop.py`
**Command so far:**
```
python plot_synop.py
--plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
--plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS
--plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
--plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
--plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS
```
`plot_synop` parses these user input flags into a _parameter dictionary_. Each parameter that has been provided is one key in said dictionary. For every key, one list of scores is assigned. 
![](https://i.imgur.com/kdQrufu.png)
Afterwards this `params_dict` should get passed to separate plotting pipelines for the various different plots. 

 
## 1. SPATIAL VERIFICATION
![alt text](http://i.imgur.com/8o44hib.png =320x230)

For each parameter, the scores *FBI, MF, POD, FAR, THS, ETS* have different threshols which are relevant. The **parameter -> score -> threshold mapping**, happens via 3 different user flags: 

```
--plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 
--plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20 
--plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS
```

These `cat_params` constitute a sub-set of all parameters, which can be specified using these two flags: 
```
--plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL 
--plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS 

```



---
#### OLD DOCS


For the generation of the spatial verification plots, three scripts interact with one another. 
First the user can call `python cli_station_scores.py --help` to see the possible user inputs:
```
Usage: cli_station_scores.py [OPTIONS]

  CREATE MOVERO STATION SCORES PLOTS 

Options:
  --input_dir PATH                Specify input directory.
  --output_dir TEXT               Specify output directory. Def: plots
  --season [2020s4|2021s1|2021s2|2021s3|2021s4]
                                  Specify the season of interest. Def: 2021s4
  --lt_ranges [01-06|07-12|13-18|19-24|25-30]
                                  Specify the lead time ranges of interest.
                                  Def: 19-24
  --domain [C-1E_ch|C-1E_alps]    Specify the domain of interest. Def: C-1E_ch
  --scores [ME|MMOD|MAE|STDE|RMSE|COR|NOBS|FBI|MF|POD|FAR|THS|ETS]
                                  Specify the scores of interest.
  --parameters [TOT_PREC12|TOT_PREC6|TOT_PREC1|CLCT|GLOB|DURSUN12|DURSUN1|T_2M|T_2M_KAL|TD_2M|TD_2M_KAL|RELHUM_2M|FF_10M|FF_10M_KAL|VMAX_10M6|VMAX_10M1|DD_10M|PS|PMSL]
                                  Specify the parameters of interest.
  --prefix TEXT                   Specify file prefix. Def: station_scores
  --postfix TEXT                  Specify output directory. Def: .dat
  --relief                        Add relief to map.
  --verbose                       Add comments to command prompt.
  --help                          Show this message and exit.
```
Most of them have default values - s.t. the user doesn't need to specify anything. Perhaps the most interesting flags are: `parameters` & `scores`. 

The source files for the station scores are called: `station_scores<lt-range>_<parameter>.dat`. The columns in this file correspond to the stations in Switzerland (159 in total). The rows correspond to the computed scores for the given parameter. 

### cli_station_scores



## 2. TIME SERIES OF VERIFICATION SCORES
started w/ this part by implementing parts of the `plot_timeseries` sub-package of the `plot_profile` package, see here: [GitHub Repo](https://github.com/MeteoSwiss-APN/plot_profile)

## 3. DIURNAL CYCLYE OF VERIFICATION SCORES
**TODO**
## 4. TOTAL SCORES DEP. ON LEAD-TIME RANGES
**TODO**
## 5. NUMERIC VALUES OF TOTAL SCORES
**TODO**