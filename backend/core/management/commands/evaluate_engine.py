import json

from django.core.management.base import BaseCommand

from matching.engine import SkillExtractor, precision_recall_f1
from matching.evaluation import evaluate
from matching.services import scorer_for


class Command(BaseCommand):
    help = ("Print Precision@5, NDCG@5, Spearman and Cohen's kappa for the manually rated pairs, and optionally "
            "Precision/Recall/F1 of skill extraction from a labelled file: [{\"text\": \"...\", \"skills\": [\"python\"]}].")

    def add_arguments(self, parser):
        parser.add_argument("--skills-file", help="JSON file with labelled resume texts.")

    def handle(self, *args, **opts):
        for key, value in evaluate(scorer_for()).items():
            self.stdout.write(f"{key}: {value}")
        if opts["skills_file"]:
            with open(opts["skills_file"], encoding="utf-8") as f:
                items = json.load(f)
            extractor = SkillExtractor()
            scores = [precision_recall_f1(extractor.extract(i["text"], with_implied=False), i["skills"]) for i in items]
            n = len(scores) or 1
            self.stdout.write(
                "skill extraction  precision: %.3f  recall: %.3f  F1: %.3f  (%d texts)"
                % (sum(s[0] for s in scores) / n, sum(s[1] for s in scores) / n, sum(s[2] for s in scores) / n, len(scores))
            )
