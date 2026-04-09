"""General function to load and collect atab files."""

# Standard library
import re
from datetime import datetime
from pathlib import Path

# Local
# pylint: disable=no-name-in-module
from .utils.atab import Atab


# Module-level cache for raw ATAB parse results, keyed by resolved file path.
# This avoids re-reading the same file from disk when multiple pipelines
# (e.g. total_scores and ensemble_scores) need the same underlying data.
_atab_cache: dict = {}


def _load_atab_cached(file_path: Path, sep: str = " "):
    """Return (header, data) for an ATAB file, using cache when possible.

    The raw header dict and a *copy* of the DataFrame are returned so
    that callers can apply their own transforms without mutating the cache.
    """
    key = str(file_path.resolve())
    if key not in _atab_cache:
        loaded_atab = Atab(file=file_path, sep=sep)
        _atab_cache[key] = (loaded_atab.header, loaded_atab.data)
    header, df = _atab_cache[key]
    # Return a copy of the DataFrame so transforms don't mutate the cache
    return header, df.copy()


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
                    # extract header & dataframe (cached to avoid re-parsing)
                    header, df = _load_atab_cached(file_path, sep=" ")
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
