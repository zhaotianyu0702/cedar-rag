"""Checks the assignment's scoring contract and actual saved embedding results."""
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest
from corpus import ROOT, QUESTIONS, load_chunks
from keyword_retriever import retrieve, words


class BaselineTests(unittest.TestCase):
    def setUp(self):
        self.chunks = load_chunks()

    def test_six_verbatim_sources(self):
        original = (ROOT / "assignment/ps05-original.txt").read_text()
        self.assertEqual([c.id for c in self.chunks], ["A1", "A2", "B1", "B2", "T1", "T2"])
        for chunk in self.chunks:
            expected = re.search(r"^\[" + chunk.id + r"\] (.+)$", original, re.M).group(1)
            self.assertEqual(chunk.text, expected)

    def test_distinct_words_no_stemming_labels_excluded(self):
        self.assertEqual(words("The LASER laser a A2 student's 19:00"), {"laser", "a2", "student", "s", "19", "00"})
        first, _ = retrieve(self.chunks, "laser")
        repeated, _ = retrieve(self.chunks, "laser laser LASER")
        self.assertEqual(first, repeated)
        self.assertEqual(retrieve(self.chunks, "A1 A2 B1 B2 T1 T2")[1], [])
        self.assertEqual(retrieve(self.chunks, "xyzzy")[1], [])

    def test_q1_manual_score_and_ties(self):
        ranked, selected = retrieve(self.chunks, QUESTIONS["Q1"])
        self.assertEqual([(c.id, s) for c, s, _ in ranked],
                         [("A1", 3), ("A2", 2), ("B1", 1), ("T1", 1), ("T2", 1), ("B2", 0)])
        self.assertEqual(ranked[0][2], ["00", "graduate", "trained"])
        self.assertEqual([c.id for c, _, _ in selected], ["A1", "A2"])

    def test_k_and_positive_only(self):
        self.assertEqual(len(retrieve(self.chunks, "laser", 99)[1]), 3)
        with self.assertRaises(ValueError):
            retrieve(self.chunks, "laser", 0)


class ActualArtifactTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / "evidence/vectors.npz").exists(), "Run experiments first")
    def test_vectors_scores_rankings_and_integrity(self):
        import numpy as np
        out = ROOT / "evidence"
        data = np.load(out / "vectors.npz", allow_pickle=False)
        self.assertEqual(data["documents"].shape, (6, 384))
        self.assertEqual(data["queries"].shape, (4, 384))
        for name in ("documents", "queries"):
            np.testing.assert_allclose(np.linalg.norm(data[name], axis=1), 1, atol=1e-6)
        recomputed = data["queries"] @ data["documents"].T
        np.testing.assert_allclose(data["scores"], recomputed, atol=1e-6)
        rankings = json.loads((out / "rankings.json").read_text())
        with (out / "results-unjudged.csv").open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 4)
        for i, row in enumerate(rows):
            order = sorted(range(6), key=lambda j: (-float(data["scores"][i, j]), data["document_ids"][j]))
            self.assertEqual(row["embedding_top_ids"], ";".join(data["document_ids"][j] for j in order[:2]))
            self.assertEqual([x["id"] for x in rankings[row["question_id"]]["embedding"]],
                             [data["document_ids"][j] for j in order])
            self.assertEqual(row["embedding_evidence_complete"], "")
        self.assertEqual(rows[3]["required_ids"], "absent")
        metadata = json.loads((out / "run-metadata.json").read_text())
        for section, directory in (("source_sha256", ROOT), ("code_sha256", ROOT), ("output_sha256", out)):
            for name, digest in metadata[section].items():
                self.assertEqual(hashlib.sha256((directory / name).read_bytes()).hexdigest(), digest, name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
