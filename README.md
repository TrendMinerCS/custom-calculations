# Custom Calculations Examples

## Getting Started

Begin by exploring the [Custom Calculations Introduction notebook](custom%20calculations%20introduction.ipynb). It provides a concise overview of:

* Setting up tag dependencies
* Authenticating with the TrendMiner API
* Handling time zones and index intervals
* Retrieving data and performing value based searches
* Defining output formats and exporting results

This notebook is your first entry point into custom calculations.

## Example Scripts

All example scripts live in the `custom calculations scripts` directory. Each script is a standalone Python file demonstrating a common pattern for writing custom calculation tags in TrendMiner.

### Regular Intervals Examples

These examples cover the operations that happen on regular intervals. Daily, weekly, monthly, and yearly intervals can be generated with the `client.time.interval.range` method with `normalize=True`. Note that this approach does not work for hourly intervals, for which you need to write a custom function (returning all full hours that overlap with the index interval). Alternatively, you could opt to perform a value-based search for a built-in hour tag (e.g, TM_hour_Europe_Brussels) being constant.

* [**Block aggregation**](custom%20calculations%20scripts/regular%20intervals%20examples/block_aggregation.py)
  * Apply aggregation functions (e.g., sum, average) on fixed time blocks within the index interval. This can be helpful for creating a tag for roll-up reporting or monitoring purposes.
  ![img.png](images/block_aggregation.png)
* [**Event count**](custom%20calculations%20scripts/regular%20intervals%20examples/event_counter.py)
  * This tag uses a value-based search to see how often the search criteria occur within a regular interval. It only counts the search results that actually start in the interval. This tag type can be used to create monitorable summary statistics on a batch, campaign, or continuous run of equipment whose condition can be defined by a search.
  ![img_1.png](images/event_count.png)
* [**Incrementing counter**](custom%20calculations%20scripts/regular%20intervals%20examples/incrementing_counter.py)
  * Maintain a running count of events across the entire index interval and reset the counter after a defined period.
  ![img.png](images/incrementing_counter.png)
* [**Incrementing totalizer**](custom%20calculations%20scripts/regular%20intervals%20examples/incrementing_totalizer.py)
  * Compute a cumulative sum of tag values over time, integrating continuously across blocks and reset the totalizer after a defined period.
  ![img.png](images/incrementing_totalizer.png)

### Search Results Examples

These examples cover the operations that happen on search results. A search is first performed, and the results of the custom calculation are then plotted at the times of the search results.

In these templates, as an example we will simply search for the day being a Monday, Wednesday or Friday.

* [**Block aggregations using calculations on search results**](custom%20calculations%20scripts/search%20results%20examples/block_aggregations_calc_search_results.py)
  * Per search result, perform a custom calculation based on aggregations saved with the search. This allows you to delve deeper into the evolution of search aggregate calculations and well as perform custom calculations (ex. KPIs or empirical formulae) on them.
  * ![img.png](images/block_aggregations_calc_search_results.png)

* [**Event count on search results**](custom%20calculations%20scripts/search%20results%20examples/event_counter_for_search_results.py)
  * Per search result, count the number of results of a second search that start within it.This algorithm can be applicable to counting events within a particular timeframe (such as tank filling periods during a campaign or equipment defouling within a particular maintenance interval) or that a particular step occurs within a batch.
  * ![img.png](images/event_counter_for_search_results.png)
  
* [**Incrementing event counter**](custom%20calculations%20scripts/search%20results%20examples/incrementing_event_counter_search_results.py)
  * Per main search result, have an incrementing counter for the results of a secondary search. This is similar to the last example’s application, but instead one single total count value, the counter starts at 0 and increments with 1 for every new result, resetting to 0 after the main search result concludes. This shows exactly when secondary results occured, and allows for more up to date indexing of the value rather than needing both search periods to conclude before calculating and indexing a value.
![img.png](images/incrementing_event_counter_search_results.png)
* [**Incrementing value totalizer**](custom%20calculations%20scripts/search%20results%20examples/incrementing_value_totalizer_search_results.py)
  * Totalize a given tag over the course of a search result. Typically, we do not want to wait until search results are completed, or add a minimal duration to the search, as that would delay the totalizer. This tag type shows the evolution of the same event summary variables that can be obtained by calculations on search results, allowing for monitoring and proactive response to deviation from expected values.
![img.png](images/incrementing_value_totalizer_search_results.png)

---

Feel free to copy or adapt any of these scripts for your own custom calculations in TrendMiner and if you have any questions you can always reach us on the TrendMiner [community](https://community.trendminer.com)!

---

## DEV

### Command-Line Interface

Run any custom calculation script and generate a time-series plot:

```bash
python local_run.py path/to/your_script.py \
    --env-file .env \
    --start 2025-05-01T00:00:00Z \
    --end   2025-05-07T00:00:00Z \
    --mode  analog
```

- `--env-file`: path to your `.env` file with TrendMiner credentials.  
- `--start` and `--end`: ISO timestamps for the time range.  
- `--mode`: `analog` (line plot) or `block` (step plot).  
- Outputs: a timestamped subfolder named after your script, containing a CSV and PNG.

### Web Frontend

Start the Flask app to run and visualize calculations in your browser:

1. Move into the project root and run:
   ```bash
   export FLASK_APP=app.py
   flask run
   ```
2. Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.
3. Make sure your script is in the custom calculations folder
3. Select a script, pick start/end timestamps, choose mode, and click **Run & Plot**.  
4. The interactive chart appears below the form.

Environment variables for the web (e.g., `SERVER_URL`, `CLIENT_ID`) should be set in your `.env` as for the CLI.


git checkout -p dev -- "custom calculations introduction.ipynb"