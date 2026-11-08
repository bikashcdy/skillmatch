from django.core.management.base import BaseCommand, CommandError

from matching.engine import tune_weights
from matching.evaluation import dataset_warnings, rating_groups
from matching.services import scorer_for
from core.models import WeightConfig


class Command(BaseCommand):
    help = "Grid-search the matching weights (steps of 0.05) with NDCG@5 on the manually rated resume/job pairs."

    def add_arguments(self, parser):
        parser.add_argument("--activate", action="store_true", help="Make the tuned weights live.")

    def handle(self, *args, **opts):
        scorer = scorer_for(weights={})
        tuning = rating_groups(scorer, "tune")
        if not tuning:
            raise CommandError("Rate at least 2 jobs for 1 resume in the 'tune' split first (Admin page).")
        testing = rating_groups(scorer, "test")
        result = tune_weights(tuning, testing or None)
        for warning in dataset_warnings(tuning, testing):
            self.stdout.write(self.style.WARNING("Warning: " + warning))
        version = (WeightConfig.objects.order_by("-version").values_list("version", flat=True).first() or 0) + 1
        if opts["activate"]:
            WeightConfig.objects.update(is_active=False)
        WeightConfig.objects.create(
            version=version, weights=result["weights"], tuning_ndcg=result["tuning_ndcg"], test_ndcg=result["test_ndcg"],
            note="Grid search (command)", is_active=opts["activate"],
        )
        for key, value in result.items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(self.style.SUCCESS(f"Saved as version {version}" + (" and activated." if opts["activate"] else ".")))
