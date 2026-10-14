from pathlib import Path

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_COLLECTION = "freight_context_notes"


class NoteRetriever:
    """
    Retrieve potentially relevant freight context notes using
    Sentence Transformers embeddings and ChromaDB.

    Retrieval identifies candidates; it does not establish
    whether a note justifies a cost increase.
    """

    def __init__(
        self,
        notes: pd.DataFrame,
        persist_directory: str | Path = "chroma_db",
        model_name: str = DEFAULT_MODEL,
    ):
        required_columns = {
            "note_id",
            "date",
            "applies_to",
            "note",
        }

        missing = required_columns - set(notes.columns)

        if missing:
            raise ValueError(
                f"Notes are missing columns: {sorted(missing)}"
            )

        if notes.empty:
            raise ValueError("Cannot index an empty notes dataset.")

        self.notes = notes.copy()

        self.notes["date"] = pd.to_datetime(
            self.notes["date"],
            errors="raise",
        )

        self.model = SentenceTransformer(model_name)

        self.client = chromadb.PersistentClient(
            path=str(persist_directory)
        )

        self.collection = self.client.get_or_create_collection(
            name=DEFAULT_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

        self._index_notes()

    def _index_notes(self) -> None:
        """Index the supplied notes in ChromaDB."""
        ids = self.notes["note_id"].astype(str).tolist()

        documents = (
            self.notes["applies_to"].astype(str)
            + " | "
            + self.notes["date"].dt.strftime("%Y-%m-%d")
            + " | "
            + self.notes["note"].astype(str)
        ).tolist()

        metadata = [
            {
                "note_id": str(row.note_id),
                "date": row.date.strftime("%Y-%m-%d"),
                "applies_to": str(row.applies_to),
            }
            for row in self.notes.itertuples(index=False)
        ]

        embeddings = self.model.encode(
            documents,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        # Upsert makes rerunning the indexing process idempotent for the supplied note IDs.
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadata,
            embeddings=embeddings,
        )

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Return the top-k semantically similar notes.

        Results are candidates only. Callers must validate
        route applicability, dates, and supporting evidence.
        """
        if not query.strip():
            raise ValueError("Retrieval query cannot be empty.")

        if top_k < 1:
            raise ValueError("top_k must be at least 1.")

        query_embedding = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).tolist()

        result = self.collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        candidates = []

        for index, note_id in enumerate(result["ids"][0]):
            candidates.append(
                {
                    "note_id": note_id,
                    "document": result["documents"][0][index],
                    "metadata": result["metadatas"][0][index],
                    "distance": result["distances"][0][index],
                }
            )

        return candidates