from src.aggregation import aggregate_weekly_costs
from src.data_loader import load_shipments


def main():
    shipments = load_shipments("data/shipment_records.csv")

    weekly = aggregate_weekly_costs(shipments)

    print("Original shipment records:", len(shipments))
    print("Aggregated route-week records:", len(weekly))

    print("\nFirst 10 weekly records:")
    print(
        weekly.head(10).to_string(index=False)
    )

    print("\nRoute-week counts:")
    print(
        weekly.groupby(
            ["origin", "destination", "route_type"]
        ).size().to_string()
    )

    print("\nCost statistics:")
    print(
        weekly["cost_per_tonne_km"].describe().to_string()
    )

    # Basic integrity checks.
    assert weekly["week_of"].dt.dayofweek.eq(0).all()
    assert weekly["cost_per_tonne_km"].notna().all()
    assert (weekly["cost_per_tonne_km"] >= 0).all()

    print("\nWeekly aggregation validation passed.")


if __name__ == "__main__":
    main()