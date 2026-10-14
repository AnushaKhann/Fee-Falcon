import pandas as pd
import pytest

from src.aggregation import aggregate_weekly_costs


def test_shipments_are_grouped_into_monday_weeks():
    shipments = pd.DataFrame(
        {
            "origin": ["Mumbai", "Mumbai", "Mumbai"],
            "destination": ["Pune", "Pune", "Pune"],
            "route_type": ["Short", "Short", "Short"],
            "quantity_tonnes": [10.0, 20.0, 10.0],
            "distance_km": [100.0, 100.0, 100.0],
            "freight_cost_inr": [1000, 2000, 1500],
            "shipment_date": [
                "2024-01-01",  # Monday
                "2024-01-07",  # Sunday, same week
                "2024-01-08",  # Next Monday
            ],
        }
    )

    result = aggregate_weekly_costs(shipments)

    assert len(result) == 2

    first_week = result.iloc[0]
    second_week = result.iloc[1]

    assert first_week["week_of"] == pd.Timestamp("2024-01-01")
    assert first_week["shipment_count"] == 2

    # (1000 + 2000) / ((10 * 100) + (20 * 100))
    assert first_week["cost_per_tonne_km"] == pytest.approx(1.0)

    assert second_week["week_of"] == pd.Timestamp("2024-01-08")
    assert second_week["shipment_count"] == 1

    # 1500 / (10 * 100)
    assert second_week["cost_per_tonne_km"] == pytest.approx(1.5)


def test_empty_input_is_rejected():
    empty = pd.DataFrame(
        columns=[
            "origin",
            "destination",
            "route_type",
            "quantity_tonnes",
            "distance_km",
            "freight_cost_inr",
            "shipment_date",
        ]
    )

    with pytest.raises(ValueError, match="empty"):
        aggregate_weekly_costs(empty)


def test_missing_required_column_is_rejected():
    shipments = pd.DataFrame(
        {
            "origin": ["Mumbai"],
            "destination": ["Pune"],
        }
    )

    with pytest.raises(ValueError, match="missing columns"):
        aggregate_weekly_costs(shipments)