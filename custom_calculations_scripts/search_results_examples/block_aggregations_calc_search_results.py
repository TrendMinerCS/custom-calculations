import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.tag import TagCalculationOptions
from trendminer.sdk.search import ValueBasedSearchOperators, SearchCalculationOptions

# ---- PARAMETERS -----

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",  # <--- SET TIMEZONE
)

# default value to return to between results
default_value = 0

# tag definition; add these as dependencies!
tag1 = client.tag.get_by_name("[CS]BA:CONC.1")
tag2 = client.tag.get_by_name("[CS]BA:LEVEL.1")
tag3 = client.tag.get_by_name("TM_day_Europe_Brussels")

# search definition
search = client.search.value(
    queries=[
        (tag3, ValueBasedSearchOperators.IN_SET, ["Monday", "Wednesday", "Friday"])
    ],
    duration="23h",
    calculations={
        "calc1": (tag1, SearchCalculationOptions.MAXIMUM),
        # MEAN, MINIMUM, MAXIMUM, RANGE, START, END, DELTA, INTEGRAL, STDEV
        "calc2": (tag2, SearchCalculationOptions.MAXIMUM),
    }
)

# maximal search result duration
maximal_duration = client.time.timedelta("25h")


# additional custom operation on search calculations
def calculate(intervals):
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

# Widen interval
search_interval = client.time.interval(
    index_interval.start - maximal_duration,
    index_interval.end + maximal_duration,
)

# Get results
intervals = search.get_results(search_interval)

# Remove open-ended result
if (len(intervals) > 0) and ((search_interval.end - intervals[-1].end) < client.resolution):
    intervals.pop(-1)

# Perform the calculation
calculate(intervals)

# Put the results in a Series
ser = pd.Series(
    name="value",
    index=[
        timestamp for interval in intervals
        for timestamp in (interval.start, interval.end)
    ],
    data=[
        value for interval in intervals
        for value in (interval["result"], default_value)
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