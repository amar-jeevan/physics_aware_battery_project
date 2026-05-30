from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "extracted"
    / "DST-US06-FUDS-25"
    / "A1-007-DST-US06-FUDS-25-20120827.xlsx"
)


def main():
    print(f"Reading: {DATA_FILE}")

    excel_file = pd.ExcelFile(DATA_FILE)

    print("\n=== SHEET NAMES ===")
    print(excel_file.sheet_names)

    for sheet in excel_file.sheet_names:
        print(f"\n\n=== SHEET: {sheet} ===")

        df = pd.read_excel(DATA_FILE, sheet_name=sheet)

        print("\nHEAD:")
        print(df.head())

        print("\nCOLUMNS:")
        print(df.columns.tolist())

        print("\nSHAPE:")
        print(df.shape)


if __name__ == "__main__":
    main()