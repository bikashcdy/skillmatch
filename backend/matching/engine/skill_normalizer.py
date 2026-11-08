"""Fuzzy skill normalisation: synonyms first, then Levenshtein similarity."""

from .levenshtein import similarity
from .skill_data import ALIAS_INDEX

THRESHOLD = 0.85  # minimum similarity to accept a spelling match


def normalize_skill(name, threshold=THRESHOLD):
    """Map 'ReactJS', 'Javascripts' or 'javascrpt' to the standard skill name."""
    n = " ".join((name or "").strip().lower().split())
    if n in ALIAS_INDEX:  # synonym dictionary
        return ALIAS_INDEX[n]
    if n.endswith("s") and n[:-1] in ALIAS_INDEX:  # plural: "javascripts"
        return ALIAS_INDEX[n[:-1]]
    if len(n) >= 5:  # spelling mistakes: "javascrpt", "wordpres"
        best, best_sim = None, 0.0
        for alias in ALIAS_INDEX:
            if len(alias) < 5:
                continue
            s = similarity(n, alias)
            if s >= threshold and s > best_sim:
                best, best_sim = alias, s
        if best:
            return ALIAS_INDEX[best]
    return n
