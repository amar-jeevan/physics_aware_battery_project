from dataclasses import dataclass
from pathlib import Path
import numpy as np

# Load LFP R(T) coefficients from the resistance fit module at import time.
# This keeps battery.py decoupled from resistance_fit.py — if the fit module
# is unavailable, the fallback tuple below is used instead.
def _load_lfp_coeffs() -> tuple:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from resistance_fit import load_lfp_coefficients_ohm
        return load_lfp_coefficients_ohm()
    except Exception:
        # Fallback: literature-derived LFP coefficients (A123, Lin 2013)
        # R(T) [Ω] = 0.028318 - 0.0016036*T + 0.00002848*T²
        return (0.028318, -0.0016036, 0.00002848)

_LFP_RESISTANCE_COEFFS = _load_lfp_coeffs()


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

    # Thermal parameters — sourced from Gao et al. 2017, Table 1
    # (same cell: A123 ANR26650M1-B)
    #
    # Single-cell values from paper:
    #   Cp          = 810.53 J/kg/K  (measured, Table 1)
    #   m_cell      = 76 g = 0.076 kg
    #   C_cell      = 0.076 × 810.53 = 61.6 J/K per cell
    #   hconv       = 5 W/m²/K  (natural convection, still air, Table 1)
    #   Sarea       = 0.0149 m²  (26650 surface area, Table 1)
    #   h_cell      = 5 × 0.0149 = 0.0745 W/K per cell
    #   τ_cell      = 61.6 / 0.0745 = 827 s ≈ 14 min (single cell, still air)
    #
    # Pack-level scaling (for a 120 kWh / 400 V system):
    #   ~14,500 cells → C_pack ≈ 14,500 × 61.6 ≈ 893,000 J/K
    #   For a single-module (representative) model, 75,000 J/K (~1,200 cells)
    #   h = 80 W/K corresponds to forced-air cooling at pack level.
    #   Adjust both values linearly if modelling a different pack size.
    thermal_capacity_j_per_k: float = 75_000.0
    cooling_coeff_w_per_k: float = 80.0
    dt_hours: float = 1.0

    # LFP polynomial coefficients for R(T) in ohm:
    # R(T) = a0 + a1*T + a2*T^2  [Ω]
    #
    # Stage 2A values — fitted from published A123 ANR26650M1A LFP data:
    #   Source: Lin et al. (2013) IEEE TCST, DOI: 10.1109/TCST.2013.2278763
    #           Forgez et al. (2010) J. Power Sources, DOI: 10.1016/j.jpowsour.2009.10.105
    #           Consistent with Sandia/Preger (2020), DOI: 10.1149/1945-7111/abae37
    #   Valid: -10 °C to +40 °C, ~50% SOC, fresh cell
    #   Fit:  RMSE = 2.97 mΩ,  R² = 0.961
    #
    # Stage 2B upgrade: re-fit using raw CALCE A123 DST (0-50 °C) and
    #   Sandia Battery Archive SNL_18650_LFP CSV once downloaded.
    #   Run src/resistance_fit.py to regenerate coefficients automatically.
    resistance_coeffs: tuple = _LFP_RESISTANCE_COEFFS

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