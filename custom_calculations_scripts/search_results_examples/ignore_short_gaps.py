# Put a value of 1 when a value-based search is True, but ignore gaps between results which are shorter than a given threshold
import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.search import ValueBasedSearchOperators


# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)

# tag definition; add these as dependencies!
tag1 = client.tag.get_by_name("TM5-HEX-PI06201")

# Maximal size of the gap between results which should be ignored
max_ignored_gap = pd.Timedelta(minutes=5)

# Estimated maximal duration of a search result to make sure we get complete results
maximal_duration = pd.Timedelta(days=1)

# search definition
search_duration = pd.Timedelta(minutes=5)
search = client.search.value(
    queries=[
        (tag1, ValueBasedSearchOperators.GREATER_THAN, 5)
    ],
    duration=search_duration,
)


# ---- CODE EXECUTION -----

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# Widen interval. Accounting for gap size and maximal search result duration
search_interval = client.time.interval(
    index_interval.start - max_ignored_gap - maximal_duration,
    index_interval.end + max_ignored_gap + maximal_duration,
)

# Get results
intervals = search.get_results(search_interval)

# Remove open-ended result
if (len(intervals) > 0) and ((search_interval.end - intervals[-1].end) < client.resolution):
    intervals.pop(-1)

# Put the results in a Series; 1 on result start, 0 on result end
ser = pd.Series(
    name="value",
    index=[
        timestamp for interval in intervals
        for timestamp in (interval.start, interval.end)
    ],
    data=[
        value for _ in intervals
        for value in (1, 0)
    ],
)

# Filter out the short gaps
is_short_gap = (
    (ser == 0)  # end of search result
    & (-ser.index.diff(-1) <= max_ignored_gap)  # and short time to next search result
)

# Remove the short gaps
ser = ser[~is_short_gap]

# Filter for timestamps
ser = (
    ser
    .loc[lambda x: x.index > index_interval.start]
    .loc[lambda x: x.index <= index_interval.end]
)

# To file
if not ser.empty:
    ser.to_csv(
        os.environ["OUTPUT_FILE"]
    )
