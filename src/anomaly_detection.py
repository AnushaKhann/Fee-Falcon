import pandas as pd

from src.config import (
    OWN_HISTORY_THRESHOLD_PCT,
    SIMILAR_ROUTES_THRESHOLD_PCT,
)


def detect_anomalies(
    weekly_with_baselines: pd.DataFrame,
) -> pd.DataFrame:
    """
    Identify route-weeks with unusually high costs.

    A route-week becomes an anomaly candidate when its cost is
    at least the configured threshold above either available baseline.

    This function does not decide whether the anomaly is justified
    by contextual evidence. That decision belongs to a later stage.
    """
    required_columns = {
        "origin",
        "destination",
        "route_type",
        "week_of",
        "cost_per_tonne_km",
        "own_history_baseline",
        "similar_routes_baseline",
        "vs_own_history_pct",
        "vs_similar_routes_pct",
    }

    missing = required_columns - set(weekly_with_baselines.columns)

    if missing:
        raise ValueError(
            f"Input is missing columns: {sorted(missing)}"
        )

    df = weekly_with_baselines.copy()

    if df.empty:
        raise ValueError("Cannot detect anomalies in empty data.")

    history_trigger = (
        df["vs_own_history_pct"]
        >= OWN_HISTORY_THRESHOLD_PCT
    ).fillna(False)

    peer_trigger = (
        df["vs_similar_routes_pct"]
        >= SIMILAR_ROUTES_THRESHOLD_PCT
    ).fillna(False)

    df["history_trigger"] = history_trigger
    df["peer_trigger"] = peer_trigger

    df["anomaly_candidate"] = (
        history_trigger | peer_trigger
    )

    def describe_trigger(row):
        reasons = []

        if row["history_trigger"]:
            reasons.append("own history")

        if row["peer_trigger"]:
            reasons.append("similar routes")

        return ", ".join(reasons)

    df["anomaly_trigger"] = df.apply(
        describe_trigger,
        axis=1,
    )

    return df