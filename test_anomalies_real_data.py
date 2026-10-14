from src.aggregation import aggregate_weekly_costs
from src.anomaly_detection import detect_anomalies
from src.baselines import add_baselines
from src.data_loader import load_shipments


def main():
    shipments = load_shipments("data/shipment_records.csv")

    weekly = aggregate_weekly_costs(shipments)
    baselined = add_baselines(weekly)
    results = detect_anomalies(baselined)

    candidates = results[
        results["anomaly_candidate"]
    ].copy()

    print("Total route-weeks:", len(results))
    print("Anomaly candidates:", len(candidates))

    print("\nCandidates by route:")

    print(
        candidates.groupby(
            ["origin", "destination"]
        ).size().to_string()
    )

    print("\nFirst 20 anomaly candidates:")

    columns = [
        "origin",
        "destination",
        "week_of",
        "cost_per_tonne_km",
        "vs_own_history_pct",
        "vs_similar_routes_pct",
        "anomaly_trigger",
    ]

    print(
        candidates[columns]
        .head(20)
        .to_string(index=False)
    )

    print("\nAnomaly detection completed.")


if __name__ == "__main__":
    main()