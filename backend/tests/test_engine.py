"""Tests for every algorithm in core/engine/ (pure Python, no database) and the weight tuner."""

import unittest
from types import SimpleNamespace

from django.test import SimpleTestCase

from matching.engine import (
    CandidateProfile, CycleError, MatchEngine, Recommender, SkillExtractor, TextScorer, cohens_kappa, combine,
    generate_learning_path, levenshtein_distance, ndcg_at_k, normalize_skill, precision_at_k,
    precision_recall_f1, score_education, score_experience, score_preferences, score_skills,
    skill_gap_percentage, spearman, tune_weights, weight_grid,
)
from matching.engine.levenshtein import similarity
from matching.engine.match_engine import DEFAULT_WEIGHTS, KNOCKOUT_CAP, job_text
from matching.engine.recommender import clear_cache
from matching.engine.whatif import simulate

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:  # scikit-learn is only needed to double-check the custom TF-IDF
    TfidfVectorizer = None


def job(**kw):
    base = dict(pk=1, title="Python Developer", company="Acme", description="Build web apps", location="Pokhara",
                required_skills=["python"], nice_to_have_skills=[], min_experience_years=0,
                required_education="", job_type="full_time")
    base.update(kw)
    return SimpleNamespace(**base)


class SkillExtractorTest(SimpleTestCase):
    def test_document_example(self):
        text = "Experienced in Python, Machine Learning and React.js."
        self.assertEqual(SkillExtractor().extract(text, with_implied=False), ["machine learning", "python", "react"])

    def test_longest_phrase_wins_and_overlaps_are_removed(self):
        # "django rest framework" (3 words) beats "rest" + "framework"; "machine learning" is one skill
        found = SkillExtractor().extract("Built an API with Django REST Framework", with_implied=False)
        self.assertEqual(found, ["django"])
        self.assertNotIn("rest api", found)

    def test_special_tokens_and_separators(self):
        found = SkillExtractor().extract("C++, C#, .NET, Python/Django, CI/CD and scikit-learn", with_implied=False)
        for skill in ("c++", "c#", "python", "django", "devops", "machine learning"):
            self.assertIn(skill, found)

    def test_implied_skills(self):
        self.assertIn("python", SkillExtractor().extract("I use Django daily"))

    def test_no_partial_word_matches(self):
        self.assertEqual(SkillExtractor().extract("javascripture and pythonic habits", with_implied=False), [])


class NormalizerTest(SimpleTestCase):
    def test_levenshtein_document_example(self):
        self.assertEqual(levenshtein_distance("javascrpt", "javascript"), 1)
        self.assertAlmostEqual(similarity("javascrpt", "javascript"), 0.90)
        self.assertEqual(levenshtein_distance("kitten", "sitting"), 3)

    def test_variants_map_to_one_name(self):
        for variant in ("React", "React.js", "ReactJS", "reactjs"):
            self.assertEqual(normalize_skill(variant), "react")
        self.assertEqual(normalize_skill("javascrpt"), "javascript")
        self.assertEqual(normalize_skill("Javascripts"), "javascript")

    def test_unknown_skill_is_kept_and_different_skills_are_not_merged(self):
        self.assertEqual(normalize_skill("Blockchain"), "blockchain")
        self.assertNotEqual(normalize_skill("javascript"), normalize_skill("typescript"))


class SkillScorerTest(SimpleTestCase):
    def test_document_example(self):
        # Python, JavaScript exact; React related (Vue known); Docker missing
        r = score_skills(["python", "javascript", "vue"], ["python", "javascript", "react", "docker"])
        self.assertEqual((r["matched"], r["partial"], r["missing"]), (["javascript", "python"], ["react"], ["docker"]))
        self.assertAlmostEqual(r["score"], (2 + 2 + 0.5 * 2 + 0) / 8)
        self.assertTrue(r["knockout"])  # Docker is a must-have and completely missing

    def test_nice_to_have_counts_half_as_much_and_never_knocks_out(self):
        r = score_skills(["python"], ["python"], ["docker"])
        self.assertAlmostEqual(r["score"], 2 / 3)
        self.assertFalse(r["knockout"])
        self.assertEqual(r["missing"], ["docker"])

    def test_related_skill_gives_half(self):
        r = score_skills(["django"], ["flask"])
        self.assertEqual(r["partial"], ["flask"])
        self.assertAlmostEqual(r["score"], 0.5)
        self.assertFalse(r["knockout"])  # partially covered is not "completely missing"

    def test_names_are_normalised_and_empty_job(self):
        self.assertEqual(score_skills(["ReactJS"], ["react.js"])["score"], 1.0)
        self.assertEqual(score_skills([], [])["score"], 1.0)


