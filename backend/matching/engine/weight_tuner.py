"""Grid-search weight optimisation using NDCG@5 against manual relevance ratings."""

from .match_engine import COMPONENTS, DEFAULT_WEIGHTS, combine
from .metrics import ndcg_at_k

STEP = 0.05


def weight_grid(step=STEP, parts=len(COMPONENTS)):
    """Every combination of `parts` non-negative weights in multiples of `step` that sum to 1."""
    units = round(1 / step)

    def rec(remaining, slots):
        if slots == 1:
            yield (remaining,)
            return
        for first in range(remaining + 1):
            for rest in rec(remaining - first, slots - 1):
                yield (first,) + rest

    for combo in rec(units, parts):
        yield {k: v * step for k, v in zip(COMPONENTS, combo)}


def average_ndcg(groups, weights, k=5):
    """groups: {query_id: [(components, knockout, rating), ...]} -> mean NDCG@k over the queries."""
    scores = []
    for items in groups.values():
        ranked = sorted(
            ((combine(c, weights, ko)[0], rating) for c, ko, rating in items), key=lambda x: -x[0]
        )
        scores.append(ndcg_at_k([r for _, r in ranked], k))
    return sum(scores) / len(scores) if scores else 0.0


def tune_weights(tuning_groups, test_groups=None, step=STEP, k=5):
    """Pick the weight combination with the best average NDCG@k on the tuning data.

    Ties go to the combination closest to the default weights. The winner is then
    measured on the separate test data.
    """
    best, best_key = None, None
    for weights in weight_grid(step):
        ndcg = average_ndcg(tuning_groups, weights, k)
        distance = sum(abs(weights[c] - DEFAULT_WEIGHTS[c]) for c in COMPONENTS)
        key = (round(ndcg, 9), -distance)
        if best_key is None or key > best_key:
            best, best_key = weights, key
    return {
        "weights": {c: round(best[c], 2) for c in COMPONENTS},
        "tuning_ndcg": round(average_ndcg(tuning_groups, best, k), 4),
        "test_ndcg": round(average_ndcg(test_groups, best, k), 4) if test_groups else None,
        "default_tuning_ndcg": round(average_ndcg(tuning_groups, DEFAULT_WEIGHTS, k), 4),
        "default_test_ndcg": round(average_ndcg(test_groups, DEFAULT_WEIGHTS, k), 4) if test_groups else None,
        "combinations_tested": sum(1 for _ in weight_grid(step)),
    }
