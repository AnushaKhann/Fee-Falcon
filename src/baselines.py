import pandas as pd


ROUTE_COLUMNS = [
    "origin",
    "destination",
    "route_type",
]

BASELINE_COLUMNS = [
    "own_history_baseline",
    "similar_routes_baseline",
    "vs_own_history_pct",
    "vs_similar_routes_pct",
]


def add_baselines(
    weekly: pd.DataFrame,
    history_window: int = 8,
) -> pd.DataFrame:
    """
    Add historical and peer-route baselines to weekly route costs.

    Historical baseline:
        Mean of the preceding `history_window` weekly observations,
        excluding the current week.

    Peer baseline:
        Mean cost for other routes with the same route_type
        during the same week.

    Percentage differences:
        (current cost / baseline - 1) * 100

    If no historical observation or eligible peer route exists,
    the corresponding baseline and percentage difference are NaN.
    """
    required_columns = {
        *ROUTE_COLUMNS,
        "week_of",
        "cost_per_tonne_km",
    }

    missing = required_columns - set(weekly.columns)

    if missing:
        raise ValueError(
            f"Weekly data is missing columns: {sorted(missing)}"
        )

    if weekly.empty:
        raise ValueError("Cannot calculate baselines on empty data.")

    if history_window < 1:
        raise ValueError("history_window must be at least 1.")

    df = weekly.copy()

    df["week_of"] = pd.to_datetime(
        df["week_of"],
        errors="raise",
    )

    if df["cost_per_tonne_km"].isna().any():
        raise ValueError("Weekly costs contain missing values.")

    if not df["cost_per_tonne_km"].map(
        lambda value: pd.notna(value) and abs(value) != float("inf")
    ).all():
        raise ValueError("Weekly costs must be finite.")

    if (df["cost_per_tonne_km"] < 0).any():
        raise ValueError("Weekly costs cannot be negative.")

    if df.duplicated(ROUTE_COLUMNS + ["week_of"]).any():
        raise ValueError("Duplicate route-week records found.")

    df = df.sort_values(
        ROUTE_COLUMNS + ["week_of"],
        kind="stable",
    ).reset_index(drop=True)

    # 1. Historical baseline: prior observations only.
    df["own_history_baseline"] = (
        df.groupby(ROUTE_COLUMNS, sort=False)["cost_per_tonne_km"]
        .transform(
            lambda series: (
                series.shift(1)
                .rolling(
                    window=history_window,
                    min_periods=1,
                )
                .mean()
            )
        )
    )

    # 2. Peer baseline: same week and route type, excluding the current route from its own peer average.
    peer_groups = df.groupby(
        ["week_of", "route_type"],
        sort=False,
    )["cost_per_tonne_km"]

    peer_total = peer_groups.transform("sum")
    peer_count = peer_groups.transform("count")

    eligible_peer_count = peer_count - 1

    df["similar_routes_baseline"] = (
        (peer_total - df["cost_per_tonne_km"])
        / eligible_peer_count.where(eligible_peer_count > 0)
    )

    # 3. Percentage differences against each baseline.
    df["vs_own_history_pct"] = (
        (
            df["cost_per_tonne_km"]
            / df["own_history_baseline"]
        ) - 1
    ) * 100

    df["vs_similar_routes_pct"] = (
        (
            df["cost_per_tonne_km"]
            / df["similar_routes_baseline"]
        ) - 1
    ) * 100

    # A zero baseline makes a percentage comparison undefined.
    df.loc[
        df["own_history_baseline"] == 0,
        "vs_own_history_pct",
    ] = float("nan")

    df.loc[
        df["similar_routes_baseline"] == 0,
        "vs_similar_routes_pct",
    ] = float("nan")

    return df