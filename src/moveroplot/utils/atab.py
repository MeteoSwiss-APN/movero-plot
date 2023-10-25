"""Atab file support."""
# Standard library
from typing import Any
from typing import Dict
from typing import Optional

# Third-party
import pandas as pd


class Atab:

    """Support atab files.
    Attributes:
        header: Header information of the atab file.
        data: Data part of the atab file.
    """

    def __init__(self, file, sep: str = ";") -> None:
        """Create an instance of ``Atab``.
        Args:
            file: Input file.
            sep (optional): Separator for data.
        """
        # Check consistency
        supported_seps = [
            " ",
            ";",
        ]
        # TODO: perhaps add r"\s+" to support multiple spaces.
        # There was a problem w/ parsing the header for
        # the station scores files. (lon, lat rows)
        if sep not in supported_seps:
            raise RuntimeError(
                f"Separator {sep} not supported. Must be one of "
                + ",".join(map("'{}'".format, supported_seps))  # noqa: W503
            )

        # Set instance variables
        self.file = file
        self.sep = sep
        self.n_header_lines = 0
        self.header: Dict[str, Any] = {}

        # parse file content
        self.data: Optional[pd.DataFrame] = None
        self._parse()

    def _parse(self) -> None:
        """Parse the atab file.
        Parse the header first, then the remaining data block using
        ``pandas.read_csv``.
        """
        # Parse the header information
        self._parse_header()

        # Parse the data section
        args: Dict[str, Any] = {"skiprows": self.n_header_lines, "parse_dates": True}
        if self.sep == " ":
            args["delim_whitespace"] = True
        else:
            args["sep"] = self.sep
        self.data = pd.read_csv(self.file, **args)

        # Add experiment number as new column if available in header
        experiment = self.header.get("Experiment", None)
        if experiment is not None:
            n_rows = len(self.data.index)
            string_array = [experiment[0] for _ in range(n_rows)]
            self.data["Experiment"] = pd.Series(string_array, index=self.data.index)

        # Add product type as new column if available in header
        product_type = self.header.get("Type_of_product", None)
        if product_type is not None:
            n_rows = len(self.data.index)
            string_array = [product_type[0] for _ in range(n_rows)]
            self.data["Product_Type"] = pd.Series(string_array, index=self.data.index)

        # Remove columns with all NaN
        self.data = self.data.dropna(axis=1, how="all")

    def _parse_header(self):
        """Parse the header of the atab file."""
        with open(self.file, "r") as f:
            lines = f.readlines()

        idx = 0
        while len(lines) > 0:
            line = lines.pop(0)
            elements = line.strip().split(
                ":", maxsplit=1
            )  # ADDED maxsplit, so i.e. timestamp doesn't get split into separate parts  # noqa: E501
            # Treat first line separately
            if idx == 0:
                # Extract format from header (ATAB odr XLS_TABLE)
                self.header["Format"] = elements[0].strip(self.sep)
                line = lines.pop(0)
                elements = line.strip().split(":", maxsplit=1)
                key = elements[0]
                self.header[key] = "".join(elements[1:]).strip(self.sep).split(self.sep)

                idx += 1
                continue

            # Stop extraction of header information if line contains no ":"
            if len(elements) == 1:
                self.n_header_lines = idx + 1
                break

            # Store header information
            key = elements[0]
            self.header[key] = "".join(elements[1:]).strip(self.sep).split(self.sep)
            idx += 1

        # # Check if all mandatory keys are in the header
        # # Extract header of the atab file and generate dictionary
        # mandatory_keys=[
        #    "Width_of_text_label_column",
        #    "Number_of_integer_label_columns",
        #    "Number_of_real_label_columns",
        #    "Number_of_data_columns",
        #    "Number_of_data_rows",
        #    ]
        # key_set = set(list(self.header.keys()))
        # print(self.header)
        # mandatory_key_set = set(mandatory_keys)
        # diff_set = mandatory_key_set - key_set
        # if diff_set:
        #     raise RuntimeError(
        #         f"Missing mandatory key(s) in header of {self.file}: {repr(diff_set)}"
        #     )
