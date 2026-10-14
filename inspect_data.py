from pathlib import Path

import pandas as pd

DATA_DIR = Path("data")

FILES = [
    "shipment_records.csv",
    "context_notes.csv",
    "sample_output_format_v2.csv",
]

for filename in FILES:
    path = DATA_DIR / filename

    print(f"\n{'=' * 70}")
    print(f"FILE: {filename}")
    print(f"{'=' * 70}")

    if not path.exists():
        print(f"ERROR: File not found: {path.resolve()}")
        continue

    if filename == "sample_output_format_v2.csv":
        print("\nRaw CSV contents:")

        with path.open("r", encoding="utf-8-sig") as file:
            for line_number, line in enumerate(file, start=1):
                print(f"{line_number}: {line.rstrip()}")

        print("\nHeader columns:")

        header = pd.read_csv(path, nrows=0)
        print(header.columns.tolist())
        print("Number of columns:", len(header.columns))

        continue

    df = pd.read_csv(path)

    print("\nShape:", df.shape)
    print("\nColumns:", df.columns.tolist())
    print("\nData types:")
    print(df.dtypes)
    print("\nFirst 3 rows:")
    print(df.head(3).to_string(index=False))
    print("\nMissing values:")
    print(df.isnull().sum().to_string())