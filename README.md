# Cedar Lab RAG — MIT 1.125 PS05

A small, local teaching project comparing exact word overlap with real
`sentence-transformers/all-MiniLM-L6-v2` CPU embeddings. The corpus contains the
six fictional Cedar Lab paragraphs verbatim. This is classroom material, not
operational safety guidance.

**Status:** implementation and local experiments completed on 2026-10-21.
The Q1–Q4 retrieval judgments and Q1/Q4 answer audits have been reviewed.
The user-provided reflection is stored verbatim in `REFLECTION_TODO.txt` (141 words).

Student name: **Tianyu Zhao**  
Working arrangement: **Worked individually; no partner.**

The [assignment](https://docs.google.com/document/d/1EIb-8b-DZx9Ir_Yk3yfA1D6gAtMta1vtQMmclskoXPg/edit)
says **Due 10/22 5pm**. The course page is for Fall 2026. The handout does not
specify a timezone; do not treat a Boston-time interpretation as confirmed.
Its full fetched text and source metadata are saved under `assignment/`; embedded
screenshots are not included in the text export.

## Start on this Mac

```sh
cd cedar-rag
.venv/bin/python keyword_retriever.py 'May a trained graduate student operate the laser alone at 19:00?' -k 2
HF_HUB_OFFLINE=1 .venv/bin/python embedding_retriever.py 'May a trained graduate student operate the laser alone at 19:00?' -k 2 --products --offline
.venv/bin/python -m unittest -v test_retrieval.py
```

The existing `.venv` and model cache are ready. No API key or GPU is needed.
The keyword retriever also runs with system `python3` and only the standard library.
`-k`/`--k` defaults to 2 and must be a positive integer. Keyword retrieval selects
only positive scores; embedding retrieval always selects up to k chunks, even
when none can answer. k above 6 cannot return more than the six available chunks.

To repeat all four questions, vector inspection and the Q1 k experiment without
overwriting the original evidence, choose a new output directory:

```sh
HF_HUB_OFFLINE=1 .venv/bin/python run_experiments.py --offline --output-dir evidence/rerun-01
```

The runner refuses to overwrite existing experiment artifacts. Its generated
`results-unjudged.csv` intentionally leaves both judgment fields and observations
blank. In the root `results.csv`, **Q1–Q4 retrieval judgments are student-confirmed**.
Both Q1/Q4 answer audits are student-confirmed. For vector review, the student agreed with the matrix/compatible-space explanation after reading it; extrema were program-verified and shown, not independently found by the student. The user-provided reflection text has been inserted verbatim.

## Recreate the environment

On this Mac, Python 3.13.5 was already installed at `/opt/anaconda3/bin/python3.13`.
The project virtual environment was created with `uv`; no system packages were
changed. On another machine use a compatible Python installation:

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python run_experiments.py --output-dir evidence/fresh-install-01
```

The first model load needs internet access to download public weights. Subsequent
runs can use `HF_HUB_OFFLINE=1` and `--offline`. If `uv` is preferred, an equivalent
install command is:

```sh
UV_CACHE_DIR=/tmp/cedar-rag-uv-cache uv pip install --python .venv/bin/python -r requirements-lock.txt
```

The exact package lock is from this macOS arm64 environment; another platform may
need compatible wheels. `requirements.txt` contains the broader direct requirements.

| Component | Actual version / setting |
|---|---|
| Python | 3.13.5 |
| sentence-transformers | 5.7.0 |
| numpy | 2.5.4 |
| torch | 2.14.1 |
| transformers | 5.20.2 |
| huggingface-hub | 2.2.0 |
| Execution | CPU, float32 vectors, one Torch thread |
| Model revision | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |

`model-revision.txt` pins the download. The library's config reported
`_commit_hash=null`; that fact is preserved, not replaced with a guessed loaded
value. `evidence/model-cache-manifest.json` records the actual pinned snapshot's
files and SHA-256 hashes, and a successful fully offline run verifies cache use.
The public Hugging Face download used no authentication token. Model weights and
the environment are ignored by Git, not bundled as submission artifacts.

## What the code does

1. **Load.** `corpus.py:16` reads exactly the three named files. It separates each
   `[ID]` from its body, retains filename metadata, verifies the expected IDs,
   and sorts six chunks by ID. `keyword_retriever.py:45` calls the loader.
2. **Score words.** `keyword_retriever.py:9` lowercases and extracts alphanumeric
   tokens, converts to a set, and removes exactly the handout's 17 stopwords.
   Lines 19–20 intersect question words with each chunk's words and count distinct
   matches. No stemming or synonyms are added.
3. **Rank words.** `keyword_retriever.py:21` sorts by descending score and ascending
   ID; line 22 takes up to k positive results. All six scores and matched words
   are printed, followed by full selected text or `No matching passages.`
4. **Encode.** `embedding_retriever.py:29` loads the pinned model on CPU.
   Line 33 calls `encode_document` once for the six bodies with normalization and
   NumPy output enabled. Line 60 calls `encode_query` for each question with the
   same settings. IDs and filenames are never encoded. The runner reuses the
   same document matrix across all four questions and all k values.
5. **Compare vectors.** `embedding_retriever.py:66` multiplies each document row
   by the question vector and sums the coordinate products. Line 67 calculates
   cosine from the lengths as a cross-check; line 69 sorts the six scores.
   Line 76 selects the first k indices. Scores are computed using all 384
   coordinates; only printed values are rounded.
6. **Generate separately.** `run_experiments.py` prepares question-specific prompts
   containing only the selected k=2 evidence. Two fresh projectless Codex
   conversations received these prompts. Retrieval itself does not generate
   an answer or update model weights.

## Actual results

| Question | Keyword top 2 | Embedding top 2 | Required evidence coverage |
|---|---|---|---|
| Q1 | A1 (3), A2 (2) | A2 (0.686445594), T1 (0.581952810) | Keyword 2/2; embedding 1/2 |
| Q2 | A2 (2), B1 (1) | A2 (0.585193336), T1 (0.434760630) | Both 1/1 |
| Q3 | T1 (2), A2 (1) | T1 (0.742027402), B1 (0.471195221) | Both 1/1 |
| Q4 | A2 (1), B1 (1) | T1 (0.347721219), A2 (0.320827156) | Not applicable: answer absent |

Keyword and cosine scores have different scales; do not compare their numeric
magnitudes across methods. Q1 is a documented embedding retrieval failure:
A1 ranks fourth. At k=1, k=2 and k=3, coverage remains 1/2; k=3 adds B1's booking
rule, not the missing access hours. Q4's positive scores do not prove answerability.
This tiny evidence-coverage check is not a general performance estimate.

The actual Q1 answer refuses solo operation and explicitly acknowledges missing
access-time evidence. The Q4 answer says the wavelength cannot be determined.
Both passed student-confirmed claim-by-claim audits, so the handout's conditional prompt
revision was not triggered. No unsuccessful answer was hidden or invented.
The original answers happen to be in Chinese and are saved unchanged.

## Evidence map

| File | Contents |
|---|---|
| `evidence/pre-retrieval.txt` | Q1 evidence expectation recorded before retrieval |
| `evidence/keyword-q1.txt` | Actual standard-library Q1 baseline output |
| `evidence/embedding-inspection.txt` | Versions, shapes, first 12 coordinates, lengths, Q1 coordinate products and direct cosine check |
| `evidence/vectors.npz` | Full six document vectors, four query vectors, scores and row IDs |
| `evidence/retrieval-runs.txt` | All six scores for all four questions and both methods at k=2 |
| `evidence/results-unjudged.csv` | Original four rows with judgment columns blank |
| `results.csv` | Four rows with retrieval judgments reviewed and confirmed by Tianyu Zhao |
| `evidence/k-experiment.txt` | Actual Q1 k=1,2,3 results and coverage |
| `evidence/retrieval-audit.md` | Manual word count, observed failures and vector explanation |
| `evidence/q1-answer-prompt.txt`, `evidence/q4-answer-prompt.txt` | Exact context handoffs |
| `evidence/q1-answer-original.txt`, `evidence/q4-answer-original.txt` | Actual unedited outputs from new answer conversations |
| `evidence/q1-answer-audit.md`, `evidence/q4-answer-audit.md` | Claim-by-claim citation checks confirmed by Tianyu Zhao; no answer failure identified, so no revision was triggered |
| `evidence/answer-conversations.json` | Thread/turn IDs, timestamps, exact prompts and outputs; no answer-time tool calls observed |
| `evidence/run-metadata.json` | Environment, source/code/output hashes, and run timestamp |
| `evidence/validation.txt` | All five tests passing, including saved-vector and artifact checks |
| `evidence/reproducibility.txt` | Independent offline rerun: vectors/scores bitwise identical, max absolute difference 0 |
| `evidence/model-load.txt` | Actual CPU model load and document-vector inspection |

The first dependency install failed because sandbox DNS could not resolve PyPI.
An approved network installation succeeded. Model download succeeded and all final
experiments ran offline. No borrowed instructor/partner run output was used.

## Submission contents

- [x] Student name and working arrangement recorded: Tianyu Zhao; worked individually.
- [x] Tianyu Zhao reviewed and confirmed the Q1–Q4 retrieval judgments in `results.csv`
  and both Q1/Q4 answer audits; the original experiment outputs and answers are preserved.
- [x] User-provided reflection text inserted verbatim in `REFLECTION_TODO.txt`:
  141 words, within the assignment's 150-word limit.

Course submission destination: [Sign Up Sheet](https://docs.google.com/spreadsheets/d/1ZewIG5udWWpk3Kdrab5yDbsWDV4gnH3liKobIAp7HG4/edit?usp=sharing).

References: [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html),
[model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
[course lectures](https://onexi.org/lectures.html).
