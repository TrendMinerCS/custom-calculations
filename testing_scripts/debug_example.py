# Example for running custom calculations locally, giving the option to debug code
import os
import keyring
import requests
import pandas as pd
from trendminer.impl._util import DefaultUrlUtils


# 1. SET AUTHENTICATION
# you could opt to get this data from your .env file too
url = "https://cs.trendminer.net"
client_id = "wdanielsclient"

response = requests.post(
    url=f"{url}/auth/realms/trendminer/protocol/openid-connect/token",
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": keyring.get_password(url, client_id),
        },
)

os.environ["ACCESS_TOKEN"] = response.json()["access_token"]
DefaultUrlUtils.get_default_url = lambda *_, **__: url  # url getter needs to be overwritten for local runs

# 2. SET INDEX INTERVAL
os.environ["START_TIMESTAMP"] = pd.Timestamp(year=2024, month=3, day=19).isoformat()
os.environ["END_TIMESTAMP"] = pd.Timestamp(year=2024, month=6, day=19).isoformat()
os.environ["OUTPUT_FILE"] = "_local_run.csv" # temporary file

# 3. RUN A CUSTOM CALCULATION BY IMPORTING THE FILE
from custom_calculations_scripts.coolprop_examples import heat_exchanger_energy_flow

# 4. PERFORM ACTIONS/TESTS ON THE OUTPUT FILE
df = pd.read_csv(os.environ["OUTPUT_FILE"])
print(df)

# 5. CLEAN UP THE OUTPUT FILE
os.remove(os.environ["OUTPUT_FILE"])