class TextScorerTest(SimpleTestCase):
    A = "Python developer with SQL experience."
    B = "Looking for a Python developer with database knowledge."

    def test_identical_disjoint_and_partial(self):
        scorer = TextScorer()
        self.assertAlmostEqual(scorer.similarity(self.A, self.A), 1.0)
        self.assertEqual(scorer.similarity("alpha beta", "gamma delta"), 0.0)
        self.assertEqual(scorer.similarity("", self.B), 0.0)
        self.assertTrue(0 < scorer.similarity(self.A, self.B) < 1)

    @unittest.skipIf(TfidfVectorizer is None, "scikit-learn not installed (pip install -r requirements-dev.txt)")
    def test_matches_scikit_learn(self):
        from matching.engine.text_scorer import STOP_WORDS

        others = ["Django backend engineer needed for our team", "Senior React frontend developer with CSS skills",
                  "Data analyst with Excel and SQL experience", "Looking for a marketing manager"]
        scorer = TextScorer(others)
        mine = scorer.similarity(self.A, self.B)
        vec = TfidfVectorizer(stop_words=list(STOP_WORDS), sublinear_tf=True).fit(others + [self.A, self.B])
        a, b = vec.transform([self.A]), vec.transform([self.B])
        self.assertAlmostEqual(mine, float(cosine_similarity(a, b)[0][0]), places=9)
        # the raw-count variant matches scikit-learn too
        raw = TfidfVectorizer(stop_words=list(STOP_WORDS)).fit(others + [self.A, self.B])
        self.assertAlmostEqual(TextScorer(others, sublinear_tf=False).similarity(self.A, self.B),
                               float(cosine_similarity(raw.transform([self.A]), raw.transform([self.B]))[0][0]), places=9)


class TextScorerImprovementsTest(SimpleTestCase):
    JOB = "Python developer needed to build web applications with Django and SQL"

    def test_textbook_idf_goes_negative_but_ours_does_not(self):
        import math

        self.assertLess(math.log(2 / (1 + 2)), 0)  # N=2 documents, a word in both: log(2/3) < 0
        self.assertGreaterEqual(math.log((1 + 2) / (1 + 2)) + 1, 1)  # smoothed IDF stays >= 1

    def test_repeating_a_word_barely_changes_the_score_with_sublinear_tf(self):
        honest = "Python developer. Built web applications with Django and SQL databases at two companies."
        stuffed = honest + " python " * 60
        sub = TextScorer(sublinear_tf=True)
        raw = TextScorer(sublinear_tf=False)
        gain_sub = sub.similarity(stuffed, self.JOB) - sub.similarity(honest, self.JOB)
        gain_raw = raw.similarity(stuffed, self.JOB) - raw.similarity(honest, self.JOB)
        self.assertLess(abs(gain_sub), abs(gain_raw))  # raw counts let 60 repeats distort the score a lot
        self.assertLess(abs(gain_sub), 0.05)


class ScoreComponentsTest(SimpleTestCase):
    def test_experience(self):
        self.assertEqual(score_experience(3, 2), 1.0)  # document example
        self.assertEqual(score_experience(1, 2), 0.5)
        self.assertEqual(score_experience(0, 0), 1.0)  # fresher job
        self.assertEqual(score_experience(None, 2), 0.0)

    def test_education_levels(self):
        self.assertEqual(score_education("bachelor", "bachelor"), 1.0)
        self.assertAlmostEqual(score_education("bachelor", "master"), 3 / 4)
        self.assertAlmostEqual(score_education("diploma", "bachelor"), 2 / 3)
        self.assertEqual(score_education("none", ""), 1.0)
        self.assertEqual(score_education("phd", "master"), 1.0)

    def test_preferences_only_count_what_was_given(self):
        self.assertEqual(score_preferences("", "", "Pokhara", "full_time")[0], None)
        self.assertEqual(score_preferences("pokhara", "", "Pokhara, Nepal", "full_time")[0], 1.0)
        self.assertEqual(score_preferences("Pokhara", "internship", "Pokhara", "full_time"), (0.5, 1, 2))
        self.assertEqual(score_preferences("Butwal", "internship", "Pokhara", "full_time")[0], 0.0)

    def test_skill_gap_document_example(self):
        self.assertEqual(skill_gap_percentage(["docker"], 5), 20.0)
        self.assertEqual(skill_gap_percentage([], 0), 0.0)


