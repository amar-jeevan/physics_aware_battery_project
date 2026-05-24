from dataclasses import dataclass
import numpy as np


@dataclass
class BatteryParams:
    """
    Battery model parameters.

    Units:
        capacity_kwh: battery energy capacity in kWh
        max_power_kw: maximum charge/discharge power in kW
        nominal_voltage_v: nominal DC bus voltage in V
        soc_min: minimum allowed SOC fraction
        soc_max: maximum allowed SOC fraction
        initial_soc: initial SOC fraction
        initial_temperature_c: initial battery temperature in degree Celsius
        ambient_temperature_c: ambient temperature in degree Celsius
        thermal_capacity_j_per_k: lumped thermal capacity in J/K
        cooling_coeff_w_per_k: heat transfer coefficient in W/K
        dt_hours: simulation timestep in hours
    """

    capacity_kwh: float = 100.0
    max_power_kw: float = 50.0
    nominal_voltage_v: float = 400.0

    soc_min: float = 0.1
    soc_max: float = 0.9
    initial_soc: float = 0.5

    initial_temperature_c: float = 25.0
    ambient_temperature_c: float = 25.0

    thermal_capacity_j_per_k: float = 75_000.0
    cooling_coeff_w_per_k: float = 12.0
    dt_hours: float = 1.0

    # Placeholder polynomial coefficients for R(T) in ohm.
    # R(T) = a0 + a1*T + a2*T^2
    # Stage 2 will replace these with coefficients fitted from published Li-ion data.
    resistance_coeffs: tuple = (0.085, -0.0012, 0.000015)

    fixed_point_tolerance: float = 1e-5
    fixed_point_max_iter: int = 50


class PhysicsAwareBattery:
    def __init__(self, params: BatteryParams):
        self.params = params
        self.soc = params.initial_soc
        self.temperature_c = params.initial_temperature_c

    def resistance_ohm(self, temperature_c: float) -> float:
        """
        Temperature-dependent internal resistance.

        This is a placeholder polynomial model. The lower bound avoids
        nonphysical negative resistance if exploratory coefficients are changed.
        """
        coeffs = self.params.resistance_coeffs
        resistance = sum(a * temperature_c**i for i, a in enumerate(coeffs))
        return max(resistance, 1e-4)

    def efficiency(self, temperature_c: float) -> float:
        """
        Simple temperature-dependent efficiency model.

        Efficiency is highest near 25 degC and decreases away from this reference.
        This is intentionally simple for Stage 1.
        """
        eta = 0.96 - 0.00025 * abs(temperature_c - 25.0)
        return float(np.clip(eta, 0.85, 0.97))

    def available_charge_power_kw(self) -> float:
        remaining_capacity_kwh = (self.params.soc_max - self.soc) * self.params.capacity_kwh
        return max(0.0, min(self.params.max_power_kw, remaining_capacity_kwh / self.params.dt_hours))

    def available_discharge_power_kw(self) -> float:
        available_energy_kwh = (self.soc - self.params.soc_min) * self.params.capacity_kwh
        return max(0.0, min(self.params.max_power_kw, available_energy_kwh / self.params.dt_hours))

    def solve_coupled_step(self, battery_power_kw: float) -> dict:
        """
        Fixed-point iteration for thermal-electrical coupling.

        Convention:
            battery_power_kw > 0: charging
            battery_power_kw < 0: discharging

        The electrical current depends on battery power.
        The heat generation depends on I^2 R(T).
        The next temperature depends on heat generation and cooling.
        """

        p = self.params
        dt_seconds = p.dt_hours * 3600.0

        temperature_guess = self.temperature_c
        power_w = abs(battery_power_kw) * 1000.0

        converged = False
        iterations = 0

        for k in range(p.fixed_point_max_iter):
            resistance = self.resistance_ohm(temperature_guess)
            current_a = power_w / p.nominal_voltage_v if p.nominal_voltage_v > 0 else 0.0

            q_gen_w = current_a**2 * resistance
            q_loss_w = p.cooling_coeff_w_per_k * (temperature_guess - p.ambient_temperature_c)

            temperature_new = self.temperature_c + ((q_gen_w - q_loss_w) / p.thermal_capacity_j_per_k) * dt_seconds

            iterations = k + 1
            if abs(temperature_new - temperature_guess) < p.fixed_point_tolerance:
                converged = True
                temperature_guess = temperature_new
                break

            temperature_guess = temperature_new

        self.temperature_c = temperature_guess

        eta = self.efficiency(self.temperature_c)

        if battery_power_kw > 0:
            # Charging: only eta fraction effectively stored.
            delta_soc = eta * battery_power_kw * p.dt_hours / p.capacity_kwh
        elif battery_power_kw < 0:
            # Discharging: more internal energy is drawn due to losses.
            delta_soc = battery_power_kw * p.dt_hours / (eta * p.capacity_kwh)
        else:
            delta_soc = 0.0

        self.soc = float(np.clip(self.soc + delta_soc, p.soc_min, p.soc_max))

        return {
            "soc": self.soc,
            "temperature_c": self.temperature_c,
            "efficiency": eta,
            "current_a": current_a if power_w > 0 else 0.0,
            "resistance_ohm": self.resistance_ohm(self.temperature_c),
            "q_gen_w": (power_w / p.nominal_voltage_v) ** 2 * self.resistance_ohm(self.temperature_c) if power_w > 0 else 0.0,
            "converged": converged,
            "iterations": iterations,
        }
