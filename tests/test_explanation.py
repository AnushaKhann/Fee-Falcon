import pandas as pd

from src.explanation import build_explanation


def make_row(
    anomaly_candidate=True,
    own_change=30.0,
    peer_change=25.0,
):
    return pd.Series({
        "origin": "Chennai",
        "destination": "Bangalore",
        "week_of": "2025-02-24",
        "cost_per_tonne_km": 3.58,
        "vs_own_history_pct": own_change,
        "vs_similar_routes_pct": peer_change,
        "anomaly_candidate": anomaly_candidate,
    })


def make_candidate(
    note_id,
    applies_to,
    note_date,
    document="Example note",
):
    return {
        "note_id": note_id,
        "document": document,
        "metadata": {
            "note_id": note_id,
            "applies_to": applies_to,
            "date": note_date,
        },
        "distance": 0.2,
    }


def test_supported_anomaly_is_marked_justified():
    row = make_row()

    candidate = make_candidate(
        "N001",
        "Chennai-Bangalore",
        "2025-02-24",
    )

    result = build_explanation(row, [candidate])

    assert result["flagged"] == "No (justified)"
    assert result["matched_note_id"] == "N001"


def test_unsupported_anomaly_remains_flagged():
    row = make_row()

    candidate = make_candidate(
        "N006",
        "All Routes",
        "2025-09-22",
        document=(
            "Demand remained stable with no major disruptions."
        ),
    )

    result = build_explanation(row, [candidate])

    assert result["flagged"] == "Yes"
    assert result["matched_note_id"] == ""


def test_non_anomaly_is_not_flagged():
    row = make_row(anomaly_candidate=False)

    result = build_explanation(row, [])

    assert result["flagged"] == "No"
    assert result["matched_note_id"] == ""


def test_wrong_route_note_does_not_justify_anomaly():
    row = make_row()

    candidate = make_candidate(
        "N002",
        "Ahmedabad-Mumbai",
        "2025-01-20",
    )

    result = build_explanation(row, [candidate])

    assert result["flagged"] == "Yes"
    assert result["matched_note_id"] == ""


def test_missing_baselines_are_formatted_safely():
    row = make_row(
        own_change=float("nan"),
        peer_change=float("nan"),
    )

    result = build_explanation(row, [])

    assert result["vs_own_history"] == "N/A"
    assert result["vs_similar_routes"] == "N/A"