from pathlib import Path
import pandas as pd


def load_calce_dynamic_profile(file_path: Path) -> pd.DataFrame:
    """
    Load CALCE A123 dynamic profile Excel file.

    Uses Sheet1 because it contains clean reduced columns:
    time, step time, step index, current, voltage, temperature.
    """

    df = pd.read_excel(file_path, sheet_name="Sheet1")

    df = df.rename(
        columns={
            "Test_Time(s)": "time_s",
            "Step_Time(s)": "step_time_s",
            "Step_Index": "step_index",
            "Current(A)": "current_a",
            "Voltage(V)": "voltage_v",
            "Temperature (C)_1": "temperature_c",
        }
    )

    required_cols = [
        "time_s",
        "step_time_s",
        "step_index",
        "current_a",
        "voltage_v",
        "temperature_c",
    ]

    df = df[required_cols].copy()

    df = df.dropna()

    return df