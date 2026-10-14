from src.data_loader import load_context_notes
from src.note_retrieval import NoteRetriever


def main():
    notes = load_context_notes("data/context_notes.csv")

    retriever = NoteRetriever(
        notes=notes,
        persist_directory="chroma_db",
    )

    queries = [
        (
            "Chennai-Bangalore",
            "Flooding and detours increased transportation "
            "costs on Chennai-Bangalore in February 2025.",
        ),
        (
            "Ahmedabad-Mumbai",
            "A regional festival caused a temporary "
            "transportation surcharge on Ahmedabad-Mumbai "
            "in January 2025.",
        ),
        (
            "Mumbai-Pune",
            "Find documented events that could explain "
            "an unusual freight cost increase on Mumbai-Pune "
            "in September 2025.",
        ),
    ]

    for route, query in queries:
        print("\n" + "=" * 70)
        print("Route:", route)
        print("Query:", query)
        print("=" * 70)

        candidates = retriever.retrieve(
            query=query,
            top_k=5,
        )

        for rank, candidate in enumerate(candidates, start=1):
            metadata = candidate["metadata"]

            print(
                f"\n{rank}. Note ID: {metadata['note_id']}"
            )
            print("   Applies to:", metadata["applies_to"])
            print("   Date:", metadata["date"])
            print("   Distance:", round(candidate["distance"], 4))
            print("   Text:", candidate["document"])

    print("\nRetrieval test completed.")


if __name__ == "__main__":
    main()