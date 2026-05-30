import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from calce_parser import load_calce_dynamic_profile


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

    print("\n=== CLEANED DATA HEAD ===")
    print(df.head())

    print("\n=== CLEANED COLUMNS ===")
    print(df.columns.tolist())

    print("\n=== SHAPE ===")
    print(df.shape)

    print("\n=== SUMMARY ===")
    print(df.describe())


if __name__ == "__main__":
    main()