"""General functions to create plots."""

# Standard library
from datetime import datetime


def get_total_dates_from_headers(headers: list):
    total_start_date = min(
        datetime.strptime(header["Start time"][0], "%Y-%m-%d") for header in headers
    )

    total_end_date = max(
        datetime.strptime(header["End time"][0], "%Y-%m-%d") for header in headers
    )
    return total_start_date, total_end_date
