import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Constants
MAX_REALISTIC_SPEED = {
    'Container ships': 25,
    'Bulk carriers': 18,
    'Passenger ships': 22
}

FUEL_CONSUMPTION = 0.190  # kg/kWh
CO2_FACTOR = 3.14  # kg CO2/kg fuel
seawater_density = 1.025
block_coefficient = 0.7

# Load data
ship_dims = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_dimensions.csv", sep=';')
ship_dims.columns = ship_dims.columns.str.strip().str.lower()

# Load time series
ship_dataA = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_A.csv", sep=';')
ship_dataB = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_B.csv", sep=';')
ship_dataC = pd.read_csv(r"C:\Users\Sysadmin\Downloads\ship_C.csv", sep=';')


def parse_timestamp(x):
    if isinstance(x, (int, float)):
        return pd.to_datetime(x, unit="d", origin="1899-12-30")
    else:
        return pd.to_datetime(x, format="%d.%m.%Y %H:%M", errors="coerce")


# Created speed validation function
def validate_and_correct_speeds(speeds, ship_type, service_speed):
    """
    Validated and corrected unrealistic speed values
    """
    max_allowed = MAX_REALISTIC_SPEED.get(ship_type, service_speed)

    # Identify unrealistic speeds
    unrealistic_mask = speeds > max_allowed

    if unrealistic_mask.any():
        print(f"  Found {unrealistic_mask.sum()} unrealistic speed points (> {max_allowed} knots)")

        # Caped at maximum realistic speed
        corrected = speeds.copy()
        corrected[unrealistic_mask] = max_allowed

        return corrected

    return speeds


def calculate_power_with_limits(speed, displacement, C_A, aux_power, main_power_max, ship_type):
    """
    Calculated power with realistic limits
    """
    # Calculated theoretical power
    power_main = (displacement ** (2 / 3)) * (speed ** 3) / C_A

    # Caped at maximum engine power
    power_main = np.minimum(power_main, main_power_max)

    # Added auxiliary power
    total_power = power_main + aux_power

    return total_power


ship_results = {}

