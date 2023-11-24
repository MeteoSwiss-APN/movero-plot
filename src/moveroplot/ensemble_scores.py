"""Calculate ensemble scores from parsed data."""
# Standard library
from pathlib import Path
from pprint import pprint
from datetime import datetime
import re

# Third-party
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from .config.plot_settings import PlotSettings

# Third-party
from matplotlib.lines import Line2D

# Local
# pylint: disable=no-name-in-module
from .utils.atab import Atab
from .utils.check_params import check_params
from .utils.parse_plot_synop_ch import total_score_range
from .total_scores import _initialize_plots
from .total_scores import _customise_ax, _set_ylim, _save_figure

ens_plot_function_dict = {
    "OUTLIERS": None,
    "RPS": None,
    "RPS_REF": None,
    "RPSS": None,
    "RANK": None,
    "REL": None,
    "RES": None,
    "BS": None,
    "BS_REF": None,
    "BSS": None,
    "BSSD": None,
    "REL_DIA": None,
}

def memoize(func):
    cache = {}

    def wrapper(*args):
        if args in cache:
            return cache[args]
        result = func(*args)
        cache[args] = result
        return result

    return wrapper

def collect_relevant_files(
    input_dir, file_prefix, file_postfix, debug, model_plots, parameter, lt_ranges
):
    corresponding_files_dict = {}
    extracted_model_data = {}
    # for dbg purposes:
    files_list = []
    for model in model_plots:
        source_path = Path(f"{input_dir}/{model}")
        for file_path in source_path.glob(f"{file_prefix}*{parameter}{file_postfix}"):
            if file_path.is_file():
                ltr_match = re.search(r"(\d{2})-(\d{2})", file_path.name)
                if ltr_match:
                    lt_range = ltr_match.group()
                else:
                    raise IOError(
                        f"The filename {file_path.name} does not contain a LT range."
                    )

                in_lt_ranges = True
                
                if lt_ranges:
                    in_lt_ranges = lt_range in lt_ranges

                if in_lt_ranges:
                    # extract header & dataframe
                    loaded_Atab = Atab(file=file_path, sep=" ")

                    header = loaded_Atab.header
                    df = loaded_Atab.data
                    # clean df
                    df = df.replace(float(header["Missing value code"][0]), np.NaN)
                    df.set_index(keys="Score", inplace=True)

                    # add information to dict
                    if lt_range not in corresponding_files_dict:
                        corresponding_files_dict[lt_range] = {}

                    corresponding_files_dict[lt_range][model] = {
                        "header": header,
                        "df": df,
                    }

                    # add path of file to list of relevant files
                    files_list.append(file_path)

    if debug:
        print(f"\nFor parameter: {parameter} these files are relevant:\n")
        pprint(files_list)

    extracted_model_data = corresponding_files_dict
    return extracted_model_data


def _ensemble_scores_pipeline(
    plot_setup,
    lt_ranges,
    file_prefix,
    file_postfix,
    input_dir,
    output_dir,
    debug,
) -> None:
    print("PLOT SETUP ", plot_setup)
    if not lt_ranges:
        lt_ranges = "19-24"
    for model_plots in plot_setup["model_versions"]:
        for parameter, scores in plot_setup["parameter"].items():
            model_data = {}
            model_data = collect_relevant_files(
                input_dir,
                file_prefix,
                file_postfix,
                debug,
                model_plots,
                parameter,
                lt_ranges,
            )
            print(model_data.keys())
            
            print("MODELS DATA ",model_data[next(iter(model_data.keys()))].keys() )
            _generate_ensemble_scores_plots(
                plot_scores=scores,
                models_data=model_data,
                parameter=parameter,
                output_dir=output_dir,
                debug=debug,
            )

def num_sort(test_string):
    return list(map(int, re.findall(r'\d+', test_string)))[0]

