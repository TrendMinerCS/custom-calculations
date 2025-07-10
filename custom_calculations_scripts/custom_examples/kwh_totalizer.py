import os
import pandas as pd
import numpy as np
from datetime import timedelta
from scipy.integrate import cumulative_trapezoid
from trendminer import TrendMinerClient
from trendminer.sdk.tag import TagCalculationOptions
from trendminer.sdk.search import ValueBasedSearchOperators

# ---- PARAMETERS -----

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)

# Frequency selection for the totalizer reset interval
# Change 'freq' to set the duration of the totalizer:
#   - Daily:    freq = "D"
#   - Weekly:   freq = "W-MON"  (week starts on Monday)
#   - Monthly:  freq = "MS"
#   - Yearly:   freq = "YS"
# See: https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases
freq = "D"  # <-- Change this value for different totalizer durations

# Set maximal_duration to the maximum possible length of one interval
# For daily:   "25h" (covers a full day plus a margin)
# For weekly:  "8d"  (covers a full week plus a margin)
# For monthly: "32d" (covers a full month plus a margin)
# Adjust as needed for your chosen freq
maximal_duration = client.time.timedelta("25h")  # <-- Change this for different durations

# tag definition; this is the tag we will integrate (in kW)
tag_to_totalize = client.tag.get_by_name("[CS]BA:CONC.1")  # <-- replace with your kW tag name

# Time unit for kWh: 1 hour
# Since the tag is in kW, integrating over hours gives kWh
# 1 hour = 3600 seconds
kwh_time_unit = client.time.timedelta("1h")

# ---- CODE EXECUTION -----

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# Get regular intervals. In this case we also have to look backwards.
intervals = client.time.interval.range(
    freq=freq,  # <-- This determines the reset interval for the totalizer
    start=index_interval.start - maximal_duration,
    end=index_interval.end + maximal_duration,
    normalize=True,
)

# Generate a dataframe per interval
ser_list = []
for interval in intervals:
    tag_data = tag_to_totalize.get_data(interval, resolution="1m")
    if len(tag_data) <= 1:
        continue
    relative_index = tag_data.index - tag_data.index[0]
    x_coordinate = relative_index.total_seconds() / kwh_time_unit.total_seconds()
    # Integrate kW over hours to get kWh
    total_values = cumulative_trapezoid(y=tag_data, x=x_coordinate)
    total_values = np.insert(total_values, 0, 0)  # start values at 0

    # Add 1ms to avoid duplicate timestamps
    totals = pd.Series(
        index=[tag_data.index[0] + timedelta(seconds=0.001)] + tag_data.index[1:].tolist(),
        data=total_values,
    )
    ser_list.append(totals)

# Concatenate the series
ser = pd.concat(ser_list)
ser.name = "value"

# Filter for timestamps and NaN values
ser = (
    ser
    .loc[lambda x: x.index > index_interval.start]
    .loc[lambda x: x.index <= index_interval.end]
    .dropna()
)

# To file
ser.to_csv(
    os.environ["OUTPUT_FILE"]
)
