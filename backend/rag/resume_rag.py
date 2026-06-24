"""
Resume RAG (Retrieval Augmented Generation).
Embeds resume chunks into ChromaDB vector store.
Retrieves relevant resume context for any interview question.
"""

import chromadb
from pathlib import Path
from chromadb.utils import embedding_functions
from backend.rag.resume_loader import ResumeLoader
from backend.utils.logger import get_logger

logger = get_logger(__name__)

# ChromaDB storage path
CHROMA_PATH = Path(__file__).resolve().parents[2] / "database" / "chroma"


class ResumeRAG:
    """
    Stores resume as vector embeddings and retrieves
    relevant sections when answering interview questions.

    Usage:
        rag = ResumeRAG()
        rag.load_resume("resume.pdf")
        context = rag.get_context("Tell me about your projects")
    """

    COLLECTION_NAME = "resume"

    def __init__(self):
        CHROMA_PATH.mkdir(parents=True, exist_ok=True)

        # Local ChromaDB — no internet needed
        self._client = chromadb.PersistentClient(path=str(CHROMA_PATH))

        # Use sentence-transformers for embeddings — runs fully offline
        self._embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self._collection = self._client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            embedding_function=self._embed_fn
        )

        self._loader = ResumeLoader()
        self._resume_loaded = False

        logger.info("ResumeRAG initialized")

    def load_resume(self, pdf_path: str) -> int:
        """
        Load a resume PDF into the vector store.
        Returns number of chunks stored.
        """
        chunks = self._loader.load(pdf_path)

        # Clear existing resume data
        try:
            self._client.delete_collection(self.COLLECTION_NAME)
            self._collection = self._client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=self._embed_fn
            )
        except Exception:
            pass

        # Store chunks with unique IDs
        ids = [f"chunk_{i}" for i in range(len(chunks))]
        self._collection.add(
            documents=chunks,
            ids=ids
        )

        self._resume_loaded = True
        logger.info(f"Resume indexed | {len(chunks)} chunks stored")
        return len(chunks)

    def get_context(self, question: str, top_k: int = 3) -> str:
        """
        Retrieve the most relevant resume sections for a question.
        Returns formatted context string to inject into LLM prompt.
        """
        if not self._resume_loaded and self._collection.count() == 0:
            return ""

        try:
            results = self._collection.query(
                query_texts=[question],
                n_results=min(top_k, self._collection.count())
            )

            docs = results.get("documents", [[]])[0]
            if not docs:
                return ""

            context_lines = ["Candidate's resume context:"]
            for doc in docs:
                context_lines.append(f"- {doc.strip()}")

            context = "\n".join(context_lines)
            logger.debug(f"RAG retrieved {len(docs)} chunks for: {question[:50]}")
            return context

        except Exception as e:
            logger.error(f"RAG query error: {e}")
            return ""

    def is_loaded(self) -> bool:
        return self._resume_loaded or self._collection.count() > 0