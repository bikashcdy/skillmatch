"""Levenshtein (edit) distance and the similarity ratio built on it."""


def levenshtein_distance(a, b):
    """Minimum number of single-character inserts, deletes or substitutions to turn a into b."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(
                min(
                    previous[j] + 1,  # delete
                    current[j - 1] + 1,  # insert
                    previous[j - 1] + (ca != cb),  # substitute
                )
            )
        previous = current
    return previous[-1]


def similarity(a, b):
    """Similarity(a,b) = 1 - distance / max(len(a), len(b)). 1.0 means identical."""
    longest = max(len(a), len(b))
    if longest == 0:
        return 1.0
    return 1 - levenshtein_distance(a, b) / longest
