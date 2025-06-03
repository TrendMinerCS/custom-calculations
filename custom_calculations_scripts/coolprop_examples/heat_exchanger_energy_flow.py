#%%
import os
from time import tzname

import pandas as pd
from CoolProp.CoolProp import PropsSI
from trendminer import TrendMinerClient

# ——————————————————————————————————————————
# 1. Init client & index interval
# ——————————————————————————————————————————
client = TrendMinerClient.from_token(
    token=os.environ["ACCESS_TOKEN"],
    tz="Europe/Brussels",
)

index_interval = client.time.interval(
    os.environ["START_TIMESTAMP"],
    os.environ["END_TIMESTAMP"],
)

# ——————————————————————————————————————————
# 2. Grab your tags (replace with your real IDs)
# ——————————————————————————————————————————
T_tag    = client.tag.get_by_name("TM5-HEX-TI0620")   # process temperature (°C)
P_tag    = client.tag.get_by_name("TM5-HEX-PI06201")  # inlet pressure (bar)
rho_tag  = client.tag.get_by_name("TM5-HEX-QI0620")   # fluid density (kg/m³)
flow_tag = client.tag.get_by_name("TM5-HEX-FI0620")   # volumetric flow (m³/s)

# ——————————————————————————————————————————
# 3. Fetch raw data at 1 min resolution
# ——————————————————————————————————————————
ser_T    = T_tag   .get_data(index_interval, resolution="1m")
ser_P    = P_tag   .get_data(index_interval, resolution="1m")
ser_rho  = rho_tag .get_data(index_interval, resolution="1m")
ser_flow = flow_tag.get_data(index_interval, resolution="1m")

# ——————————————————————————————————————————
# 4. Align into one DataFrame & drop missing points
# ——————————————————————————————————————————
df = pd.concat([ser_T, ser_P, ser_rho, ser_flow], axis=1, join="outer")
df.columns = ["T","P","rho","vol_flow"]
df = df.dropna()

# ——————————————————————————————————————————
# 5. Compute specific enthalpy & energy flow (fixed)
# ——————————————————————————————————————————
#   - T °C→K; P bar→Pa; PropsSI returns J/kg so divide by 1e3 → kJ/kg

# Pre-compute arrays for speed/readability
temps_K  = df["T"] + 273.15
press_Pa = df["P"] * 1e5
# print(temps_K)
# Compute specific enthalpy [kJ/kg] at each point
enthalpies = [
    PropsSI('H', 'T', T, 'P', P, 'IF97::Water') / 1e3
    for T, P in zip(temps_K, press_Pa)
]
# print(enthalpies)
df["h_kJkg"] = enthalpies

# Compute mass flow [kg/s] = density [kg/m³] * volumetric flow [m³/s]
df["m_dot"] = df["rho"] * df["vol_flow"]

# Instantaneous heat duty [kW] = ṁ [kg/s] * h [kJ/kg]
df["value"] = df["m_dot"] * df["h_kJkg"]
# Drop all other columns, keep only the result
df = df[["value"]]

# ——————————————————————————————————————————
# 6. Final filtering and CSV output
# ——————————————————————————————————————————
df = df.loc[
    (df.index > index_interval.start) &
    (df.index <= index_interval.end)
]

ser = pd.Series(df["value"].values, index=df.index)
ser.name = "value"

ser.to_csv(os.environ["OUTPUT_FILE"])