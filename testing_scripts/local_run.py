#!/usr/bin/env python3
"""
Run any TrendMiner custom-calculation script locally and
produce a PNG plot of its CSV output.
"""
import os
import sys
import argparse
from pathlib import Path

from dotenv import load_dotenv
import keycloak
import keyring
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # force non‑GUI backend (safe for threads & Flask)
import matplotlib.pyplot as plt
import runpy
from trendminer.impl._util import DefaultUrlUtils
from datetime import datetime

import logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)

def load_environment(env_file: str) -> None:
    """Load variables from .env without overwriting existing ones."""
    logger.debug("Loading environment from %s", env_file)
    load_dotenv(dotenv_path=env_file, override=False)


def override_from_cli(args: argparse.Namespace) -> None:
    """Override START_TIMESTAMP, END_TIMESTAMP if provided."""
    logger.debug("Override from CLI args: start=%s, end=%s", args.start, args.end)
    if args.start:
        os.environ["START_TIMESTAMP"] = args.start
    if args.end:
        os.environ["END_TIMESTAMP"] = args.end


def fetch_access_token() -> None:
    """Retrieve ACCESS_TOKEN via Keycloak+keyring if not already set."""
    if os.environ.get("ACCESS_TOKEN"):
        logger.debug("ACCESS_TOKEN already set in environment")
        return

    url = os.getenv("SERVER_URL")
    client_id = os.getenv("CLIENT_ID")
    secret = keyring.get_password(url, client_id)

    if not secret:
        logger.error("No ACCESS_TOKEN and no secret in keyring for %s@%s", client_id, url)
        sys.exit(1)

    oid = keycloak.KeycloakOpenID(
        server_url=f"{url}/auth/",
        realm_name="trendminer",
        client_id=client_id,
        client_secret_key=secret,
    )
    token = oid.token(grant_type="client_credentials")["access_token"]
    os.environ["ACCESS_TOKEN"] = token
    DefaultUrlUtils.get_default_url = lambda *_, **__: url
    logger.info("Fetched ACCESS_TOKEN via Keycloak from %s", url)


def run_calculation(script_path: Path) -> None:
    """Execute the user’s calculation script."""
    logger.info("run_calculation started for %s", script_path)
    runpy.run_path(str(script_path), run_name="__main__")
    logger.info("run_calculation finished for %s", script_path)


def plot_csv(csv_path: Path, mode: str = "analog") -> Path:
    """Read CSV and save a PNG plot alongside it."""
    logger.debug("plot_csv called for %s with mode=%s", csv_path, mode)
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True).dropna()

    # Plot timestamps vs. values
    plt.figure()
    if mode == "block":
        plt.step(df.index, df.iloc[:, 0], where="post")
    else:
        plt.plot(df.index, df.iloc[:, 0])
    plt.xlabel("Timestamp")
    plt.ylabel("Value")
    plt.title(csv_path.stem)
    plt.gcf().autofmt_xdate()

    png_path = csv_path.with_suffix(".png")
    logger.debug("Saving plot to %s", png_path)
    plt.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close()
    return png_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a TrendMiner custom-calculation script and plot its output."
    )
    parser.add_argument("script", help="Path to the custom-calculation .py file")
    parser.add_argument("--env-file", default=".env",
                        help="Path to the .env file (default: ./.env)")
    parser.add_argument("--start", help="Override START_TIMESTAMP")
    parser.add_argument("--end",   help="Override END_TIMESTAMP")
    parser.add_argument("--mode",
                        choices=["analog", "block"],
                        default="analog",
                        help="Plot mode: 'analog' (line) or 'block' (step)")
    args = parser.parse_args()

    load_environment(args.env_file)
    override_from_cli(args)
    os.environ["PLOT_MODE"] = args.mode
    fetch_access_token()

    # Ensure required env vars
    needed = ["ACCESS_TOKEN", "START_TIMESTAMP", "END_TIMESTAMP"]
    missing = [k for k in needed if k not in os.environ]
    if missing:
        parser.error(f"Missing environment variables: {', '.join(missing)}")

    script_file = Path(args.script).expanduser().resolve()
    if not script_file.exists():
        parser.error(f"Script not found: {script_file}")

    # Create output subfolder under the repo’s top-level output directory
    script_name = script_file.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(__file__).resolve().parent.parent / "output"
    output_dir = base_output / script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_filename = f"{script_name}_{timestamp}.csv"
    # Override OUTPUT_FILE to point to the new location
    os.environ["OUTPUT_FILE"] = str(output_dir / csv_filename)

    run_calculation(script_file)

    output_csv = Path(os.environ["OUTPUT_FILE"]).expanduser().resolve()
    if output_csv.exists():
        png = plot_csv(output_csv, os.environ.get("PLOT_MODE", "analog"))
        print(f"Plot saved to {png}")
    else:
        print(f"Warning: CSV not found at {output_csv}", file=sys.stderr)

def run_and_plot(script_path: str, start: str, end: str, mode: str):
    """
    Run the custom script with given start/end,
    return the CSV path and the PNG path.
    """
    load_environment(".env")
    os.environ["START_TIMESTAMP"] = start
    os.environ["END_TIMESTAMP"] = end
    os.environ["PLOT_MODE"] = mode
    # Fetch or refresh the TrendMiner access token
    fetch_access_token()

    # Save outputs in a top-level 'output' folder under the repo, one subfolder per script
    script_file = Path(script_path).expanduser().resolve()
    script_name = script_file.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_output = Path(__file__).resolve().parent.parent / "output"
    output_dir = base_output / script_name
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{script_name}_{timestamp}.csv"
    os.environ["OUTPUT_FILE"] = str(csv_path)
    # Log where the CSV will be written
    print(f"Saving CSV to: {csv_path}", flush=True)

    # 3) Run & plot:
    run_calculation(script_file)
    png_path = plot_csv(csv_path, os.environ["PLOT_MODE"])
    return csv_path, png_path


if __name__ == "__main__":
    main()
