import os
import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.integrate import cumulative_trapezoid
from trendminer import TrendMinerClient
from trendminer.sdk.search import ValueBasedSearchOperators

# ---- PARAMETERS -----

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)

# default value to return to between results
default_value = 0

# tag definition; add these as dependencies!
tag1 = client.tag.get_by_name("TM_day_Europe_Brussels")

tag_to_totalize = client.tag.get_by_name("[CS]BA:CONC.1")

# Time unit the tag is expressed in; required to get correct totalizer values
time_unit = client.time.timedelta("1h")  # here expressed in 'per hour'

# Base search definition
search = client.search.value(
    queries=[
        (tag1, ValueBasedSearchOperators.IN_SET, ["Monday", "Wednesday", "Friday"])
    ],
    duration="2m",
)

# maximal search result duration
maximal_duration = client.time.timedelta("25h")

# ---- CODE EXECUTION -----

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# Widen interval
search_interval = client.time.interval(
    index_interval.start - maximal_duration,
    index_interval.end + maximal_duration,
)

# Get search results
intervals = search.get_results(search_interval)

# Generate a dataframe per interval
ser_list = []
for interval in intervals:
    tag_data = tag_to_totalize.get_data(interval, resolution="1m")
    if len(tag_data) <= 1:
        continue
    relative_index = tag_data.index - tag_data.index[0]
    x_coordinate = relative_index.total_seconds() / time_unit.total_seconds()
    total_values = cumulative_trapezoid(y=tag_data, x=x_coordinate)
    total_values = np.insert(total_values, 0, 0)  # start values at 0

    # Add 1ms to avoid duplicate timestamps
    totals = pd.Series(
        index=[tag_data.index[0] + timedelta(seconds=0.001)] + tag_data.index[1:].tolist(),
        data=total_values,
    )

    # Return to default value in between search results; only for completed results
    if (default_value is not None) and (interval.end < index_interval.end):
        totals = pd.concat(
            [
                totals,
                pd.Series(index=[interval.end + timedelta(seconds=0.001)], data=[default_value])
            ]
        )

    ser_list.append(totals)

# Concatenate the series
ser = pd.concat(ser_list)
ser.name = "value"

# Filter for timestamps and NaN values
ser = (
    ser
    .loc[lambda x: x.index >= index_interval.start]
    .loc[lambda x: x.index < index_interval.end]
    .dropna()
)

# To file
ser.to_csv(
    os.environ["OUTPUT_FILE"]
)