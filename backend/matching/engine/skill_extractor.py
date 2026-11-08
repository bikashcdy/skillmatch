"""N-gram skill extraction using a hash map (dictionary) with longest-phrase matching."""

import re

from .skill_data import ALIAS_INDEX, IMPLIES

# Keeps skill-like tokens whole: c++, c#, .net, node.js, ci/cd, scikit-learn.
_TOKEN = re.compile(r"\.?[a-z0-9]+(?:[.\-+#/][a-z0-9]+)*[+#]*")
_SPLIT = re.compile(r"[./\-]")


class SkillExtractor:
    """Finds skills in free text.

    1. lowercase and tokenize
    2. build n-grams from the longest (3 words) down to single words
    3. look every n-gram up in the hash map (alias -> canonical skill)
    4. longer phrases win; words already used by an accepted phrase are skipped
    """

    def __init__(self, alias_index=None, implies=None):
        self.index = dict(alias_index or ALIAS_INDEX)
        self.implies = implies if implies is not None else IMPLIES
        self.max_n = max(len(alias.split()) for alias in self.index)

    def tokenize(self, text):
        tokens = []
        for token in _TOKEN.findall((text or "").lower()):
            if token in self.index or not _SPLIT.search(token.strip(".")):
                tokens.append(token)
            else:  # "python/django" or "react-native" -> separate words
                tokens.extend(part for part in _SPLIT.split(token) if part)
        return tokens

    def extract(self, text, with_implied=True):
        tokens = self.tokenize(text)
        used = [False] * len(tokens)
        found = set()
        for n in range(min(self.max_n, len(tokens)), 0, -1):
            for start in range(len(tokens) - n + 1):
                if any(used[start : start + n]):  # overlaps a longer accepted match
                    continue
                skill = self.index.get(" ".join(tokens[start : start + n]))
                if skill:
                    found.add(skill)
                    for i in range(start, start + n):
                        used[i] = True
        if with_implied:  # a Django developer also knows Python
            for skill in list(found):
                found.update(self.implies.get(skill, []))
        return sorted(found)


_default = SkillExtractor()


def extract_skills(text):
    return _default.extract(text)
