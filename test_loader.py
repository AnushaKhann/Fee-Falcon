from src.data_loader import load_context_notes, load_shipments


def main():
    shipments = load_shipments("data/shipment_records.csv")
    notes = load_context_notes("data/context_notes.csv")

    print("Shipment validation passed.")
    print("Shipment records:", len(shipments))
    print("Shipment date range:")
    print(shipments["shipment_date"].min(), "to",
          shipments["shipment_date"].max())

    print("\nContext-note validation passed.")
    print("Number of notes:", len(notes))
    print("Note IDs:", notes["note_id"].tolist())

    print("\nRoute types:")
    print(shipments["route_type"].value_counts().to_string())


if __name__ == "__main__":
    main()