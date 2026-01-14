from importlib.metadata import files
import pandas as pd
import numpy as np
# Load vessel time-series data and Load ship characteristics
ship_dims = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_dimensions.csv",
    sep=';')
ship_dataB = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_B.csv",
    sep=';')
ship_dataC = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_C.csv",
    sep=';')
ship_dataA = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_A.csv",
    sep=';')
ship_dims.columns = ship_dims.columns.str.strip().str.lower()
print(ship_dims.columns.tolist())
weight_ship = ship_dims["deadweight"]
ship_speed = ship_dims["service speed (knots)"]
engine_power_main = ship_dims["main engine power (kw)"]
engine_power_aux = ship_dims["aux. engine power (kw)"]

new_C_value = (weight_ship ** 2/3 * ship_speed ** 3)/(engine_power_main + engine_power_aux)

print(new_C_value)

new_power_demand = (weight_ship ** 2/3 * ship_speed ** 3)/new_C_value
print(new_power_demand)

def parse_timestamp(x):
    # Excel numeric date
    if isinstance(x, (int, float)):
        return pd.to_datetime(x, unit="d", origin="1899-12-30")
    # String date
    else:
        return pd.to_datetime(x, format="%d.%m.%Y %H:%M", errors="coerce")

ship_timeA = ship_dataA.copy()
ship_timeA["timestamp"] = ship_timeA["timestamp"].apply(parse_timestamp)
ship_timeA = ship_timeA.sort_values("timestamp")
ship_timeA["hours_since_prev"] = ship_timeA["timestamp"].diff().dt.total_seconds() / 3600
ship_timeA = ship_timeA.fillna(0)

ship_timeB = ship_dataB.copy()
ship_timeB["timestamp"] = ship_timeB["timestamp"].apply(parse_timestamp)
ship_timeB = ship_timeB.sort_values("timestamp")
ship_timeB["hours_since_prev"] = ship_timeB["timestamp"].diff().dt.total_seconds() / 3600
ship_timeB = ship_timeB.fillna(0)

ship_timeC = ship_dataC.copy()
ship_timeC["timestamp"] = ship_timeC["timestamp"].apply(parse_timestamp)
ship_timeC = ship_timeC.sort_values("timestamp")
ship_timeC["hours_since_prev"] = ship_timeC["timestamp"].diff().dt.total_seconds() / 3600
ship_timeC = ship_timeC.fillna(0)

energy_demand_KwhA = new_power_demand * ship_timeA["hours_since_prev"]
energy_demand_KwhB = new_power_demand * ship_timeB["hours_since_prev"]
energy_demand_KwhC = new_power_demand * ship_timeC["hours_since_prev"]

FUEL_CONSUMPTION = 0.2       # kg fuel per kWh
CO2_FACTOR = 3.114          # kg CO2 per kg fuel

fuel_kgA = energy_demand_KwhA * FUEL_CONSUMPTION
fuel_kgB = energy_demand_KwhB * FUEL_CONSUMPTION
fuel_kgC = energy_demand_KwhC * FUEL_CONSUMPTION
C02_kgA = fuel_kgA * CO2_FACTOR
C02_kgB = fuel_kgB * CO2_FACTOR
C02_kgC = fuel_kgC * CO2_FACTOR

energy_demand_KwhB.isna().sum()
fuel_kgB.isna().sum()
C02_kgB.isna().sum()
print(ship_timeC)
energy_demand_KwhB.describe()
total_co2_A = C02_kgA.sum(skipna=True)
total_co2_B = C02_kgB.sum(skipna=True)
total_co2_C = C02_kgC.sum(skipna=True)
print(total_co2_B)
print(total_co2_C)
print(total_co2_A)
