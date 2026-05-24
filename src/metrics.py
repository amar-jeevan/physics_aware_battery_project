def calculate_metrics(results, dt_hours: float = 1.0) -> dict:
    total_load_kwh = results["load_kw"].sum() * dt_hours

    grid_import_kwh = results.loc[results["grid_power_kw"] > 0, "grid_power_kw"].sum() * dt_hours
    surplus_export_kwh = -results.loc[results["grid_power_kw"] < 0, "grid_power_kw"].sum() * dt_hours

    battery_charge_kwh = results.loc[results["battery_power_kw"] > 0, "battery_power_kw"].sum() * dt_hours
    battery_discharge_kwh = -results.loc[results["battery_power_kw"] < 0, "battery_power_kw"].sum() * dt_hours

    energy_served_by_local_system_kwh = max(total_load_kwh - grid_import_kwh, 0.0)

    return {
        "total_load_kwh": total_load_kwh,
        "grid_import_kwh": grid_import_kwh,
        "surplus_export_or_curtailment_kwh": surplus_export_kwh,
        "battery_charge_kwh": battery_charge_kwh,
        "battery_discharge_kwh": battery_discharge_kwh,
        "local_energy_served_percent": 100.0 * energy_served_by_local_system_kwh / total_load_kwh if total_load_kwh > 0 else 0.0,
        "max_temperature_c": results["temperature_c"].max(),
        "average_efficiency_percent": 100.0 * results["efficiency"].mean(),
        "max_fixed_point_iterations": int(results["iterations"].max()),
        "all_steps_converged": bool(results["converged"].all()),
    }
