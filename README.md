# MOVERO PLOTS
## 0. GENERAL
### 0.1 Task Description / Overview
> **_Task_**: Replace the IDL plot scripts for the verification plots with Python scripts.
> There is a number of different plots, which need to be created. For each type of plot a number of scripts is necessary.

These plots need to be implemented:
1. Time Series of verification scores
2. Diurnal cycle of verification scores
3. Total scores depending on lead-time ranges
4. Numeric values of total scores



### 0.2 Usage
The entry point for this package is a script called [plot_synop](src/movero/plot_synop.py). By executing `python plot_synop.py --help`, one can see the required and optional command line inputs:
```
Usage: plot_synop.py [OPTIONS] MODEL_VERSION

  Entry Point for the MOVERO Plotting Pipeline.

  The only input argument is the MODEL_VERSION argument. Pass this along with any number
  of  options. These usually have a default value or are not necessary.

Options:
  --debug                         Add debug comments to command prompt.
  --lt_ranges TEXT                Specify the lead time range(s) of interest.
                                  Def: 19-24
  --plot_params TEXT              Specify parameters to plot.
  --plot_scores TEXT              Specify scores to plot.
  --plot_cat_params TEXT          Specify categorical parameters to plot.
  --plot_cat_thresh TEXT          Specify categorical scores thresholds to
                                  plot.
  --plot_cat_scores TEXT          Specify categorical scores to plot.
  --plot_ens_params TEXT          Specify ens parameters to plot.
  --plot_ens_thresh TEXT          Specify ens scores thresholds to plot.
  --plot_ens_scores TEXT          Specify ens scores thresholds to plot.
  --input_dir PATH                Specify input directory.
  --output_dir TEXT               Specify output directory. Def: plots
  --relief                        Add relief to maps.
  --grid                          Add grid to plots.
  --season [2020s4|2021s1|2021s2|2021s3|2021s4]
                                  Specify the season of interest. Def: 2021s4
  --help                          Show this message and exit.

```

> [time=Wed, Mar 2, 2022 2:21 PM]
**Command so far to create all plots for model v. C-1E-CTR_ch:**



```
python plot_synop.py C-1E-CTR_ch
--plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
--plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS
--plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
--plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
--plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS
```

`plot_synop.py` parses these user inputs into a _parameter dictionary_. Each provided parameter is one key in this dictionary. For every key, a list of corresponding scores is assigned.
![**Parameters Dictitonary**](https://i.imgur.com/kdQrufu.png)
Afterwards this `plot_setup` is passed to separate plotting pipelines. There, the source files are retrieved, parsed and plotted. Ultimately, all plots are placed in the `<output_dir>/<plot_type>/` directory.

## 1. SPATIAL VERIFICATION
<!-- ![alt text](http://i.imgur.com/8o44hib.png) -->

> Relevant File: [station_score.py](src/movero/station_scores.py)

The spatial verification plots feature a map, where all stations have are marked with a coloured dot. The colour of this dot corresponds to a colour-bar on the right side of the map. The smaller the deviation from the centre of the colourbar, the better. One can see directly, if & where the model performed well, or rather less so.

###### Example: Old Station Score Plot
<img src="https://i.imgur.com/LA2zev4.png)" alt="drawing" width="300"/>

###### Example: New Station Scores Plot
<img src="https://i.imgur.com/SiHcvpW.jpg" alt="drawing" width="300"/>

---


## 2. TIME SERIES OF VERIFICATION SCORES
> Relevant File: [time_scores.py](src/movero/time_scores.py)

###### Example: Old vs. New Station Scores Plot
![](https://i.imgur.com/g9t612p.png)
![](https://i.imgur.com/mlwMtTY.png)

---
## 3. DIURNAL CYCLYE OF VERIFICATION SCORES
> Relevant File: [daytime_scores.py](src/movero/daytime_scores.py)
###### Example: Old vs. New Station Scores Plot
![](https://i.imgur.com/FGSW1My.png)
![](https://i.imgur.com/pSNKEF4.png)


___
## 4. TOTAL SCORES DEP. ON LEAD-TIME RANGES

> Remark: how are scores assigned to subplots?
>
> die Reihenfolge in --plot_scores ist entscheidend. Es kommen immer 4 plots auf eine Seite für die normalen Scores. Die --plot_cat_scores beginnen auf jeden Fall auf einer neuen Seite, und jeder Threshold beginnt wieder auf einer neuen Seite.

###### Example: Old vs. New Station Scores Plot
![](https://i.imgur.com/RViAUU4.png)
![](https://i.imgur.com/2d69BoT.png)
