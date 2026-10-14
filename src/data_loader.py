from pathlib import Path

import pandas as pd


SHIPMENT_COLUMNS = {
    "shipment_id",
    "origin",
    "destination",
    "route_type",
    "material",
    "quantity_tonnes",
    "distance_km",
    "freight_cost_inr",
    "shipment_date",
    "transporter",
}

NOTE_COLUMNS = {
    "note_id",
    "date",
    "applies_to",
    "note",
}


def load_shipments(path: str | Path) -> pd.DataFrame:
    """Load and validate shipment records."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Shipment file not found: {path}")

    df = pd.read_csv(path)

    missing = SHIPMENT_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Shipment file is missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError("Shipment dataset is empty.")

    if df["shipment_id"].isna().any():
        raise ValueError("shipment_id contains missing values.")

    if df["shipment_id"].duplicated().any():
        raise ValueError("shipment_id contains duplicate values.")

    text_columns = [
        "origin",
        "destination",
        "route_type",
        "material",
        "transporter",
    ]

    for column in text_columns:
        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")

        df[column] = df[column].astype(str).str.strip()

        if df[column].eq("").any():
            raise ValueError(f"{column} contains empty strings.")

    valid_route_types = {"Short", "Medium", "Long"}

    invalid_types = set(df["route_type"]) - valid_route_types
    if invalid_types:
        raise ValueError(f"Unexpected route types: {sorted(invalid_types)}")

    numeric_columns = [
        "quantity_tonnes",
        "distance_km",
        "freight_cost_inr",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(df[column], errors="raise")

        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")

        if not df[column].map(lambda value: pd.notna(value) and abs(value) != float("inf")).all():
            raise ValueError(f"{column} contains non-finite values.")

    if (df["quantity_tonnes"] <= 0).any():
        raise ValueError("quantity_tonnes must be positive.")

    if (df["distance_km"] <= 0).any():
        raise ValueError("distance_km must be positive.")

    if (df["freight_cost_inr"] < 0).any():
        raise ValueError("freight_cost_inr cannot be negative.")

    df["shipment_date"] = pd.to_datetime(
        df["shipment_date"],
        errors="raise",
    )

    return df


def load_context_notes(path: str | Path) -> pd.DataFrame:
    """Load and validate contextual notes."""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Context notes file not found: {path}")

    df = pd.read_csv(path)

    missing = NOTE_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"Context notes are missing required columns: {sorted(missing)}"
        )

    if df.empty:
        raise ValueError("Context notes dataset is empty.")

    for column in ["note_id", "date", "applies_to", "note"]:
        if df[column].isna().any():
            raise ValueError(f"{column} contains missing values.")

        df[column] = df[column].astype(str).str.strip()

        if df[column].eq("").any():
            raise ValueError(f"{column} contains empty strings.")

    if df["note_id"].duplicated().any():
        raise ValueError("note_id contains duplicate values.")

    df["date"] = pd.to_datetime(df["date"], errors="raise")

    return df