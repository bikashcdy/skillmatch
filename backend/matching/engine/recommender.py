"""Top-K job recommendation with a min-heap and a score cache."""

import heapq
import itertools

from .match_engine import MatchEngine, job_text

_CACHE = {}
_CACHE_LIMIT = 5000


def _candidate_key(c):
    return (tuple(sorted(c.skills)), c.experience_years, c.education_level, hash(c.text), c.preferred_location, c.preferred_job_type)


def _job_key(job):
    return (
        job.pk, hash(job_text(job)), job.min_experience_years, job.required_education, job.location, job.job_type,
    )


class Recommender:
    """Scores every job for a candidate and keeps the K best using a min-heap: O(J log K)."""

    def __init__(self, engine=None, weights_version=0, corpus_signature=0):
        self.engine = engine or MatchEngine()
        self.salt = (weights_version, corpus_signature, tuple(sorted(self.engine.weights.items())))

    def score(self, candidate, job):
        key = (self.salt, _candidate_key(candidate), _job_key(job))
        hit = _CACHE.get(key)
        if hit is None:
            hit = self.engine.calculate(candidate, job)
            if len(_CACHE) >= _CACHE_LIMIT:
                _CACHE.clear()
            _CACHE[key] = hit
        return hit

    def top_k(self, candidate, jobs, k=5):
        """Return [(job, result), ...] for the K highest scores, best first."""
        heap, counter = [], itertools.count()  # counter breaks ties so jobs are never compared
        for job in jobs:
            result = self.score(candidate, job)
            item = (result["match_percentage"], -next(counter), job, result)
            if len(heap) < k:
                heapq.heappush(heap, item)
            elif item[0] > heap[0][0]:
                heapq.heapreplace(heap, item)
        return [(job, result) for _, _, job, result in sorted(heap, key=lambda x: (-x[0], -x[1]))]


def clear_cache():
    _CACHE.clear()
