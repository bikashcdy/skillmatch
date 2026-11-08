"""TF-IDF vectors and cosine similarity, written from scratch (no scikit-learn needed).

The textbook formula  TF x log(N / (1 + DF))  has two weaknesses, so two standard fixes are used:

1. IDF = ln((1 + N) / (1 + DF)) + 1   (smoothed IDF)
   The textbook version goes NEGATIVE when a word appears in every document (N=2, DF=2 gives log(2/3)),
   which makes common words subtract from the similarity. The smoothed version is always >= 1.
2. TF = 1 + ln(count)                  (sublinear TF)
   With raw counts a candidate can repeat "python" 50 times and push the score up. With sublinear TF
   the 50th repeat adds almost nothing, so keyword stuffing no longer works.

Vectors are L2-normalised, so the cosine similarity is simply their dot product.
Both options behave exactly like scikit-learn's TfidfVectorizer(smooth_idf=True, sublinear_tf=True).
"""

import math
import re
from collections import Counter

_WORD = re.compile(r"(?u)\b\w\w+\b")
STOP_WORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the this to was were will with
    we you your our their they he she i me my us about into over under than then them these those not no
    can could should would may might also any all each other more most such only own same so too very""".split()
)


def tokenize(text):
    return [w for w in _WORD.findall((text or "").lower()) if w not in STOP_WORDS]


class TextScorer:
    """Compare two texts. `corpus` (e.g. every job description) makes IDF meaningful."""

    def __init__(self, corpus=(), sublinear_tf=True):
        self.sublinear_tf = sublinear_tf
        self.base_texts = set()
        self.df = Counter()
        self.n_docs = 0
        for text in corpus:
            self._add(text)

    def _add(self, text):
        if text in self.base_texts:
            return
        self.base_texts.add(text)
        self.n_docs += 1
        self.df.update(set(tokenize(text)))

    def _vector(self, text, df, n_docs):
        counts = Counter(tokenize(text))
        vec = {
            t: ((1 + math.log(c)) if self.sublinear_tf else c) * (math.log((1 + n_docs) / (1 + df.get(t, 0))) + 1)
            for t, c in counts.items()
        }
        norm = math.sqrt(sum(v * v for v in vec.values()))
        return {t: v / norm for t, v in vec.items()} if norm else {}

    def similarity(self, a, b):
        """Cosine similarity (0..1) between texts a and b, using the corpus plus a and b."""
        df, n_docs = self.df.copy(), self.n_docs
        for text in (a, b):
            if text not in self.base_texts:
                df.update(set(tokenize(text)))
                n_docs += 1
        va, vb = self._vector(a, df, n_docs), self._vector(b, df, n_docs)
        if not va or not vb:
            return 0.0
        small, large = (va, vb) if len(va) < len(vb) else (vb, va)
        return max(0.0, min(1.0, sum(v * large.get(t, 0.0) for t, v in small.items())))
