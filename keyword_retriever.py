"""Transparent, standard-library-only word-overlap baseline."""
import argparse
import re
from corpus import load_chunks, positive_k

STOPWORDS = set("a an the is are to of in at for and or may can i it be".split())


def words(text):
    return set(re.findall(r"[a-z0-9]+", text.lower())) - STOPWORDS


def retrieve(chunks, question, k=2):
    if k < 1:
        raise ValueError("k must be positive")
    query_words = words(question)
    ranked = []
    for chunk in chunks:
        matched = sorted(query_words & words(chunk.text))
        ranked.append((chunk, len(matched), matched))
    ranked.sort(key=lambda row: (-row[1], row[0].id))
    selected = [row for row in ranked if row[1] > 0][:k]
    return ranked, selected


def print_result(question, k, ranked, selected):
    print(f"KEYWORD question={question!r} k={k}")
    print("Distinct query words:", ", ".join(sorted(words(question))))
    print("All six scores (descending; ties: ascending ID):")
    for chunk, score, matched in ranked:
        print(f"{chunk.id} score={score} matched={matched}")
    if not selected:
        print("No matching passages.")
    else:
        print("Selected:", ", ".join(row[0].id for row in selected))
        for chunk, score, _ in selected:
            print(f"[{chunk.id}] {chunk.filename} score={score}\n{chunk.text}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question")
    parser.add_argument("-k", "--k", type=positive_k, default=2)
    args = parser.parse_args()
    ranked, selected = retrieve(load_chunks(), args.question, args.k)
    print_result(args.question, args.k, ranked, selected)


if __name__ == "__main__":
    main()