class MatchEngineTest(SimpleTestCase):
    def test_document_example_is_75(self):
        components = {"skill": 0.70, "text": 0.55, "experience": 0.80, "education": 1.0, "preference": 1.0}
        final, raw = combine(components, DEFAULT_WEIGHTS)
        self.assertAlmostEqual(final, 75.0)  # 28 + 11 + 16 + 10 + 10

    def test_knockout_caps_at_60(self):
        components = {"skill": 1.0, "text": 1.0, "experience": 1.0, "education": 1.0, "preference": 1.0}
        self.assertEqual(combine(components, DEFAULT_WEIGHTS, knockout=True)[0], KNOCKOUT_CAP)
        self.assertEqual(combine(components, DEFAULT_WEIGHTS)[0], 100.0)

    def test_missing_preference_does_not_punish_the_candidate(self):
        components = {"skill": 1.0, "text": 1.0, "experience": 1.0, "education": 1.0, "preference": None}
        self.assertAlmostEqual(combine(components, DEFAULT_WEIGHTS)[0], 100.0)

    def test_default_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(DEFAULT_WEIGHTS.values()), 1.0)

    def test_full_calculation_and_explanation(self):
        cand = CandidateProfile(skills=["python", "django"], experience_years=2, education_level="bachelor",
                                text="Python Django developer with two years experience")
        j = job(required_skills=["python", "django", "docker"], nice_to_have_skills=["git"], min_experience_years=2,
                required_education="bachelor")
        r = MatchEngine().calculate(cand, j)
        self.assertTrue(r["knockout"])
        self.assertLessEqual(r["match_percentage"], 60)
        self.assertGreater(r["raw_percentage"], r["match_percentage"])
        self.assertEqual(r["missing_must_have"], ["docker"])
        self.assertEqual(r["missing_skills"], ["docker", "git"])
        self.assertIsNone(r["preference_score"])
        self.assertEqual(r["skill_gap"], 50.0)
        self.assertTrue(any("capped" in line for line in r["explanation"]))

    def test_perfect_candidate(self):
        cand = CandidateProfile(skills=["python"], experience_years=1, education_level="bachelor",
                                text="Python Developer. Build web apps. python", preferred_location="Pokhara",
                                preferred_job_type="full_time")
        r = MatchEngine().calculate(cand, job())
        self.assertFalse(r["knockout"])
        self.assertEqual(r["preference_score"], 100.0)
        self.assertGreater(r["match_percentage"], 85)


class RecommenderTest(SimpleTestCase):
    def setUp(self):
        clear_cache()
        self.cand = CandidateProfile(skills=["python", "django"], text="python django developer")
        self.jobs = [job(pk=i, title=f"Role {i}", required_skills=skills) for i, skills in enumerate(
            [["python"], ["python", "django"], ["docker"], ["django"], ["react"], ["python", "sql"]], start=1)]

    def test_top_k_matches_full_sort(self):
        rec = Recommender()
        full = sorted(((rec.score(self.cand, j)["match_percentage"], j.pk) for j in self.jobs), reverse=True)
        top = rec.top_k(self.cand, self.jobs, k=3)
        self.assertEqual([r["match_percentage"] for _, r in top], [pct for pct, _ in full[:3]])
        self.assertEqual(len(top), 3)
        self.assertEqual(rec.top_k(self.cand, [], k=3), [])

    def test_scores_are_cached(self):
        rec = Recommender()
        first = rec.score(self.cand, self.jobs[0])
        self.assertIs(rec.score(self.cand, self.jobs[0]), first)


