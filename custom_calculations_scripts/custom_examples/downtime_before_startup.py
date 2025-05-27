# In this example, we will put the hours of downtime before a startup as a discrete tag over the startup phase. The
# downtime before startup can be used to categorize the startup itself, as the amount of time the equipment was out of
# operation can have a significant effect on the startup process.
#
# Startups are defined as the periods that fall between downtime and stable operation (both of which are defined as a
# value-based search). The downtime in hours is placed as a discrete tag over the startup which follows that downtime.
# During the downtime itself, our tag will have a value of 0. This way, a search on our downtime duration tag will
# directly yield the startup period.

# Imports
import os
import pandas as pd
from trendminer import TrendMinerClient
from trendminer.sdk.search import ValueBasedSearchOperators

# Initialize client
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",
)

# Set the maximal duration a run or downtime can take
maximal_duration = client.time.timedelta("30d")

# Received index interval
index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# Load tags; add these as dependencies!
tag = client.tag.get_by_name("[CS]BA:LEVEL.1")

# Downtime search definition
search_downtime = client.search.value(
    queries = [
        (tag, ValueBasedSearchOperators.LESS_THAN, 1)
    ],
    duration="2m"
)

# Running search definition
search_running = client.search.value(
    queries = [
        (tag, ValueBasedSearchOperators.GREATER_THAN, 18)
    ],
    duration="5m"
)

# --- CODE EXECUTION ----

# Widen interval
search_interval = client.time.interval(
    index_interval.start - maximal_duration,
    index_interval.end + maximal_duration,
)

# Perform the searches
downtimes = search_downtime.get_results(search_interval)
running = search_running.get_results(search_interval)

# The start of the startup is the end of the downtime
df_downtimes = pd.DataFrame(index=[result.end for result in downtimes])

# We add the duration (in hours)
df_downtimes["value"] = [result.duration.total_seconds()/3600 for result in downtimes]

# The end of the startup is the start of the stable period
df_running = pd.DataFrame(index=[result.start for result in running])

# At which point our tag value should become 0 again
df_running["value"] = 0

# We put all values together, sorted by timestamp
df = (
    pd.concat([df_downtimes, df_running])
    .sort_index()
)

# We want to ignore instances where a downtime does not reach stable operation, but rather is followed by another downtime
# Keep only values of 0 (running) or where the next value is 0 (downtime followed by running), and the timestamp is in the index interval
keep = ((df["value"] == 0) | (df["value"].shift(-1) == 0)) & (index_interval.start <= df.index) & (df.index < index_interval.end)
df = df[keep]

# To file
df.to_csv(os.environ["OUTPUT_FILE"])