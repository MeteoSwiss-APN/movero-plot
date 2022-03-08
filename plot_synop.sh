# python src/movero/plot_synop.py C-1E-CTR_ch --plot_params TOT_PREC12 --plot_scores MMOD/MOBS
# python src/movero/plot_synop.py C-1E-CTR_ch --plot_params CLCT --plot_scores MMOD/MOBS --plot_cat_params VMAX_10M1 --plot_cat_thresh 5,12.5,20 --plot_cat_scores THSAX_10M1 --plot_cat_thresh 5,12.5,20 --plot_cat_scores THS

# python src/movero/plot_synop.py C-1E-CTR_ch --plot_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL --plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS --plot_cat_params TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1 --plot_cat_thresh 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20 --plot_cat_scores FBI,MF/OF,POD,FAR,THS,ETS

python src/movero/plot_synop.py C-1E-CTR_ch --plot_params TOT_PREC12 --plot_scores ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS