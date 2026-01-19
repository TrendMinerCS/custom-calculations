import os
import pandas as pd
import numpy as np
from scipy.integrate import cumulative_trapezoid
from trendminer import TrendMinerClient
from trendminer.sdk.tag import TagCalculationOptions

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)


# tag definition; this is the tag we will integrate
tag = client.tag.get_by_name("[CS]BA:CONC.1")  # <-- replace with your kW tag name

# To get a correct integrated value, we need to know about the time unit of the tag.
time_unit = client.time.timedelta("1h")

# The start time from which we start integrating
start_time = client.time.datetime("2025-01-01 00:00:00")

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# If the index interval is completely before the start_time, return zeros
if index_interval.end <= start_time:
    ser = pd.Series(
        index=[index_interval.start, index_interval.end],
        data=[0, 0],
    )

else:

    # Special consideration for the start value falling in the index interval
    if index_interval.start >= start_time:
        aggregation_interval = client.time.interval(
            start_time,
            index_interval.start,
        )

        aggregation_correction = client.time.timedelta("24h")/time_unit
        start_value = tag.calculate(
            intervals=[aggregation_interval],
            operation=TagCalculationOptions.INTEGRAL,
            key="total",
        )[0]["total"]*aggregation_correction

        data_interval = index_interval
    else:
        data_interval = client.time.interval(
            start_time,
            index_interval.end,
        )
        start_value = 0

    resolution = client.time.timedelta("1m")
    trapezoid_correction = resolution/time_unit
    tag_data = tag.get_data(data_interval, resolution=resolution)
    if tag_data.empty:
        quit()
    data = np.insert(cumulative_trapezoid(y=tag_data), 0, 0)*trapezoid_correction + start_value
    ser = pd.Series(
        index=tag_data.index,
        data=data,
    )

# Filter for timestamps and NaN values
ser = (
    ser
    .loc[lambda x: x.index >= index_interval.start]
    .loc[lambda x: x.index < index_interval.end]
    .dropna()
)

# To file
if not ser.empty:
    ser.to_csv(
        os.environ["OUTPUT_FILE"]
    )