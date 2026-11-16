import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    """
    Tokenize text into lowercase alphanumeric and hyphenated tokens.
    Preserves administrative terms, scheme codes (e.g. 'pm-kisan'), and digits.
    """
    if not text:
        return []
    return re.findall(r"\b[a-zA-Z0-9]+(?:-[a-zA-Z0-9]+)*\b", text.lower())


class BM25Okapi:
    """
    A standalone, pure-Python implementation of BM25Okapi with smoothed IDF.
    """

    def __init__(
        self,
        corpus: list[list[str]],
        k1: float = 1.5,
        b: float = 0.75
    ) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens = [len(doc) for doc in corpus]
        self.avgdl = (
            sum(self.doc_lens) / self.corpus_size
            if self.corpus_size > 0
            else 0.0
        )
        self.doc_freqs: list[Counter] = []
        self.nd: dict[str, int] = {}
        self.idf: dict[str, float] = {}

        for doc in corpus:
            freq = Counter(doc)
            self.doc_freqs.append(freq)
            for token in freq.keys():
                self.nd[token] = self.nd.get(token, 0) + 1

        for token, freq in self.nd.items():
            # Smoothed BM25 IDF (always non-negative)
            self.idf[token] = math.log(
                1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5)
            )

    def get_scores(self, query_tokens: list[str]) -> list[float]:
        scores = [0.0] * self.corpus_size
        if self.corpus_size == 0 or self.avgdl == 0:
            return scores

        for token in query_tokens:
            if token not in self.idf:
                continue
            idf_val = self.idf[token]
            for idx, doc_freq in enumerate(self.doc_freqs):
                tf = doc_freq.get(token, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lens[idx]
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * (
                    1.0 - self.b + self.b * (doc_len / self.avgdl)
                )
                scores[idx] += idf_val * (numerator / denominator)

        return scores


class BM25Retriever:
    """
    Retriever wrapping page-isolated chunks for a single document.
    """

    def __init__(self, chunks: list[dict], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.tokenized_corpus = [
            tokenize(chunk.get("text", "")) for chunk in chunks
        ]
        self.bm25 = BM25Okapi(self.tokenized_corpus, k1=k1, b=b)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        Rank chunks using BM25.
        Returns top_k results with chunk_id, document_id, page_number, text, score.
        """
        if not self.chunks or top_k <= 0:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        # Rank indices descending by score
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda idx: scores[idx],
            reverse=True
        )

        results = []
        for idx in ranked_indices:
            score = scores[idx]
            if score <= 0.0:
                continue

            chunk = self.chunks[idx]
            results.append({
                "chunk_id": chunk.get("chunk_id"),
                "document_id": chunk.get("document_id"),
                "page_number": chunk.get("page_number"),
                "text": chunk.get("text"),
                "score": round(float(score), 4)
            })

            if len(results) >= top_k:
                break

        return results
