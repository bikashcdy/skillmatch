"""Independent, Django-free matching algorithms for JobMitra (see docs/MATCHING.md)."""

from .education_scorer import score_education
from .experience_scorer import score_experience
from .learning_path import CycleError, generate_learning_path
from .levenshtein import levenshtein_distance
from .match_engine import DEFAULT_WEIGHTS, CandidateProfile, MatchEngine, combine, job_text
from .metrics import cohens_kappa, ndcg_at_k, precision_at_k, precision_recall_f1, spearman
from .preference_scorer import score_preferences
from .recommender import Recommender
from .skill_extractor import SkillExtractor, extract_skills
from .skill_gap import skill_gap_percentage
from .skill_normalizer import normalize_skill
from .skill_scorer import score_skills
from .text_scorer import TextScorer
from .weight_tuner import tune_weights, weight_grid
