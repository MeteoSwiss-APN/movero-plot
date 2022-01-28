import pandas as pd
import matplotlib as mpl
from pprint import pprint


with open('config/plot_synop_ch', "r") as f:
    lines = [line.strip() for line in f.readlines()]

parameters = list(filter(None, lines[1].split(' ')))
scores = list(filter(None, lines[3].split(' ')))
number_of_lims = list(filter(None, lines[5].split(' ')))

columns = []
for parameter in parameters:
    columns.append(parameter+'_min')
    columns.append(parameter+'_max')

limits_df = pd.read_csv(
    'config/plot_synop_ch',
    sep='\s+',
    names=columns,
    dtype=float,
    skiprows=5,
    nrows = 12,
)

limits_df['scores'] = scores
limits_df = limits_df.set_index('scores')


colour_df = pd.read_csv(
    'config/plot_synop_ch',
    sep='\s+',
    names=parameters,
    dtype=str,
    skiprows=57,
    nrows = 12,
)

colour_df['scores'] = scores
colour_df = colour_df.set_index('scores')

pprint(colour_df)

pprint(limits_df)

# https://matplotlib.org/stable/tutorials/colors/colormaps.html
colour_df = colour_df.replace({'34':mpl.cm.jet})
colour_df = colour_df.replace({'48':mpl.cm.cubehelix})
colour_df = colour_df.replace({'52':mpl.cm.bwr})
colour_df = colour_df.replace({'53':mpl.cm.bwr_r})
colour_df = colour_df.replace({'54':mpl.cm.jet_r})
colour_df = colour_df.replace({'57':mpl.cm.jet_r}) 
colour_df = colour_df.replace({'58':mpl.cm.turbo})
colour_df = colour_df.replace({'59':mpl.cm.terrain_r})
colour_df = colour_df.replace({'60':mpl.cm.BrBG})
colour_df = colour_df.replace({'63':mpl.cm.Spectral})
colour_df = colour_df.replace({'64':mpl.cm.Spectral})