from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
import os
import tempfile
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime, timedelta

# Ensure the project root is on the Python module search path
import sys
import os
# Ensure the project root (one level up) is on the Python module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# import the helper you just added:
from local_run import run_and_plot

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route("/", methods=["GET", "POST"])
def index():
    # Discover available Python scripts on server
    scripts_dir = Path.cwd()
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

        try:
            csv_path, _ = run_and_plot(script, start, end, mode)
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True).dropna()
            timestamps = df.index.strftime('%Y-%m-%d %H:%M:%S').tolist()
            values     = df.iloc[:, 0].tolist()
            return render_template("index.html",
                                   scripts=scripts, script=script,
                                   start=start, end=end, mode=mode,
                                   timestamps=timestamps, values=values)
        except Exception as e:
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
    app.run(debug=True)