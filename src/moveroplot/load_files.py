"""General function to load and collect atab files."""

# Standard library
import re
from datetime import datetime
from pathlib import Path

# Local
# pylint: disable=no-name-in-module
from .utils.atab import Atab


# pylint: disable=too-many-arguments,too-many-locals
def is_valid_data(header):
    try:
        # %z not supported in datetime of Python 3.11
        datetime.strptime(" ".join(header["Start time"][0:2]), "%Y-%m-%d %H:%M")
        datetime.strptime(" ".join(header["End time"][0:2]), "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def load_relevant_files(
    input_dir,
    file_prefix,
    file_postfix,
    debug,
    model_plots,
    parameter,
    lt_ranges,
    ltr_first=True,
    transform_func=None,
):
    corresponding_files_dict = {}
    files_list = []
    for model in model_plots:
        source_path = Path(f"{input_dir}/{model}")
        for file_path in source_path.glob(f"{file_prefix}*{parameter}{file_postfix}"):
            if file_path.is_file():
                ltr_match = re.search(r"(\d{2,3})(-\d{2,3})*", file_path.name)
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
                    loaded_atab = Atab(file=file_path, sep=" ")
                    header = loaded_atab.header
                    df = loaded_atab.data
                    if transform_func:
                        df = transform_func(df, header)
                    if is_valid_data(header):
                        # add information to dict
                        first_key, second_key = (
                            (lt_range, model) if ltr_first else (model, lt_range)
                        )
                        corresponding_files_dict.setdefault(first_key, {})[
                            second_key
                        ] = {
                            "header": header,
                            "df": df,
                        }

                        # add path of file to list of relevant files
                        files_list.append(file_path)

    if debug:
        print(f"\nFor parameter: {parameter} these files are relevant:\n")
        print("Found files: ", files_list)

    return corresponding_files_dict
