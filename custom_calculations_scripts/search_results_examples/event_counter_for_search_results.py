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

# default value to return to between results
default_value = 0

# tag definition; add these as dependencies!
tag1 = client.tag.get_by_name("TM_day_Europe_Brussels")
tag2 = client.tag.get_by_name("[CS]BA:ACTIVE.1")


# Base search definition
search = client.search.value(
    queries=[
        (tag1, ValueBasedSearchOperators.IN_SET, ["Monday", "Wednesday", "Friday"])
    ],
    duration="23h",
)

# event search definition
event_search_duration = client.time.timedelta("2m")
event_search = client.search.value(
    queries=[
        (tag2, ValueBasedSearchOperators.IN_SET, ["Active"])
    ],
    duration=event_search_duration,
)

# maximal search result duration over both searches
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

# Get base search results
intervals = search.get_results(search_interval)

# Remove open-ended result
if (len(intervals) > 0) and ((search_interval.end - intervals[-1].end) < client.resolution):
    intervals.pop(-1)

# Get event restults
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
    name="value",
    index=[
        timestamp for interval in intervals
        for timestamp in (interval.start, interval.end)
    ],
    data=[
        value for interval in intervals
        for value in (interval["count"], default_value)
    ],
)

ser.index.name = "ts"

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