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

last_timestamp = min([
    tag.get_plot_data(check_interval, n_intervals=1).index[-1]
    for tag in tags
])

# Get regular intervals
intervals = client.time.interval.range(
    freq=freq,
    start=index_interval.start,
    end=min([
        index_interval.end + maximal_duration,
        last_timestamp - search_duration,
    ]),
    normalize=True,
)

# Get search results
search_interval = client.time.interval(
    index_interval.start - client.resolution,
    index_interval.end + maximal_duration,
)

results = event_search.get_results(search_interval)

# Count number of results that start in each regular interval
for interval in intervals:
    interval["count"] = sum([
        1 for result in results
        if (interval.start <= result.start)
           and (result.start < interval.end)
    ])

# Put the results in a Series
ser = pd.Series(
    index=[
        interval.start for interval in intervals
    ],
    data=[
        interval["count"] for interval in intervals
    ],
)

# Filter for timestamps and NaN values
ser = (
    ser
    .loc[lambda x: x.index > index_interval.start]
    .loc[lambda x: x.index <= index_interval.end]
    .dropna()
)

# To file
if not ser.empty:
    ser.to_csv(
        os.environ["OUTPUT_FILE"]
    )