def _plot_and_save_scores(
    output_dir,
    base_filename,
    parameter,
    plot_scores_setup,
    sup_title,
    models_data,
    models_color_lines,
    debug=False,
):
    filename = base_filename
    fig, subplot_axes = _initialize_plots(models_color_lines, models_data.keys())
    for idx, score_setup in enumerate(plot_scores_setup):
        print("SCORE SETUP ", score_setup, models_data.keys())
        for score_idx, score in enumerate(score_setup):
            if score == "RANK":
                
                for ltr, model_data in models_data.items():
                    fig, ((ax0), (ax2)) = plt.subplots(nrows=2, ncols=1)
                    for model_idx, (model_version, data) in enumerate(model_data.items()):
                        model_ranks = sorted([index for index in data["df"]["Total"].index if "RANK" in index], key=lambda x: int(''.join(filter(str.isdigit, x))))
                        ds = data["df"]["Total"][model_ranks].reset_index(drop=True)
                        print("MODEK RANKS ",model_ranks)
                        ax0.bar(np.arange(len(model_ranks))+model_idx*0.25, ds, width=0.25)

                    fig.savefig(f"{output_dir}/test.png")
            
            else:
                return
                ltr_list = []
                for model_version, data in models_data.items():
                    ltr_sorted = sorted(
                        list(data.keys()), key=lambda x: int(x.split("-")[0])
                    )
                    ltr_list += ltr_sorted
                ltr = "19-24"
                all_indices = set().union(
                    *(
                        series[ltr]["df"]["Total"].index
                        for series in models_data.values()
                    )
                )
                all_ranks = [
                    index for index in all_indices if "RANK" in index
                ]
                model_rank_data = pd.DataFrame()
                print(all_ranks)
                for model_version, data in models_data.items():
                    model_data = data[ltr]["df"]["Total"]
                    rank_cols = sorted(
                        [ind for ind in model_data.index if "RANK" in ind]
                    )
                    model_rank_data[model_version] = model_data.loc[rank_cols].reindex(all_ranks).fillna(0)

                model_rank_data = model_rank_data.sort_index()
                #print("RANK COLS \n", model_rank_data)
                # print("MODEL RANKS ", model_ranks , "\n", next(iter(models_data.values()))['19-24']['df'].loc['RANK[8]'])
                pass
            else:
                pass

        return
        for model_idx, data in enumerate(models_data.values()):
            model_plot_color = PlotSettings.modelcolors[model_idx]
            # sorted lead time ranges
            ltr_sorted = sorted(list(data.keys()), key=lambda x: int(x.split("-")[0]))
            x_int = list(range(len(ltr_sorted)))

            # extract header from data & create title
            header = data[ltr_sorted[-1]]["header"]
            unit = header["Unit"][0]
            # get ax, to add plot to
            ax = subplot_axes[idx % 4]
            # ax.set_xlim(x_int[0], x_int[-1])
            y_label = ",".join(score_setup)
            ax.set_ylabel(f"{y_label.upper()} ({unit})")

            if len(score_setup) > 2:
                raise ValueError(
                    f"Maximum two scores are allowed in one plot. Got {len(score_setup)}"
                )
            for score_idx, score in enumerate(score_setup):
                if model_idx == 0:
                    filename += f"{score}_"
                if score == "RANK":
                    print("DATA ", data)
                elif score == "REL_DIA":
                    pass
                else:
                    _set_ylim(param=parameter, score=score_setup[0], ax=ax, debug=debug)
                    y_values = [
                        data[ltr]["df"]["Total"].loc[score] for ltr in ltr_sorted
                    ]
                    ax.plot(
                        x_int,
                        y_values,
                        color=model_plot_color,
                        linestyle=PlotSettings.line_styles[score_idx],
                        marker="D",
                        fillstyle="none",
                        label=f"{score_setup[0].upper()}",
                    )

            # Generate a legend if two scores in one subplot
            if len(score_setup) > 1:
                sub_plot_legend = ax.legend(
                    score_setup,
                    loc="upper right",
                    markerscale=0.9,
                    bbox_to_anchor=(1.35, 1.05),
                )
                # make lines in the legend always black
                for line in sub_plot_legend.get_lines():
                    line.set_color("black")

        # customise grid, title, xticks, legend of current ax
        _customise_ax(
            parameter=parameter,
            scores=score_setup,
            x_ticks=ltr_sorted,
            grid=True,
            ax=ax,
        )

        # save filled figure & re-set necessary for next iteration
        full_figure = idx > 0 and (idx + 1) % 4 == 0
        last_plot = idx == len(plot_scores_setup) - 1
        if full_figure or last_plot:
            _save_figure(output_dir, filename, sup_title, fig, subplot_axes, idx)
            fig, subplot_axes = _initialize_plots(
                models_color_lines, models_data.keys()
            )
            filename = base_filename


def _generate_ensemble_scores_plots(
    plot_scores,
    models_data,
    parameter,
    output_dir,
    debug,
):
    """Generate Ensemble Score Plots."""
    model_plot_colors = PlotSettings.modelcolors
    model_versions = list(models_data.keys())
    custom_lines = [
        Line2D([0], [0], color=model_plot_colors[i], lw=2)
        for i in range(len(model_versions))
    ]

    # initialise filename
    base_filename = (
        f"ensemble_scores_{parameter}_"
        if len(model_versions) == 1
        else f"ensemble_scores_{parameter}_"
    )
    '''
    headers = [
        data[sorted(list(data.keys()), key=lambda x: int(x.split("-")[0]))[-1]][
            "header"
        ]
        for data in models_data.values()
    ]

    total_start_date = min(
        datetime.strptime(header["Start time"][0], "%Y-%m-%d") for header in headers
    )

    total_end_date = max(
        datetime.strptime(header["End time"][0], "%Y-%m-%d") for header in headers
    )

    model_info = (
        ""
        if len(model_versions) > 1
        else f"Model: {headers[0]['Model version'][0]} | \n"
    )
    
    sup_title = (
        model_info
        + f"""Period: {total_start_date.strftime("%Y-%m-%d")} - {total_end_date.strftime("%Y-%m-%d")} | © MeteoSwiss"""
    )
    '''
    sup_title = ""

    _plot_and_save_scores(
        output_dir,
        base_filename,
        parameter,
        plot_scores["regular_ens_scores"],
        sup_title,
        models_data,
        custom_lines,
        debug=False,
    )
