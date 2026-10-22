# Retrieval and vector audit — confirmed retrieval checks and documented vector-review provenance

These judgments follow the actual saved run, not an expected ranking. The initial
Q1 evidence expectation was saved in `pre-retrieval.txt` before running retrieval.
All figures below come from `retrieval-runs.txt` and `embedding-inspection.txt`.

## Corpus and baseline check

There are exactly six chunks. A test compares each body, character for character,
with the fetched handout. IDs and filenames remain separate from searchable text.
The source directory contains only access.txt, training.txt and booking.txt.

Student-checked Q1 A1 count: the distinct shared words are `00`, `graduate`, `trained`, so
the score is 3. `19:00`, `08:00` and `22:00` are split into alphanumeric tokens;
the shared `00` contributes once. `student` does not match `students`, and
`operate` does not match `operating`. Repeated words do not increase a set overlap.
Tianyu Zhao answered "3" in the manual count check and identified the `00` match as "碰巧重合" (coincidental literal overlap), not evidence that the retriever understands whether 19:00 falls within the access-hours interval.

| Question | Keyword selected IDs (scores) | Embedding selected IDs (scores) | Evidence judgment |
|---|---|---|---|
| Q1 | A1 (3), A2 (2) | A2 (0.686445594), T1 (0.581952810) | Keyword 2/2; embedding 1/2, missing A1. Confirmed by Tianyu Zhao: missing access-time evidence. |
| Q2 | A2 (2), B1 (1) | A2 (0.585193336), T1 (0.434760630) | Both 1/1; A2 supplies the two-person rule. Both methods confirmed sufficient by Tianyu Zhao. |
| Q3 | T1 (2), A2 (1) | T1 (0.742027402), B1 (0.471195221) | Both 1/1; T1 supplies the 12-month renewal rule. Both methods confirmed sufficient by Tianyu Zhao. |
| Q4 | A2 (1), B1 (1) | T1 (0.347721219), A2 (0.320827156) | Wavelength absent; neither result provides the answer; ratio N/A. Confirmed by Tianyu Zhao after discussion: supplied evidence cannot determine the wavelength; do not guess from pretrained knowledge. |

The Q2 paraphrase reaches A2 by the exact words `laser` and `present`, as well as
by embedding similarity. Q3's keyword match is `laser` plus `must`; the semantic
model also ranks the correct T1 first despite the question using “refresh my laser
qualification” instead of “training ... renewed.” This run does not show embeddings
winning every comparison. Keyword retrieval includes both required Q1 passages;
the embedding top two do not.

## Q1 k experiment

| k | Selected IDs | Required coverage | Added information |
|---|---|---|---|
| 1 | A2 | 1/2 | Operating staffing condition |
| 2 | A2, T1 | 1/2 | Training validity and renewal condition |
| 3 | A2, T1, B1 | 1/2 | Two-hour booking limit and calendar procedure |

Tianyu Zhao confirmed that increasing k from 1 to 3 did not complete Q1 evidence: all three selections lack A1. The extra passages add conditions but not access times. A1 ranks
fourth with 0.374248922. k=4 was not a requested additional experiment and was not
used to replace the k=2 answer context. The recorded k=1 and k=3 outcomes remain
partial; no rankings were adjusted.

## What the vectors show

The document matrix is `(6, 384)`: one row for each passage, 384 coordinates per
row. Every question is `(384,)`. Query and document vectors need equal dimensionality
and a compatible learned representation for coordinate products to be meaningful.
Equal length alone would not make vectors from different models compatible.

Normalization divides by vector length. The actual lengths are close to 1 within
floating-point tolerance. All 384 coordinates are used in the dot product, and
direct cosine agrees within absolute tolerance 1e-6. Sorting the six scores in
descending order, breaking exact ties by ascending ID, and slicing the first k
indices turns scores into selected evidence. No relevance threshold is applied.

For Q1 × A2, the first 12 products sum to 0.016111500367; the other 372 sum to
0.670334186373. Their sum is 0.686445686740, compared with a float32 matrix dot
product of 0.686445593834. The difference is about 9.3e-8 due to accumulation
precision, below the 1e-6 tolerance; displayed rounding was not used for ranking.

Across the displayed first 12 coordinates of the six documents and Q1, the minimum
is T1 coordinate 5 (-0.116691455245018), and the maximum is T1 coordinate 12
(0.13567747175693512), using one-based indices. Neither single coordinate explains
a passage; there is no reliable semantic name for it. The whole learned vector
and its relationship to another vector drive retrieval.

`encode_document` and `encode_query` express the two roles. With this model their
underlying encoding behavior is the same. Encoding creates representations, not
answers. The pretrained model was not trained or fine-tuned on these six paragraphs;
RAG changes the generator's supplied context, not its learned weights.

Student vector review: distinguish the student's answers, understanding after correction, agreement with an explanation, and program-verified values shown to the student. Do not represent every item as independently solved by the student.

- [x] Top-2 selection: Tianyu Zhao answered "选最大的两个", selecting the largest similarity scores (A2 and T1).
- [x] RAG versus training: Tianyu Zhao answered "不改变权重，只改变上下文".
- [x] Meaning of an individual coordinate: after initially suggesting that a larger coordinate means greater feasibility, Tianyu Zhao received the correction that a coordinate is not probability, confidence or feasibility; whole-vector similarity indicates representational alignment but does not guarantee sufficient evidence. The user replied "清楚". This records understanding after correction, not a claim that the initial explanation was fully correct.
- Matrix shape and compatible representation space: the main chat explained that `(6, 384)` represents six passages with 384 coordinates each, and that matching dimensions alone are insufficient without compatible learned directions; the same embedding model was used for queries and passages. Tianyu Zhao replied "我同意". Recorded as agreement after reading the explanation, not an independently produced explanation.
- Displayed extrema: the program verified T1 coordinate 5 as the minimum (-0.116691455245018) and T1 coordinate 12 as the maximum (0.13567747175693512), using one-based indices. The main chat showed rounded values -0.1167 and 0.1357, both in T1. No claim is made that the student independently located or verified these extrema.

Numerical verification is recorded separately. The user-provided reflection text has been inserted verbatim in `REFLECTION_TODO.txt` (141 words); this review record is not a substitute for that reflection.
