from datetime import date

import pandas as pd

from src.evidence_validation import validate_note


OUTPUT_COLUMNS = [
    "route",
    "week_of",
    "cost_per_tonne_km",
    "vs_own_history",
    "vs_similar_routes",
    "flagged",
    "matched_note_id",
    "reason",
]


def format_percentage(value) -> str:
    """Format a percentage for the final report."""
    if pd.isna(value):
        return "N/A"

    return f"{value:+.1f}%"


def build_explanation(
    row: pd.Series,
    candidates: list[dict],
) -> dict:
    """
    Build the final explanation and status for one route-week.

    Candidates are retrieved notes. A note must pass evidence
    validation before it can justify a flagged anomaly.
    """
    route = f"{row['origin']}-{row['destination']}"
    week_of = pd.Timestamp(row["week_of"]).date()

    own_change = row["vs_own_history_pct"]
    peer_change = row["vs_similar_routes_pct"]

    own_text = format_percentage(own_change)
    peer_text = format_percentage(peer_change)

    result = {
        "route": route,
        "week_of": week_of.isoformat(),
        "cost_per_tonne_km": round(
            float(row["cost_per_tonne_km"]), 2
        ),
        "vs_own_history": (
            f"{own_text} vs own history"
            if own_text != "N/A"
            else "N/A"
        ),
        "vs_similar_routes": (
            f"{peer_text} vs similar routes"
            if peer_text != "N/A"
            else "N/A"
        ),
        "flagged": "No",
        "matched_note_id": "",
        "reason": "No unusual cost increase detected.",
    }

    if not bool(row["anomaly_candidate"]):
        return result

    # Validate retrieved candidates in ranking order.
    for candidate in candidates:
        validation = validate_note(
            route=route,
            week_of=week_of,
            candidate=candidate,
        )

        if validation["justified"]:
            result["flagged"] = "No (justified)"
            result["matched_note_id"] = validation["note_id"]
            result["reason"] = (
                f"Cost increase detected: own history {own_text}; "
                f"similar routes {peer_text}. "
                f"Supported by {validation['note_id']}: "
                f"{validation['reason']}"
            )
            return result

    # The anomaly remains flagged if no note sufficiently explains it.
    result["flagged"] = "Yes"
    result["reason"] = (
        f"Unexplained cost increase: own history {own_text}; "
        f"similar routes {peer_text}. "
        "No retrieved context note provided sufficient "
        "route- and time-relevant evidence."
    )

    return result


def build_output(
    anomalies: pd.DataFrame,
    candidates_by_row: dict[int, list[dict]],
) -> pd.DataFrame:
    """Build the final output DataFrame in the required column order."""
    records = []

    for index, row in anomalies.iterrows():
        candidates = candidates_by_row.get(index, [])

        records.append(
            build_explanation(
                row=row,
                candidates=candidates,
            )
        )

    return pd.DataFrame(records, columns=OUTPUT_COLUMNS)