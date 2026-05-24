import pandas as pd

from battery import PhysicsAwareBattery


def run_simulation(generation_kw, load_kw, battery: PhysicsAwareBattery) -> pd.DataFrame:
    """
    Run a time-domain simulation.

    Sign convention:
        battery_power_kw > 0: charging
        battery_power_kw < 0: discharging
        grid_power_kw > 0: import from grid
        grid_power_kw < 0: export/curtailment to grid
    """

    records = []

    for step, (p_gen, p_load) in enumerate(zip(generation_kw, load_kw)):
        net_power_kw = p_gen - p_load

        if net_power_kw > 0:
            # Surplus generation: charge battery first.
            battery_power_kw = min(net_power_kw, battery.available_charge_power_kw())
        else:
            # Deficit: discharge battery if possible.
            requested_discharge_kw = -net_power_kw
            battery_power_kw = -min(requested_discharge_kw, battery.available_discharge_power_kw())

        state = battery.solve_coupled_step(battery_power_kw)

        # Grid power is what remains after battery action.
        # If positive: grid import. If negative: surplus export/curtailment.
        grid_power_kw = p_load - p_gen + battery_power_kw

        records.append(
            {
                "step": step,
                "generation_kw": p_gen,
                "load_kw": p_load,
                "net_power_kw": net_power_kw,
                "battery_power_kw": battery_power_kw,
                "grid_power_kw": grid_power_kw,
                **state,
            }
        )

    return pd.DataFrame(records)
