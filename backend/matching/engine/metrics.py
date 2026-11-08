"""Evaluation metrics for ranking quality and skill extraction."""

import math


def precision_at_k(relevances, k=5, threshold=2):
    """Share of the top-k ranked items whose manual rating is at least `threshold`."""
    top = relevances[:k]
    return sum(1 for r in top if r >= threshold) / len(top) if top else 0.0


def dcg_at_k(relevances, k=5):
    return sum((2 ** rel - 1) / math.log2(i + 2) for i, rel in enumerate(relevances[:k]))


def ndcg_at_k(relevances, k=5):
    """NDCG@K = DCG@K / ideal DCG@K. `relevances` are manual ratings in the engine's ranked order."""
    ideal = dcg_at_k(sorted(relevances, reverse=True), k)
    return dcg_at_k(relevances, k) / ideal if ideal > 0 else 0.0


def _ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for idx in range(i, j + 1):
            ranks[order[idx]] = (i + j) / 2 + 1  # average rank for ties
        i = j + 1
    return ranks


def spearman(x, y):
    """Spearman rank correlation between two equally long lists."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    rx, ry = _ranks(x), _ranks(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else 0.0


def cohens_kappa(a, b):
    """Agreement between two label lists, corrected for chance."""
    if len(a) != len(b) or not a:
        return 0.0
    n = len(a)
    observed = sum(1 for x, y in zip(a, b) if x == y) / n
    labels = set(a) | set(b)
    expected = sum((a.count(l) / n) * (b.count(l) / n) for l in labels)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def precision_recall_f1(predicted, actual):
    """Precision, recall and F1 for one extracted skill set against the true skill set."""
    p, a = set(predicted), set(actual)
    tp = len(p & a)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(a) if a else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1
