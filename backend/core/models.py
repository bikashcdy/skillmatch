"""The database models.

Every model lives in the module of the app that owns it (accounts, jobs, resumes, applications, matching)
but is registered under the single app label "core". That keeps the existing database tables and
migrations (core_user, core_job, ...) valid, so the eight-app split needs no data migration.
"""

from accounts.models import User  # noqa: F401  (must be first: other models point at it)
from jobs.models import NEPAL_TZ, Job, nepal_today  # noqa: F401
from resumes.models import Resume  # noqa: F401
from applications.models import Application  # noqa: F401
from matching.models import RelevanceRating, WeightConfig  # noqa: F401
