import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from battery import BatteryParams, PhysicsAwareBattery
from profiles import synthetic_solar_profile, synthetic_load_profile
from simulation import run_simulation
from metrics import calculate_metrics
from plots import plot_results
from resistance_fit import load_lfp_coefficients_ohm, main as run_resistance_fit


def main():
    # --- Stage 2A: show LFP R(T) fit summary before simulation ---
    print("Generating LFP R(T) fit...")
    run_resistance_fit()

    hours = 24

    generation_kw = synthetic_solar_profile(hours=hours, peak_kw=120.0)
    load_kw = synthetic_load_profile(hours=hours, base_kw=60.0)

    # Thermal parameters — LFP pack (Stage 2A)
    # Thermal capacity: ~100 cells × 70 g × 1100 J/kg/K ≈ 7700 J/K (rounded to 75_000 for
    #   pack-level including busbars/BMS/enclosure; scale with actual cell count)
    #   Reference: Lin et al. (2022), DOI: 10.1002/batt.202100401 — Cp ≈ 1100 J/kg/K for LFP
    # Cooling coefficient: 80 W/K — representative of forced-air cooled BESS rack
    #   (natural convection ≈ 17 W/K per cell, forced air ≈ 25-100 W/m²/K)
    #   Reference: Forgez et al. (2010), DOI: 10.1016/j.jpowsour.2009.10.105
    params = BatteryParams(
        capacity_kwh=120.0,
        max_power_kw=50.0,
        nominal_voltage_v=400.0,
        initial_soc=0.5,
        initial_temperature_c=25.0,
        ambient_temperature_c=25.0,
        thermal_capacity_j_per_k=75_000.0,
        cooling_coeff_w_per_k=80.0,   # fixed from 12.0 (Stage 1) — see code review notes
        dt_hours=1.0,
    )

    battery = PhysicsAwareBattery(params)
    results = run_simulation(generation_kw, load_kw, battery)

    output_dir = PROJECT_ROOT / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    results.to_csv(output_dir / "stage1_results.csv", index=False)
    plot_results(results, output_dir=output_dir)

    metrics = calculate_metrics(results, dt_hours=params.dt_hours)

    print("\n=== Stage 1 Simulation Metrics ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    print(f"\nResults saved to: {output_dir}")


if __name__ == "__main__":
    main()
