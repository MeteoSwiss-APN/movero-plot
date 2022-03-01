# MOVERO PLOTS
## 0. GENERAL
> **_Task_**: Replace the IDL plot scripts for the verification plots with Python scripts. 
> There is a number of different plots, which need to be created. For each type of plot a number of scripts is necessary. 

1. Time Series of verification scores
![](https://i.imgur.com/xXSLJ4l.png)

2. Diurnal cycle of verification scores
![](https://i.imgur.com/swlWBA2.png)

3. Total scores depending on lead-time ranges
![](https://i.imgur.com/ZLYzobQ.png)

4. Numeric values of total scores
![](https://i.imgur.com/sAUZPIU.png)


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
`plot_synop` parses these user inputs into a _parameter dictionary_. Each parameter that has been provided is one key in this dictionary. For every key, a list of corresponding scores is assigned. 
![**Parameters Dictitonary**](https://i.imgur.com/kdQrufu.png)
Afterwards this `params_dict` should get passed to separate plotting pipelines for the various different plots. 

For each parameter, the scores *FBI, MF, POD, FAR, THS, ETS* have different thresholds that are relevant. The **parameter -> score -> threshold** mapping happens with three different user flags: 

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

## 1. SPATIAL VERIFICATION
<!-- ![alt text](http://i.imgur.com/8o44hib.png) -->
The corresponding file for the parsing of the `station_scores` Files and generating the map plots is: [station_score.py](src/pytrajplot/cli.py).

The spatial verification plots feature a map, where all measurement stations are marked with a coloured dot. The colour of this dot corresponds to a colour-bar on the right side. The smaller the deviation from the centre of th e colourbar, the better.





---


## 2. TIME SERIES OF VERIFICATION SCORES
started w/ this part by implementing parts of the `plot_timeseries` sub-package of the `plot_profile` package, see here: [GitHub Repo](https://github.com/MeteoSwiss-APN/plot_profile)

## 3. DIURNAL CYCLYE OF VERIFICATION SCORES
**TODO**
## 4. TOTAL SCORES DEP. ON LEAD-TIME RANGES
**TODO**
## 5. NUMERIC VALUES OF TOTAL SCORES
**TODO**