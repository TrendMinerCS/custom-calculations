# This example creates an incrementing totalizer of search result durations (in hours). The totalizer resets at regular
# intervals (in this example, every day).

import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.search import ValueBasedSearchOperators

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

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

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
tag_freq = pd.Timedelta("1m")  # resolution of the output tag
for interval in intervals:

    # Start from empty Series for the interval
    interval_ser = pd.Series(
            index=pd.date_range(
                start=interval.start,
                end=interval.end - tag_freq,  # avoid duplicate timestamps
                freq=tag_freq,
                tz=client.tz,
            ),
            data=0.0,  # set as float to avoid warnings
        )

    # Set a value for the times that fall in a search result
    for result in results:
        if (result.start > interval.end) or (result.end < interval.start):
            continue
        interval_ser[
            (result.start <= interval_ser.index) &
            (interval_ser.index <= result.end)
        ] = tag_freq.total_seconds()/3600  # will get duration in hours

    # Get cumulative sum to get increasing duration
    interval_ser = interval_ser.cumsum()
    ser_list.append(interval_ser)

# Concatenate the series
ser = pd.concat(ser_list)

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