class LearningPathTest(SimpleTestCase):
    def test_prerequisites_come_first(self):
        path = generate_learning_path(["react"], known_skills=[])
        self.assertEqual(path[-1], "react")
        self.assertEqual(set(path), {"html", "css", "javascript", "react"})
        self.assertLess(path.index("html"), path.index("css"))
        self.assertLess(path.index("css"), path.index("javascript"))
        self.assertLess(path.index("javascript"), path.index("react"))

    def test_known_skills_are_skipped(self):
        self.assertEqual(generate_learning_path(["react"], known_skills=["javascript", "html", "css"]), ["react"])

    def test_cycle_is_detected(self):
        with self.assertRaises(CycleError):
            generate_learning_path(["a"], prerequisites={"a": ["b"], "b": ["a"]})


class MetricsTest(SimpleTestCase):
    def test_ranking_metrics(self):
        self.assertAlmostEqual(ndcg_at_k([3, 2, 1, 0], 5), 1.0)
        self.assertLess(ndcg_at_k([0, 1, 2, 3], 5), 1.0)
        self.assertEqual(ndcg_at_k([0, 0], 5), 0.0)
        self.assertAlmostEqual(precision_at_k([3, 2, 0, 0, 1], 5), 2 / 5)

    def test_correlation_and_agreement(self):
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [10, 20, 30, 40]), 1.0)
        self.assertAlmostEqual(spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
        self.assertAlmostEqual(cohens_kappa([0, 1, 2, 3], [0, 1, 2, 3]), 1.0)
        self.assertLess(cohens_kappa([0, 0, 1, 1], [1, 1, 0, 0]), 0)

    def test_skill_extraction_prf1(self):
        p, r, f = precision_recall_f1(["python", "sql", "react"], ["python", "sql", "docker", "git"])
        self.assertAlmostEqual(p, 2 / 3)
        self.assertAlmostEqual(r, 2 / 4)
        self.assertAlmostEqual(f, 2 * (2 / 3) * (1 / 2) / ((2 / 3) + (1 / 2)))


class WeightTunerTest(SimpleTestCase):
    def test_grid_is_valid(self):
        grid = list(weight_grid())
        self.assertEqual(len(grid), 10626)  # C(24, 4) combinations in steps of 0.05
        self.assertTrue(all(abs(sum(w.values()) - 1) < 1e-9 and min(w.values()) >= 0 for w in grid))

    def test_tuner_finds_the_component_that_matches_the_manual_ratings(self):
        def comp(skill, text):
            return {"skill": skill, "text": text, "experience": 0.5, "education": 0.5, "preference": None}

        # manual ratings follow the text score, while the skill score points the other way
        tune = {1: [(comp(0.9, 0.1), False, 0), (comp(0.5, 0.5), False, 1), (comp(0.1, 0.9), False, 3), (comp(0.7, 0.3), False, 0)]}
        test = {2: [(comp(0.8, 0.2), False, 0), (comp(0.2, 0.8), False, 3), (comp(0.5, 0.6), False, 2)]}
        result = tune_weights(tune, test)
        self.assertAlmostEqual(sum(result["weights"].values()), 1.0, places=6)
        self.assertEqual(result["tuning_ndcg"], 1.0)
        self.assertGreater(result["test_ndcg"], result["default_test_ndcg"])  # generalises to unseen data
        self.assertGreater(result["tuning_ndcg"], result["default_tuning_ndcg"])
        self.assertGreater(result["weights"]["text"], result["weights"]["skill"])


class WhatIfTest(SimpleTestCase):
    def test_simulation_never_changes_the_real_profile(self):
        cand = CandidateProfile(skills=["python"], text="python developer")
        jobs = [job(pk=1, required_skills=["python", "docker"])]
        engine = MatchEngine()
        rows = simulate(cand, jobs, ["docker"], lambda c, j: engine.calculate(c, j))
        self.assertEqual(cand.skills, ["python"])
        self.assertGreater(rows[0]["after"], rows[0]["before"])
        self.assertTrue(rows[0]["crosses_threshold"] or rows[0]["after"] < 75)
