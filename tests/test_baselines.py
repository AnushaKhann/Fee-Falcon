import pandas as pd
import pytest

from src.baselines import add_baselines


def make_weekly_data():
    dates = pd.date_range(
        "2024-01-01",
        periods=10,
        freq="W-MON",
    )

    rows = []

    # Route A: Short
    for index, week in enumerate(dates):
        rows.append(
            {
                "origin": "Mumbai",
                "destination": "Pune",
                "route_type": "Short",
                "week_of": week,
                "cost_per_tonne_km": float(index + 1),
            }
        )

    # Route B: Short, same weeks
    for index, week in enumerate(dates):
        rows.append(
            {
                "origin": "Delhi",
                "destination": "Jaipur",
                "route_type": "Short",
                "week_of": week,
                "cost_per_tonne_km": float(index + 3),
            }
        )

    # Route C: Medium, same weeks
    for index, week in enumerate(dates):
        rows.append(
            {
                "origin": "Chennai",
                "destination": "Bangalore",
                "route_type": "Medium",
                "week_of": week,
                "cost_per_tonne_km": float(index + 10),
            }
        )

    return pd.DataFrame(rows)


def test_history_excludes_current_week():
    weekly = make_weekly_data()

    result = add_baselines(weekly)

    route_a = result[
        (result["origin"] == "Mumbai")
        & (result["destination"] == "Pune")
    ].sort_values("week_of")

    # The first week has no historical observations.
    assert pd.isna(
        route_a.iloc[0]["own_history_baseline"]
    )

    # Week 2 uses Week 1 only.
    assert route_a.iloc[1]["own_history_baseline"] == pytest.approx(1.0)

    # Week 9 uses Weeks 1 through 8.
    assert route_a.iloc[8]["own_history_baseline"] == pytest.approx(4.5)

    # Week 10 uses Weeks 2 through 9.
    assert route_a.iloc[9]["own_history_baseline"] == pytest.approx(5.5)


def test_peer_baseline_excludes_current_route():
    weekly = make_weekly_data()

    result = add_baselines(weekly)

    week = pd.Timestamp("2024-01-01")

    route_a = result[
        (result["origin"] == "Mumbai")
        & (result["destination"] == "Pune")
        & (result["week_of"] == week)
    ].iloc[0]

    # The other Short route costs 3.0.
    assert route_a["similar_routes_baseline"] == pytest.approx(3.0)


def test_different_route_types_are_not_peers():
    weekly = make_weekly_data()

    result = add_baselines(weekly)

    week = pd.Timestamp("2024-01-01")

    medium_route = result[
        (result["origin"] == "Chennai")
        & (result["destination"] == "Bangalore")
        & (result["week_of"] == week)
    ].iloc[0]

    # No other Medium route exists in this test data.
    assert pd.isna(medium_route["similar_routes_baseline"])
    assert pd.isna(medium_route["vs_similar_routes_pct"])


def test_invalid_history_window_is_rejected():
    with pytest.raises(ValueError, match="at least 1"):
        add_baselines(make_weekly_data(), history_window=0)