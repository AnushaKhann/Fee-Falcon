from src.aggregation import aggregate_weekly_costs
from src.baselines import add_baselines
from src.data_loader import load_shipments


def main():
    shipments = load_shipments("data/shipment_records.csv")

    weekly = aggregate_weekly_costs(shipments)
    result = add_baselines(weekly)

    print("Weekly records:", len(weekly))
    print("Records with historical baselines:",
          result["own_history_baseline"].notna().sum())
    print("Records with peer baselines:",
          result["similar_routes_baseline"].notna().sum())

    print("\nFirst 15 records:")
    columns = [
        "origin",
        "destination",
        "route_type",
        "week_of",
        "cost_per_tonne_km",
        "own_history_baseline",
        "vs_own_history_pct",
        "similar_routes_baseline",
        "vs_similar_routes_pct",
    ]

    print(result[columns].head(15).to_string(index=False))

    assert len(result) == 728

    # There should be no historical baseline in the first week
    # for any route.
    first_weeks = (
        result.groupby(
            ["origin", "destination", "route_type"]
        )["week_of"]
        .transform("min")
    )

    assert result.loc[
        result["week_of"] == first_weeks,
        "own_history_baseline",
    ].isna().all()

    print("\nBaseline integration checks passed.")


if __name__ == "__main__":
    main()