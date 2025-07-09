import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.tag import TagCalculationOptions
from trendminer.sdk.search import ValueBasedSearchOperators

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
tag1 = client.tag.get_by_name("[CS]BA:ACTIVE.1")
tags = [tag1]

# event search definition
search_duration = client.time.timedelta("2m")
event_search = client.search.value(
    queries=[
        (tag1, ValueBasedSearchOperators.IN_SET, ["Active"])
    ],
    duration=search_duration,
)

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

# Get regular intervals. In this case we also have to look backwards.
intervals = client.time.interval.range(
    freq=freq,
    start=index_interval.start - maximal_duration,
    end=index_interval.end + maximal_duration,
    normalize=True,
)

# Get search results
search_interval = client.time.interval(
    index_interval.start - maximal_duration,
    index_interval.end + maximal_duration,
)

results = event_search.get_results(search_interval)

# Generate a dataframe per interval
ser_list = []
for interval in intervals:

    interval_results = [
        result for result in results
        if (interval.start <= result.start)
           and (result.start < interval.end)
    ]

    interval_ser = pd.Series(
        index=[result.start for result in interval_results],
        data=1,
    ).cumsum()

    # start at 0 unless first result starts at interval start
    if (len(interval_results) == 0) or (interval_results[0].start != interval.start):
        interval_ser = pd.concat(
            [
                pd.Series(
                    index=[interval.start],
                    data=[0],
                ),
                interval_ser,
            ]
        )

    ser_list.append(interval_ser)

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
