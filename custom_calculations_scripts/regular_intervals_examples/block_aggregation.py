import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.tag import TagCalculationOptions

# ---- PARAMETERS -----

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)

# Frequency selection
# https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases
# Daily: D | Weekly starting Monday: W-MON | Monthly: MS | Yearly: YS
freq = "D"
maximal_duration = client.time.timedelta("25h")  # the maximal possible duration of one interval

# tag definition
tag1 = client.tag.get_by_name("[CS]BA:CONC.1")
tag2 = client.tag.get_by_name("[CS]BA:LEVEL.1")
tags = [tag1, tag2]


# calculation definition
def calculate(intervals):
    # Aggregations
    tag1.calculate(
        intervals=intervals,
        operation=TagCalculationOptions.MAXIMUM,  # MEAN, MINIMUM, MAXIMUM, RANGE, START, END, DELTA, INTEGRAL, STDEV
        key="calc1",
        inplace=True,
    )

    tag2.calculate(
        intervals=intervals,
        operation=TagCalculationOptions.MAXIMUM,
        key="calc2",
        inplace=True,
    )

    # Custom operations
    for interval in intervals:
        # Account for potential missing calculations
        try:
            interval["result"] = interval["calc1"] * interval["calc2"]
        except (TypeError, KeyError):
            interval["result"] = None


# ---- CODE EXECUTION -----

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# Determine the last point up to which we can perform calculations (all tags indexed)
check_interval = client.time.interval(
    index_interval.start,
    client.time.now(),
)

try:
    last_timestamp = min([
        tag.get_plot_data(check_interval, n_intervals=2).index[-1]
        for tag in tags
        ])
except IndexError:
    last_timestamp = index_interval.start

# Get intervals
intervals = client.time.interval.range(
    freq=freq,
    start=index_interval.start,
    end=min([
        index_interval.end + maximal_duration,
        last_timestamp,
    ]),
    normalize=True,
)

# Perform the calculation
calculate(intervals)

# Put the results in a Series
ser = pd.Series(
    index=[
        interval.start for interval in intervals
    ],
    data=[
        interval["result"] for interval in intervals
    ],
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