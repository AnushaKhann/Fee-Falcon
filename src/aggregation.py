import pandas as pd


ROUTE_COLUMNS = [
    "origin",
    "destination",
    "route_type",
]


def aggregate_weekly_costs(
    shipments: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate shipment records into weekly route-level costs.

    Weeks run Monday through Sunday.

    Cost per tonne-km is calculated as:
        sum(freight_cost_inr)
        /
        sum(quantity_tonnes * distance_km)

    Returns one record per route and week.
    """
    required_columns = {
        "origin",
        "destination",
        "route_type",
        "quantity_tonnes",
        "distance_km",
        "freight_cost_inr",
        "shipment_date",
    }

    missing = required_columns - set(shipments.columns)

    if missing:
        raise ValueError(
            f"Shipment data is missing columns: {sorted(missing)}"
        )

    if shipments.empty:
        raise ValueError("Cannot aggregate an empty shipment dataset.")

    df = shipments.copy()

    df["shipment_date"] = pd.to_datetime(
        df["shipment_date"],
        errors="raise",
    )

    # Monday = 0, Tuesday = 1, ..., Sunday = 6.
    days_since_monday = df["shipment_date"].dt.dayofweek

    df["week_of"] = (
        df["shipment_date"].dt.normalize()
        - pd.to_timedelta(days_since_monday, unit="D")
    )

    # Each shipment contributes quantity * distance tonne-km.
    df["tonne_km"] = (
        df["quantity_tonnes"] * df["distance_km"]
    )

    group_columns = ROUTE_COLUMNS + ["week_of"]

    weekly = (
        df.groupby(
            group_columns,
            as_index=False,
            sort=True,
        )
        .agg(
            total_freight_cost_inr=("freight_cost_inr", "sum"),
            total_tonne_km=("tonne_km", "sum"),
            shipment_count=("shipment_date", "size"),
        )
    )

    if (weekly["total_tonne_km"] <= 0).any():
        raise ValueError(
            "Weekly total tonne-km must be positive."
        )

    weekly["cost_per_tonne_km"] = (
        weekly["total_freight_cost_inr"]
        / weekly["total_tonne_km"]
    )

    return weekly.sort_values(
        group_columns,
        kind="stable",
    ).reset_index(drop=True)