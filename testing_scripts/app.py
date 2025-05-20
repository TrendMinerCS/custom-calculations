from http.cookiejar import debug
from venv import logger

from flask import Flask, render_template, request, flash
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, timedelta
from local_run import run_and_plot
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Tell Flask where to find templates and static files in the frontend folder
app = Flask(
    __name__,
    template_folder=str(Path(__file__).resolve().parent / "frontend" / "templates"),
    static_folder=str(Path(__file__).resolve().parent / "frontend" / "static")
)

app.secret_key = os.urandom(24)

@app.route("/", methods=["GET", "POST"])
def index():
    # Point to the dedicated scripts folder instead of current working directory
    scripts_dir = Path(__file__).resolve().parent.parent / "custom calculations scripts"
    scripts = [
        str(p.relative_to(scripts_dir))
        for p in scripts_dir.glob("**/*.py")
        if p.name not in ("app.py", "local_run.py")
    ]

    if request.method == "POST":
        start  = request.form.get("start", "").strip()
        end    = request.form.get("end", "").strip()
        mode   = request.form.get("mode", "analog")

        # User-selected script path
        script = request.form.get("script", "").strip()
        script_path = scripts_dir / script
        if not (script and script_path.exists()):
            flash("Please select a valid script", "danger")
            return render_template("index.html",
                                   scripts=scripts, script=script,
                                   start=start, end=end, mode=mode,
                                   timestamps=[], values=[])

        if not (script and start and end):
            flash("All fields are required", "danger")
            return render_template("index.html",
                                   scripts=scripts, script=script,
                                   start=start, end=end, mode=mode,
                                   timestamps=[], values=[])

        logger.info("Received POST for script=%s start=%s end=%s mode=%s", script, start, end, mode)
        try:
            logger.info("Calling run_and_plot for %s", script_path)
            csv_path, _ = run_and_plot(str(script_path), start, end, mode)
            logger.info("run_and_plot returned CSV path %s", csv_path)
            # Read CSV (index remains string), then convert index to datetime handling mixed formats
            df = pd.read_csv(csv_path, index_col=0).dropna()
            df.index = pd.to_datetime(df.index, format='mixed')
            logger.debug("DataFrame head after datetime conversion:\n%s", df.head())
            timestamps = df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
            values     = df.iloc[:, 0].tolist()
            return render_template("index.html",
                                   scripts=scripts, script=script,
                                   start=start, end=end, mode=mode,
                                   timestamps=timestamps, values=values)
        except Exception as e:
            logger.exception("Error during run_and_plot")
            flash(f"Error: {e}", "danger")
            return render_template("index.html",
                                   scripts=scripts, script=script,
                                   start=start, end=end, mode=mode,
                                   timestamps=[], values=[])

    # GET - set defaults: 7 days ago to now
    start_default = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
    end_default   = datetime.now().strftime("%Y-%m-%dT%H:%M")
    return render_template("index.html",
                           scripts=scripts, script="",
                           start=start_default, end=end_default, mode="analog",
                           timestamps=[], values=[])


if __name__ == "__main__":
    app.run()