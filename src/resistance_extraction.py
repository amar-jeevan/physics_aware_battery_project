import pandas as pd


def extract_resistance_from_step_changes(
    df: pd.DataFrame,
    min_delta_i_a: float = 0.5,
    max_resistance_mohm: float = 200.0,
) -> pd.DataFrame:
    """
    Estimate effective resistance from step-index transitions.

    This is still an effective dynamic resistance, not pure EIS resistance.

    Method:
        1. Detect where Step_Index changes.
        2. Compare the last point before the step change with the first point after.
        3. Compute R_eff = |Delta V / Delta I|.
        4. Filter extreme outliers.

    This is more physically meaningful than scanning every row.
    """

    records = []

    step_change_indices = df.index[df["step_index"].diff() != 0].tolist()

    for idx in step_change_indices:
        if idx <= 0 or idx >= len(df):
            continue

        before = df.loc[idx - 1]
        after = df.loc[idx]

        delta_i = after["current_a"] - before["current_a"]
        delta_v = after["voltage_v"] - before["voltage_v"]

        if abs(delta_i) < min_delta_i_a:
            continue

        r_eff_ohm = abs(delta_v / delta_i)
        r_eff_mohm = r_eff_ohm * 1000.0

        if r_eff_mohm > max_resistance_mohm:
            continue

        records.append(
            {
                "time_s": after["time_s"],
                "temperature_c": after["temperature_c"],
                "step_before": before["step_index"],
                "step_after": after["step_index"],
                "current_before_a": before["current_a"],
                "current_after_a": after["current_a"],
                "voltage_before_v": before["voltage_v"],
                "voltage_after_v": after["voltage_v"],
                "delta_i_a": delta_i,
                "delta_v_v": delta_v,
                "r_eff_ohm": r_eff_ohm,
                "r_eff_mohm": r_eff_mohm,
            }
        )

    return pd.DataFrame(records)