for ship_idx, ship_row in ship_dims.iterrows():
    ship_name = ship_row['ship name']
    ship_type = ship_row['ship type']

    # Get the correct time series data
    if ship_name == 'Ship A':
        time_df = ship_dataA.copy()
    elif ship_name == 'Ship B':
        time_df = ship_dataB.copy()
    elif ship_name == 'Ship C':
        time_df = ship_dataC.copy()
    else:
        continue

    print(f"\n{'=' * 60}")
    print(f"ANALYZING: {ship_name} ({ship_type})")
    print(f"{'=' * 60}")

    # Ship parameters
    L = ship_row['length (meters)']
    B = ship_row['breadth (meters)']
    T = ship_row['draught (meters)']
    V_service = ship_row['service speed (knots)']
    P_main_max = ship_row['main engine power (kw)']
    P_aux = ship_row.get('aux. engine power (kw)',0)

    # Calculated displacement and C_A
    disp_volume = L * B * T * block_coefficient
    disp_mass = disp_volume * seawater_density
    C_A = (disp_mass ** (2 / 3)) * (V_service ** 3) / (P_main_max + P_aux)

    # Processed time data
    time_df['timestamp'] = time_df['timestamp'].apply(parse_timestamp)
    time_df = time_df.sort_values('timestamp')
    time_df['hours_since_prev'] = time_df['timestamp'].diff().dt.total_seconds() / 3600
    time_df['hours_since_prev'] = time_df['hours_since_prev'].fillna(0)

    # Analyze speed data
    if 'speed' not in time_df.columns:
        print("  ERROR: No speed column found!")
        continue

    original_speeds = time_df['speed'].copy()

    print(f"\n  SPEED ANALYSIS:")
    print(f"    Original data - Min: {original_speeds.min():.2f} knots")
    print(f"                    Max: {original_speeds.max():.2f} knots")
    print(f"                    Mean: {original_speeds.mean():.2f} knots")
    print(f"                    Std: {original_speeds.std():.2f} knots")
    print(f"    Service speed: {V_service:.1f} knots")

    # Validated and corrected speeds
    validated_speeds = validate_and_correct_speeds(
        original_speeds, ship_type, V_service
    )

    print(f"\n  VALIDATED SPEEDS:")
    print(f"    Min: {validated_speeds.min():.2f} knots")
    print(f"    Max: {validated_speeds.max():.2f} knots")
    print(f"    Mean: {validated_speeds.mean():.2f} knots")

    # Calculated power with realistic limits
    time_df['speed_validated'] = validated_speeds
    time_df['power_main_kw'] = (disp_mass ** (2 / 3)) * (validated_speeds ** 3) / C_A

    # Caped at maximum engine power
    time_df['power_main_kw'] = np.minimum(time_df['power_main_kw'], P_main_max)

    # Added auxiliary power
    time_df['power_total_kw'] = time_df['power_main_kw'] + P_aux

    # For very low speeds, use auxiliary only
    low_speed_mask = validated_speeds < 0.5
    time_df.loc[low_speed_mask, 'power_total_kw'] = P_aux

    # Calculated energy
    time_df['energy_kwh'] = time_df['power_total_kw'] * time_df['hours_since_prev']

    # Calculated fuel and CO2
    time_df['fuel_kg'] = time_df['energy_kwh'] * FUEL_CONSUMPTION
    time_df['co2_kg'] = time_df['fuel_kg'] * CO2_FACTOR

    # Summarized
    total_hours = time_df['hours_since_prev'].sum()
    total_energy = time_df['energy_kwh'].sum()
    total_fuel = time_df['fuel_kg'].sum()
    total_co2 = time_df['co2_kg'].sum()

    print(f"\n  RESULTS:")
    print(f"    admiralit coefficent: {C_A:.2f}")
    print(f"    Total time period: {total_hours:.2f} hours ({total_hours / 24:.1f} days)")
    print(f"    Max power demand: {time_df['power_total_kw'].max():,.0f} KW")
    print(f"    Avg power demand: {time_df['power_total_kw'].mean():,.0f} KW")
    print(f"    Total energy: {total_energy:,.0f} kWh")
    print(f"    Total fuel: {total_fuel:,.0f} kg ({total_fuel / 1000:,.1f} tons)")
    print(f"    Total CO2: {total_co2:,.0f} kg ({total_co2 / 1000:,.1f} tons)")

    # Stored results
    ship_results[ship_name] = {
        'ship_type': ship_type,
        'displacement': disp_mass,
        'service_speed': V_service,
        'max_engine_power': P_main_max,
        'time_data': time_df,
        'total_hours': total_hours,
        'total_energy_kwh': total_energy,
        'total_fuel_kg': total_fuel,
        'total_co2_kg': total_co2
    }

    # Created visualizations
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 2, 1)
    plt.hist(original_speeds, bins=50, alpha=0.5, label='Original', color='red')
    plt.hist(validated_speeds, bins=50, alpha=0.5, label='Validated', color='blue')
    plt.xlabel('Speed (knots)')
    plt.ylabel('Frequency')
    plt.title('Speed Distribution')
    plt.legend()
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 2, 2)
    plt.plot(time_df['timestamp'], time_df['power_total_kw'], 'g-')
    plt.axhline(y=P_main_max + P_aux, color='r', linestyle='--', label='Max Power')
    plt.xlabel('Time')
    plt.ylabel('Power (KW)')
    plt.title('Power Demand')
    plt.grid(True, alpha=0.3)

    plt.subplot(2, 2, 3)
    cumulative_co2 = time_df['co2_kg'].cumsum()
    plt.plot(time_df['timestamp'], cumulative_co2, 'purple')
    plt.xlabel('Time')
    plt.ylabel('Cumulative CO2 (kg)')
    plt.title('Cumulative CO2 Emissions')
    plt.grid(True, alpha=0.3)

    plt.suptitle(f'{ship_name} ({ship_type}) - Analysis Results', fontsize=10, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f'{ship_name.replace(" ", "_")}_analysis.png', dpi=150, bbox_inches='tight')
    plt.show()
