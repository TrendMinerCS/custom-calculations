## Usage

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