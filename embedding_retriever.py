"""Real CPU embeddings; the document matrix is computed once per Retriever."""
import argparse
import importlib.metadata
import json
import os
import platform
from corpus import ROOT, load_chunks, positive_k

# Keep cache writes inside this project; never use or transmit a stored HF token.
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


class Retriever:
    def __init__(self, chunks, offline=False):
        import numpy as np
        import torch
        from sentence_transformers import SentenceTransformer
        self.np = np
        self.chunks = chunks
        torch.manual_seed(0)
        torch.set_num_threads(1)
        revision_file = ROOT / "model-revision.txt"
        revision = revision_file.read_text().strip() if revision_file.exists() else None
        self.model = SentenceTransformer(
            MODEL_NAME, device="cpu", revision=revision,
            local_files_only=offline, token=False, trust_remote_code=False,
        )
        self.documents = self.model.encode_document(
            [chunk.text for chunk in chunks], normalize_embeddings=True,
            convert_to_numpy=True, show_progress_bar=False,
        )
        assert self.documents.shape == (6, 384), self.documents.shape
        assert np.allclose(np.linalg.norm(self.documents, axis=1), 1, atol=1e-6)
        self.versions = {name: importlib.metadata.version(name) for name in (
            "sentence-transformers", "numpy", "torch", "transformers", "huggingface-hub")}
        self.metadata = {"model": MODEL_NAME, "requested_revision": revision,
                         "loaded_revision": getattr(self.model[0].auto_model.config, "_commit_hash", None),
                         "device": str(self.model.device), "python": platform.python_version(),
                         "platform": platform.platform(), "versions": self.versions,
                         "dtype": str(self.documents.dtype), "torch_threads": torch.get_num_threads()}

    def inspect_documents(self):
        np = self.np
        print(json.dumps(self.metadata, indent=2))
        print("Document matrix shape:", self.documents.shape)
        print("All 384 coordinates are used; only the first 12 are displayed.")
        print("IDs and filenames are metadata only, excluded from encoded text.")
        for chunk, vector in zip(self.chunks, self.documents):
            print(f"{chunk.id}: [{', '.join(f'{x:.4f}' for x in vector[:12])}]")
            print(f"{chunk.id} length={np.linalg.norm(vector):.9f}")
        print("Document lengths approximately 1: PASS (atol=1e-6)")

    def query(self, question):
        np = self.np
        vector = self.model.encode_query(
            question, normalize_embeddings=True, convert_to_numpy=True,
            show_progress_bar=False,
        )
        assert vector.shape == (384,), vector.shape
        assert np.isclose(np.linalg.norm(vector), 1, atol=1e-6)
        scores = self.documents @ vector
        cosine = scores / (np.linalg.norm(self.documents, axis=1) * np.linalg.norm(vector))
        assert np.allclose(scores, cosine, atol=1e-6, rtol=0)
        order = sorted(range(len(self.chunks)), key=lambda i: (-float(scores[i]), self.chunks[i].id))
        return {"question": question, "vector": vector, "scores": scores,
                "cosine": cosine, "order": order}

    def selected(self, result, k):
        if k < 1:
            raise ValueError("k must be positive")
        return [(self.chunks[i], float(result["scores"][i])) for i in result["order"][:k]]

    def print_result(self, result, k=2, products=False):
        np, vector = self.np, result["vector"]
        print(f"EMBEDDING question={result['question']!r} k={k}")
        print("Question vector shape:", vector.shape)
        print("Question first 12: [" + ", ".join(f"{x:.4f}" for x in vector[:12]) + "]")
        print(f"Question length={np.linalg.norm(vector):.9f}; approximately 1: PASS")
        print("All six similarities (full precision calculation; rounded display):")
        for i in result["order"]:
            print(f"{self.chunks[i].id} dot={result['scores'][i]:.9f} direct_cosine={result['cosine'][i]:.9f}")
        print("Dot and direct cosine agree: PASS (atol=1e-6, rtol=0)")
        selected = self.selected(result, k)
        print("Selected:", ", ".join(chunk.id for chunk, _ in selected))
        for chunk, score in selected:
            print(f"[{chunk.id}] {chunk.filename} score={score:.9f}\n{chunk.text}")
        if products:
            top = result["order"][0]
            product = vector * self.documents[top]
            print("Q1 coordinate products with top passage:", self.chunks[top].id)
            print("First 12 products: [" + ", ".join(f"{x:.9f}" for x in product[:12]) + "]")
            first = product[:12].sum(dtype=np.float64)
            rest = product[12:].sum(dtype=np.float64)
            print(f"First 12 subtotal={first:.12f}; remaining 372 subtotal={rest:.12f}")
            print(f"Full product sum={first + rest:.12f}; full dot={result['scores'][top]:.12f}")
            assert np.isclose(first + rest, result["scores"][top], atol=1e-6, rtol=0)
            displayed = [(chunk.id, j + 1, float(v)) for chunk, doc in zip(self.chunks, self.documents)
                         for j, v in enumerate(doc[:12])]
            displayed += [("Q1", j + 1, float(v)) for j, v in enumerate(vector[:12])]
            print("Smallest displayed coordinate (one-based):", min(displayed, key=lambda x: x[2]))
            print("Largest displayed coordinate (one-based):", max(displayed, key=lambda x: x[2]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("-k", "--k", type=positive_k, default=2)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--products", action="store_true", help="Q1 product inspection")
    args = parser.parse_args()
    retriever = Retriever(load_chunks(), offline=args.offline)
    retriever.inspect_documents()
    retriever.print_result(retriever.query(args.question), args.k, products=args.products)


if __name__ == "__main__":
    main()
