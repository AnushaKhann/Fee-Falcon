from datetime import date

from src.evidence_validation import validate_note


def make_candidate(
    note_id,
    applies_to,
    note_date,
    document="Example context note",
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


def test_chennai_bangalore_flooding_is_justified():
    candidate = make_candidate(
        "N001",
        "Chennai-Bangalore",
        "2025-02-24",
    )

    result = validate_note(
        route="Chennai-Bangalore",
        week_of=date(2025, 2, 24),
        candidate=candidate,
    )

    assert result["justified"] is True


def test_flood_note_does_not_justify_later_week():
    candidate = make_candidate(
        "N001",
        "Chennai-Bangalore",
        "2025-02-24",
    )

    result = validate_note(
        route="Chennai-Bangalore",
        week_of=date(2025, 3, 17),
        candidate=candidate,
    )

    assert result["justified"] is False


def test_festival_surcharge_is_justified():
    candidate = make_candidate(
        "N002",
        "Ahmedabad-Mumbai",
        "2025-01-20",
    )

    result = validate_note(
        route="Ahmedabad-Mumbai",
        week_of=date(2025, 1, 20),
        candidate=candidate,
    )

    assert result["justified"] is True


def test_wrong_route_is_rejected():
    candidate = make_candidate(
        "N002",
        "Ahmedabad-Mumbai",
        "2025-01-20",
    )

    result = validate_note(
        route="Mumbai-Pune",
        week_of=date(2025, 1, 20),
        candidate=candidate,
    )

    assert result["justified"] is False


def test_stable_demand_does_not_justify_increase():
    candidate = make_candidate(
        "N006",
        "All Routes",
        "2025-09-22",
        document=(
            "All Routes | 2025-09-22 | A logistics industry report "
            "noted overall demand for freight capacity remained "
            "stable this quarter with no major disruptions reported."
        ),
    )

    result = validate_note(
        route="Mumbai-Pune",
        week_of=date(2025, 9, 15),
        candidate=candidate,
    )

    assert result["justified"] is False


def test_diesel_note_only_justifies_starting_week():
    candidate = make_candidate(
        "N003",
        "All Routes",
        "2025-05-05",
    )

    result = validate_note(
        route="Mumbai-Pune",
        week_of=date(2025, 5, 5),
        candidate=candidate,
    )

    assert result["justified"] is True

    later_result = validate_note(
        route="Mumbai-Pune",
        week_of=date(2025, 9, 15),
        candidate=candidate,
    )

    assert later_result["justified"] is False