import pandas as pd

from src.anomaly_detection import detect_anomalies


def make_test_data():
    return pd.DataFrame(
        [
            {
                "origin": "Mumbai",
                "destination": "Pune",
                "route_type": "Short",
                "week_of": "2025-01-06",
                "cost_per_tonne_km": 3.0,
                "own_history_baseline": 2.5,
                "similar_routes_baseline": 2.0,
                "vs_own_history_pct": 20.0,
                "vs_similar_routes_pct": 50.0,
            },
            {
                "origin": "Delhi",
                "destination": "Jaipur",
                "route_type": "Short",
                "week_of": "2025-01-06",
                "cost_per_tonne_km": 2.1,
                "own_history_baseline": 2.0,
                "similar_routes_baseline": 2.0,
                "vs_own_history_pct": 5.0,
                "vs_similar_routes_pct": 5.0,
            },
            {
                "origin": "Chennai",
                "destination": "Bangalore",
                "route_type": "Medium",
                "week_of": "2025-01-06",
                "cost_per_tonne_km": 2.5,
                "own_history_baseline": 2.0,
                "similar_routes_baseline": float("nan"),
                "vs_own_history_pct": 25.0,
                "vs_similar_routes_pct": float("nan"),
            },
        ]
    )


def test_detects_anomaly_from_peer_comparison():
    result = detect_anomalies(make_test_data())

    mumbai_pune = result[
        result["origin"] == "Mumbai"
    ].iloc[0]

    assert mumbai_pune["anomaly_candidate"]
    assert mumbai_pune["history_trigger"]
    assert mumbai_pune["peer_trigger"]


def test_ordinary_increase_is_not_flagged():
    result = detect_anomalies(make_test_data())

    delhi_jaipur = result[
        result["origin"] == "Delhi"
    ].iloc[0]

    assert not delhi_jaipur["anomaly_candidate"]


def test_missing_peer_baseline_does_not_trigger_flag():
    result = detect_anomalies(make_test_data())

    chennai_bangalore = result[
        result["origin"] == "Chennai"
    ].iloc[0]

    assert chennai_bangalore["history_trigger"]
    assert not chennai_bangalore["peer_trigger"]
    assert chennai_bangalore["anomaly_candidate"]