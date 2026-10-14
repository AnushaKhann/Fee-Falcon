from pathlib import Path

import pandas as pd

from src.aggregation import aggregate_weekly_costs
from src.baselines import add_baselines
from src.data_loader import load_context_notes, load_shipments
from src.anomaly_detection import detect_anomalies
from src.evidence_validation import validate_note
from src.explanation import OUTPUT_COLUMNS, build_explanation
from src.note_retrieval import NoteRetriever


def run_pipeline(
    shipments_path: str | Path = "data/shipment_records.csv",
    notes_path: str | Path = "data/context_notes.csv",
    output_path: str | Path = "outputs/results.csv",
    chroma_path: str | Path = "chroma_db",
    history_window: int = 8,
) -> pd.DataFrame:
    """
    Run the complete freight-cost anomaly detection pipeline.

    Steps:
        1. Load and validate input data.
        2. Aggregate shipments into weekly route costs.
        3. Calculate historical and peer baselines.
        4. Detect anomalous route-weeks.
        5. Retrieve and validate contextual evidence.
        6. Generate and save the final CSV.
    """
    # 1. Load the source datasets.
    shipments = load_shipments(shipments_path)
    notes = load_context_notes(notes_path)

    # 2. Calculate weekly route costs.
    weekly = aggregate_weekly_costs(shipments)

    # 3. Add historical and peer baselines.
    weekly_with_baselines = add_baselines(
        weekly,
        history_window=history_window,
    )

    # 4. Identify unusual cost increases.
    anomalies = detect_anomalies(weekly_with_baselines)

    # 5. Retrieve candidate notes for flagged route-weeks only.
    retriever = NoteRetriever(
        notes=notes,
        persist_directory=chroma_path,
    )

    records = []

    for _, row in anomalies.iterrows():
        candidates = []

        if bool(row["anomaly_candidate"]):
            route = f"{row['origin']}-{row['destination']}"
            week_of = pd.Timestamp(row["week_of"]).date()

            query = (
                f"Explain an unusual freight transportation cost "
                f"increase on route {route} during the week of "
                f"{week_of.isoformat()}. Look for documented events "
                f"that could increase freight costs."
            )

            # Retrieve several candidates. Retrieval itself does not
            # determine whether the anomaly is justified.
            candidates = retriever.retrieve(
                query=query,
                top_k=len(notes),
            )

            # Keep only candidates that pass deterministic validation.
            valid_candidates = []

            for candidate in candidates:
                validation = validate_note(
                    route=route,
                    week_of=week_of,
                    candidate=candidate,
                )

                if validation["justified"]:
                    valid_candidates.append(
                        (candidate, validation)
                    )

            # Preserve retrieval ranking among valid candidates.
            candidates = [
                candidate
                for candidate, _ in valid_candidates
            ]

        # 6. Generate the final row.
        records.append(
            build_explanation(
                row=row,
                candidates=candidates,
            )
        )

    result = pd.DataFrame(
        records,
        columns=OUTPUT_COLUMNS,
    )

    # 7. Save a valid CSV with the required column order.
    output_file = Path(output_path)
    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        output_file,
        index=False,
    )

    print(f"Shipments loaded: {len(shipments)}")
    print(f"Context notes loaded: {len(notes)}")
    print(f"Weekly route records: {len(weekly)}")
    print(
        "Anomaly candidates: "
        f"{int(anomalies['anomaly_candidate'].sum())}"
    )
    print(
        "Justified anomalies: "
        f"{int((result['flagged'] == 'No (justified)').sum())}"
    )
    print(
        "Unexplained anomalies: "
        f"{int((result['flagged'] == 'Yes').sum())}"
    )
    print(f"Output saved to: {output_file}")

    return result