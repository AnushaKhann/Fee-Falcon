import pandas as pd
import pytest

OUTPUT_PATH = "outputs/results.csv"


@pytest.fixture(scope="module")
def results():
    return pd.read_csv(OUTPUT_PATH)


@pytest.mark.parametrize(
    "route,week,expected_flag,expected_note",
    [
        (
            "Ahmedabad-Mumbai",
            "2025-01-20",
            "No (justified)",
            "N002",
        ),
        (
            "Chennai-Bangalore",
            "2025-02-24",
            "No (justified)",
            "N001",
        ),
        (
            "Chennai-Bangalore",
            "2025-03-03",
            "No (justified)",
            "N001",
        ),
        (
            "Chennai-Bangalore",
            "2025-03-10",
            "Yes",
            None,
        ),
        (
            "Mumbai-Pune",
            "2025-09-15",
            "Yes",
            None,
        ),
    ],
)
def test_expected_real_data_cases(
    results,
    route,
    week,
    expected_flag,
    expected_note,
):
    matches = results[
        (results["route"] == route)
        & (results["week_of"] == week)
    ]

    assert len(matches) == 1

    row = matches.iloc[0]

    assert row["flagged"] == expected_flag

    if expected_note is None:
        assert pd.isna(row["matched_note_id"])
    else:
        assert row["matched_note_id"] == expected_note