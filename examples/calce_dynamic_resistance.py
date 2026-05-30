"""
CALCE DST dynamic resistance extraction.
Extracts R_eff = ΔV/ΔI from the A123 dynamic stress test profile.
NOTE: R_eff ≈ 165 mΩ at 25°C includes polarisation and OCV effects.
This is NOT ohmic R₀ (~10-30 mΩ). Use for validation purposes only,
not for the R(T) polynomial in battery.py.
See data/lfp_resistance_temperature.csv for the fitted R₀(T) values.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from calce_parser import load_calce_dynamic_profile
from resistance_extraction import extract_resistance_from_step_changes

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "extracted"
    / "DST-US06-FUDS-25"
    / "A1-007-DST-US06-FUDS-25-20120827.xlsx"
)


def main():
    df = load_calce_dynamic_profile(DATA_FILE)

    resistance_events = extract_resistance_from_step_changes(
        df,
        min_delta_i_a=0.5,
        max_resistance_mohm=200.0,
    )

    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "calce_resistance_events_25c.csv"
    resistance_events.to_csv(output_file, index=False)

    print("\n=== RESISTANCE EVENTS HEAD ===")
    print(resistance_events.head())

    print("\n=== RESISTANCE EVENTS SHAPE ===")
    print(resistance_events.shape)

    print("\n=== RESISTANCE SUMMARY [mΩ] ===")
    print(resistance_events["r_eff_mohm"].describe())

    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()