"""Command line interface of moveroplot."""
# Standard library
from pathlib import Path

# Third-party
import click
from click import Context

# Local
from . import __version__
from .main import main


@click.option(
    "--verbose",
    "-v",
    "verbose",
    help="Increase verbosity; specify multiple times for more.",
    count=True,
    is_eager=True,
    expose_value=False,
)
@click.version_option(__version__, "--version", "-V", message="%(version)s")
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.option(
    "--plot_type",
    type=str,
    help="""Specify the type of plot to generate:
    [total, time, station, daytime, ensemble].""",
)
@click.argument(
    "model_versions", type=str, default="C-1E-CTR_ch,C-1E_ch"
)  # help="Specify the correct run. I.e. C-1E-CTR_ch"
@click.option(
    "--debug", type=bool, is_flag=True, help="Add debug comments to command prompt."
)
@click.option(
    "--lt_ranges",
    type=str,
    default="19-24",
    help="Specify the lead time ranges of interest. Def: 19-24",
)
@click.option("--plot_params", type=str, help="Specify parameters to plot.")
# TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,GLOB,DURSUN12,DURSUN1,T_2M,T_2M_KAL,TD_2M,
# TD_2M_KAL,RELHUM_2M,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1,DD_10M,PS,PMSL
@click.option("--plot_scores", type=str, help="Specify scores to plot.")
# ME,MMOD/MOBS,MAE,STDE,RMSE,COR,NOBS
@click.option(
    "--plot_cat_params", type=str, help="Specify categorical parameters to plot."
)
# TOT_PREC12,TOT_PREC6,TOT_PREC1,CLCT,T_2M,T_2M_KAL,TD_2M,
# TD_2M_KAL,FF_10M,FF_10M_KAL,VMAX_10M6,VMAX_10M1
@click.option(
    "--plot_cat_thresh", type=str, help="Specify categorical scores thresholds to plot."
)
# 0.1,1,10:0.2,1,5:0.2,0.5,2:2.5,6.5:0,15,25:0,15,25:-5,5,
# 15:-5,5,15:2.5,5,10:2.5,5,10:5,12.5,20:5,12.5,20
@click.option("--plot_cat_scores", type=str, help="Specify categorical scores to plot.")
@click.option(
    "--plot_ens_params", type=str, help="Specify parameters to ensemble plots."
)
@click.option("--plot_ens_scores", type=str, help="Specify scores to ensemble plots.")
@click.option(
    "--plot_ens_cat_params",
    type=str,
    help="Specify categorical parameters to ensemble plots.",
)
@click.option(
    "--plot_ens_cat_scores",
    type=str,
    help="Specify categorical scores to ensemble plots.",
)
@click.option(
    "--plot_ens_cat_thresh",
    type=str,
    help="Specify categorical scores thresholds to ensemble plots.",
)
# FBI,MF,POD,FAR,THS,ETS
# C-1E-CTR_ch
# 🔰 new options for plot_synop call
@click.option(
    "--input_dir",
    type=click.Path(exists=True),
    default=Path("/scratch/osm/movero/wd/2022s4"),
    # default=Path("/scratch/kaufmann/movero/wd/2023s3_icon"),
    help="Specify input directory.",
)
@click.option(
    "--output_dir",
    type=str,
    default=Path("plots"),
    help="Specify output directory. Def: plots",
)
@click.option(
    "--colors",
    type=str,
    help="""Specify the plot color for each model version
    using matploblib's color coding""",
)
@click.option("--relief", type=bool, is_flag=True, help="Add relief to maps.")
@click.option("--grid", type=bool, is_flag=True, help="Add grid to plots.")
@click.pass_context
def cli(ctx: Context, **kwargs) -> None:
    """Console script for test_cli_project."""
    main(ctx, **kwargs)
