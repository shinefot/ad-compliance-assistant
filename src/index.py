"""
index.py — STEP 2. Builds the RAG search index (LlamaIndex).

Run:  python -m src.index

What happens:
  1. Each AD PDF is split into pages, then into ~500-token chunks.
  2. Each chunk is tagged with metadata: AD number, authority, page number.
  3. A small local model (bge-small) turns each chunk into an "embedding":
     a list of 384 numbers that captures its meaning. Similar meaning = similar numbers.
  4. Chunks + embeddings are saved with LlamaIndex's built-in vector store (folder index_store/).
     (We originally used Chroma, but its dependencies include a native component that
     Windows Smart App Control can block. The built-in store has no such dependencies.)

Later the Analyst asks: "find the chunks of AD 2025-14-07 most related to the
required inspection" and gets back the exact text + page numbers to cite.

The embedding model runs on your laptop for free (downloads ~130 MB the first time).
"""
import hashlib
import os
import shutil
from typing import Any

from llama_index.core import Document, StorageContext, VectorStoreIndex, load_index_from_storage
from llama_index.core.embeddings import BaseEmbedding
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters

from . import config
from .extract import load_records
from .pdf_utils import read_pages

EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


class LocalEmbedding(BaseEmbedding):
    """Wraps the free, local fastembed model so LlamaIndex can use it."""
    _model: Any = None

    def __init__(self, **kwargs):
        super().__init__(model_name=EMBED_MODEL_NAME, **kwargs)
        from fastembed import TextEmbedding
        self._model = TextEmbedding(EMBED_MODEL_NAME)

    def _get_text_embedding(self, text: str) -> list[float]:
        return list(next(iter(self._model.embed([text]))))

    def _get_text_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [list(v) for v in self._model.embed(texts)]

    def _get_query_embedding(self, query: str) -> list[float]:
        # query_embed adds the special prefix bge models expect for search queries
        return list(next(iter(self._model.query_embed(query))))

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)


class HashEmbedding(BaseEmbedding):
    """Offline stand-in used only for automated tests (EMBED_BACKEND=hash). Not for real use."""

    def __init__(self, **kwargs):
        super().__init__(model_name="hash-test", **kwargs)

    @staticmethod
    def _vec(text: str) -> list[float]:
        v = [0.0] * 256
        for w in text.lower().split():
            v[int(hashlib.md5(w.encode()).hexdigest(), 16) % 256] += 1.0
        n = sum(x * x for x in v) ** 0.5 or 1.0
        return [x / n for x in v]

    def _get_text_embedding(self, text): return self._vec(text)
    def _get_query_embedding(self, query): return self._vec(query)
    async def _aget_query_embedding(self, query): return self._vec(query)


def get_embed_model() -> BaseEmbedding:
    if os.getenv("EMBED_BACKEND") == "hash":
        return HashEmbedding()
    return LocalEmbedding()


def build_documents() -> list[Document]:
    docs = []
    for rec in load_records():
        pdf = config.DATA_DIR / rec.source_file
        for page_no, text in read_pages(pdf):
            docs.append(Document(
                text=text,
                metadata={"ad_number": rec.ad_number, "authority": rec.issuing_authority,
                          "page": page_no, "source_file": rec.source_file},
            ))
    for pdf in sorted(config.REGS_DIR.glob("*.pdf")):
        for page_no, text in read_pages(pdf):
            docs.append(Document(text=text, metadata={"ad_number": "REG", "authority": "FAA",
                                                      "page": page_no, "source_file": f"regs/{pdf.name}"}))
    return docs


def build_index() -> VectorStoreIndex:
    docs = build_documents()
    if not docs:
        raise SystemExit("No documents found. Run `python -m src.extract` first.")
    splitter = SentenceSplitter(chunk_size=512, chunk_overlap=64)  # overlap keeps sentences from being cut in half
    nodes = splitter.get_nodes_from_documents(docs)
    index = VectorStoreIndex(nodes, embed_model=get_embed_model())
    if config.INDEX_DIR.exists():
        shutil.rmtree(config.INDEX_DIR)  # start fresh each build
    index.storage_context.persist(persist_dir=str(config.INDEX_DIR))
    print(f"Indexed {len(docs)} pages as {len(nodes)} chunks into {config.INDEX_DIR.name}/")
    return index


def load_index() -> VectorStoreIndex:
    if not config.INDEX_DIR.exists():
        raise SystemExit("No search index found. Run `python -m src.index` first.")
    storage = StorageContext.from_defaults(persist_dir=str(config.INDEX_DIR))
    return load_index_from_storage(storage, embed_model=get_embed_model())


def make_retriever(index: VectorStoreIndex, k: int = 4):
    """Returns a function: (query, ad_number) -> list of {ad_number, page, text}."""
    def retrieve(query: str, ad_number: str) -> list[dict]:
        # The metadata filter means we ONLY search inside the AD we're asking about.
        filters = MetadataFilters(filters=[ExactMatchFilter(key="ad_number", value=ad_number)])
        hits = index.as_retriever(similarity_top_k=k, filters=filters).retrieve(query)
        return [{"ad_number": h.metadata["ad_number"], "page": int(h.metadata["page"]),
                 "text": h.get_content()} for h in hits]
    return retrieve


if __name__ == "__main__":
    build_index()
