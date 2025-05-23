import os
import pandas as pd
import functools
import requests
import keyring
from dotenv import load_dotenv
from pathlib import Path
from trendminer.impl._util import DefaultUrlUtils


def env_init(start, end):
    start = pd.Timestamp(start, tz="utc")
    end = pd.Timestamp(end, tz="utc")

    def decorator(test_function):

        @functools.wraps(test_function)
        def wrapper(*args, **kwargs):

            # Set authentication
            dotenv_path = Path(__file__).resolve().parent / "../testing_scripts/.env"
            load_dotenv(dotenv_path=dotenv_path.resolve(), override=False)
            url = os.environ["SERVER_URL"]
            client_id = os.environ["CLIENT_ID"]

            response = requests.post(
                url=f"{url}/auth/realms/trendminer/protocol/openid-connect/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": keyring.get_password(url, client_id),
                },
            )

            # url getter needs to be overwritten for local runs
            DefaultUrlUtils.get_default_url = lambda *_, **__: url

            # Initialize environment
            os.environ["ACCESS_TOKEN"] = response.json()["access_token"]
            os.environ["START_TIMESTAMP"] = start.isoformat()
            os.environ["END_TIMESTAMP"] = end.isoformat()
            os.environ["OUTPUT_FILE"] = "_temp_test_output.csv"

            # Run function
            result = test_function(*args, **kwargs)

            # Read output file into memory and remove
            df = pd.read_csv(os.environ["OUTPUT_FILE"], index_col=0)
            os.remove(os.environ["OUTPUT_FILE"])

            # Test output
            df.index = pd.to_datetime(df.index, format="ISO8601")
            if df.empty:
                raise ValueError("Script yielded no output")
            if df.index[0] < start:
                raise ValueError("Script yielded timestamps before index interval")
            if df.index[-1] > end:
                raise ValueError("Script yielded timestamps after index interval")

            # Return result (though should be None)
            return result

        return wrapper

    return decorator