from dataclasses import dataclass
import numpy as np


@dataclass
class BatteryParams:
    """
    Battery model parameters.
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
    cooling_coeff_w_per_k: float = 80.0
    dt_hours: float = 1.0

    # Placeholder polynomial coefficients for R(T) in ohm:
    # R(T) = a0 + a1*T + a2*T^2
    # Stage 2 will replace this with fitted coefficients from published Li-ion data.
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
        """
        coeffs = self.params.resistance_coeffs
        resistance = sum(a * temperature_c**i for i, a in enumerate(coeffs))

        # Avoid non-physical negative resistance.
        return max(resistance, 1e-4)

    def efficiency(self, temperature_c: float) -> float:
        """
        Simple temperature-dependent efficiency model.
        """
        eta = 0.96 - 0.00025 * abs(temperature_c - 25.0)
        return float(np.clip(eta, 0.85, 0.97))

    def available_charge_power_kw(self) -> float:
        """
        Maximum possible charging power based on SOC and power limit.
        """
        remaining_capacity_kwh = (
            self.params.soc_max - self.soc
        ) * self.params.capacity_kwh

        return max(
            0.0,
            min(
                self.params.max_power_kw,
                remaining_capacity_kwh / self.params.dt_hours,
            ),
        )

    def available_discharge_power_kw(self) -> float:
        """
        Maximum possible discharging power based on SOC and power limit.
        """
        available_energy_kwh = (
            self.soc - self.params.soc_min
        ) * self.params.capacity_kwh

        return max(
            0.0,
            min(
                self.params.max_power_kw,
                available_energy_kwh / self.params.dt_hours,
            ),
        )

    def solve_coupled_step(self, battery_power_kw: float) -> dict:
        """
        Fixed-point iteration for thermal-electrical coupling.

        Sign convention:
            battery_power_kw > 0 : charging
            battery_power_kw < 0 : discharging

        The electrical current depends on battery power.
        The heat generation depends on I^2 R(T).
        The resistance depends on temperature.
        Temperature evolves from heat generation and cooling.
        """

        p = self.params
        dt_seconds = p.dt_hours * 3600.0

        temperature_guess = self.temperature_c
        power_w = abs(battery_power_kw) * 1000.0

        converged = False
        iterations = 0

        last_current_a = 0.0
        last_resistance = self.resistance_ohm(temperature_guess)
        last_q_gen_w = 0.0
        last_q_loss_w = 0.0

        for k in range(p.fixed_point_max_iter):
            resistance = self.resistance_ohm(temperature_guess)

            if p.nominal_voltage_v > 0:
                current_a = power_w / p.nominal_voltage_v
            else:
                current_a = 0.0

            q_gen_w = current_a**2 * resistance
            q_loss_w = p.cooling_coeff_w_per_k * (
                temperature_guess - p.ambient_temperature_c
            )

            # Semi-implicit temperature update:
            # Cooling is treated implicitly for better numerical stability.
            temperature_new = (
                self.temperature_c
                + (dt_seconds / p.thermal_capacity_j_per_k)
                * (q_gen_w + p.cooling_coeff_w_per_k * p.ambient_temperature_c)
            ) / (
                1.0
                + (dt_seconds / p.thermal_capacity_j_per_k)
                * p.cooling_coeff_w_per_k
            )

            last_current_a = current_a
            last_resistance = resistance
            last_q_gen_w = q_gen_w
            last_q_loss_w = q_loss_w

            iterations = k + 1

            if abs(temperature_new - temperature_guess) < p.fixed_point_tolerance:
                converged = True
                temperature_guess = temperature_new
                break

            temperature_guess = temperature_new

        self.temperature_c = temperature_guess

        eta = self.efficiency(self.temperature_c)

        if battery_power_kw > 0:
            # Charging: only eta fraction is effectively stored.
            delta_soc = (
                eta
                * battery_power_kw
                * p.dt_hours
                / p.capacity_kwh
            )

        elif battery_power_kw < 0:
            # Discharging: more stored energy is drawn due to losses.
            delta_soc = (
                battery_power_kw
                * p.dt_hours
                / (eta * p.capacity_kwh)
            )

        else:
            delta_soc = 0.0

        self.soc = float(
            np.clip(
                self.soc + delta_soc,
                p.soc_min,
                p.soc_max,
            )
        )

        return {
            "soc": self.soc,
            "temperature_c": self.temperature_c,
            "efficiency": eta,
            "current_a": last_current_a,
            "resistance_ohm": last_resistance,
            "q_gen_w": last_q_gen_w,
            "q_loss_w": last_q_loss_w,
            "converged": converged,
            "iterations": iterations,
        }