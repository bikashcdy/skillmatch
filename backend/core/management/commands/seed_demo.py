from django.core.management.base import BaseCommand

from core.models import Job, User


class Command(BaseCommand):
    help = "Create demo users (admin/recruiter/candidate) and sample jobs."

    def handle(self, *args, **opts):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@demo.com", "admin12345", role="admin")
        rec, _ = User.objects.get_or_create(
            username="recruiter", defaults={"email": "rec@demo.com", "role": "recruiter", "company_name": "TechNepal"})
        rec.set_password("demo12345"); rec.save()
        cand, _ = User.objects.get_or_create(
            username="candidate", defaults={"email": "cand@demo.com", "role": "candidate"})
        cand.set_password("demo12345"); cand.save()

        jobs = [
            ("Django Backend Developer", ["python", "django", "sql", "git", "rest api"], 1, "bachelor"),
            ("React Frontend Developer", ["react", "javascript", "html", "css"], 1, "bachelor"),
            ("Full Stack Developer", ["python", "django", "react", "javascript", "sql"], 2, "bachelor"),
            ("QA Engineer", ["testing", "python", "git", "sql"], 1, "diploma"),
            ("Data Analyst", ["data analysis", "sql", "python"], 1, "bachelor"),
        ]
        for title, skills, exp, edu in jobs:
            Job.objects.get_or_create(recruiter=rec, title=title, defaults=dict(
                company="TechNepal", description=f"We are hiring a {title}.", location="Kathmandu",
                required_skills=skills, min_experience_years=exp, required_education=edu))
        self.stdout.write(self.style.SUCCESS(
            "Demo ready. Logins: admin/admin12345, recruiter/demo12345, candidate/demo12345"))
