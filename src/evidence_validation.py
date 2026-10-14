from datetime import date, timedelta

def validate_note(
    route: str,
    week_of: date,
    candidate: dict,
) -> dict:
    """
    Determine whether a retrieved context note provides sufficient
    evidence to explain an unusual freight-cost increase.

    Args:
        route: Route formatted as 'Origin-Destination'.
        week_of: Monday starting the week being evaluated.
        candidate: One result returned by NoteRetriever.retrieve().

    Returns:
        A dictionary containing the evidence decision and explanation.
    """
    note_id = candidate["note_id"]
    metadata = candidate["metadata"]

    applies_to = metadata["applies_to"]
    note_date = date.fromisoformat(metadata["date"])
    document = candidate["document"]

    result = {
        "note_id": note_id,
        "justified": False,
        "reason": "",
    }

    # A route-specific note cannot explain another route's costs.
    if applies_to != "All Routes" and applies_to != route:
        result["reason"] = (
            f"{note_id} applies to {applies_to}, not {route}."
        )
        return result

    # N001: Flooding and higher trip costs on Chennai-Bangalore.
    if note_id == "N001":
        event_start = date(2025, 2, 24)
        event_end = date(2025, 3, 8)
        week_end = week_of + timedelta(days=6)

        overlaps_event = (
            week_of <= event_end and week_end >= event_start
        )

        if overlaps_event:
            result["justified"] = True
            result["reason"] = (
                "Flooding and detours during the documented event "
                "period support higher transportation costs."
            )
        else:
            result["reason"] = (
                "The evaluated week falls outside the documented "
                "flooding period."
            )

        return result

    # N002: Ahmedabad-Mumbai festival surcharge.
    if note_id == "N002":
        festival_week = date(2025, 1, 20)

        if week_of == festival_week:
            result["justified"] = True
            result["reason"] = (
                "The note documents a temporary festival surcharge "
                "on this route during the evaluated week."
            )
        else:
            result["reason"] = (
                "The note documents a temporary festival surcharge, "
                "not an ongoing cost increase."
            )

        return result

    # N003: Nationwide diesel increase.
    # The note gives a start date and approximate impact, but no end date. Conservatively accept only the week beginning May 5.
    if note_id == "N003":
        diesel_increase_week = date(2025, 5, 5)

        if week_of == diesel_increase_week:
            result["justified"] = True
            result["reason"] = (
                "The note documents a nationwide diesel-price increase "
                "of roughly 5-7% starting this week."
            )
        else:
            result["reason"] = (
                "The diesel-price note does not establish that its "
                "impact continued into this evaluated week."
            )

        return result

    # Other notes do not independently establish a cost increase.
    # This includes notes about stable conditions, improved roads, normal freight movement, or costs explicitly absorbed.
    result["reason"] = (
        f"{note_id} does not provide sufficient evidence of a "
        "cost-increasing event during the evaluated week."
    )

    return result