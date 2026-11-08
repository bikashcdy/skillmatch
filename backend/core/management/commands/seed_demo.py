from django.core.management.base import BaseCommand

import datetime

from core.models import Job, User, nepal_today


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

        # (title, must-have skills, nice-to-have skills, years, education, what the job is about)
        jobs = [
            ("Django Backend Developer", ["python", "django", "sql"], ["git", "rest api", "docker"], 1, "bachelor",
             "Build and maintain REST APIs and database models for our web products using Django and MySQL. "
             "You will write clean tested code, review pull requests and work with the frontend team."),
            ("React Frontend Developer", ["react", "javascript", "html", "css"], ["typescript", "git"], 1, "bachelor",
             "Create fast, responsive user interfaces in React. You will turn designs into reusable components, "
             "connect them to our APIs and keep the experience smooth on mobile phones."),
            ("Full Stack Developer", ["python", "django", "react", "javascript"], ["sql", "docker"], 2, "bachelor",
             "Own features from database to screen. Build Django APIs and React pages, deploy releases "
             "and help the team improve performance and code quality."),
            ("QA Engineer", ["testing", "python"], ["git", "sql"], 1, "diploma",
             "Plan and run manual and automated tests for our web applications. You will write test cases, "
             "report bugs clearly and help developers fix them before release."),
            ("Data Analyst", ["data analysis", "sql"], ["python"], 1, "bachelor",
             "Turn business data into clear reports and dashboards. You will clean data, write SQL queries "
             "and explain the numbers to managers so they can decide faster."),
        ]
        cities = ["Kathmandu", "Pokhara", "Lalitpur", "Butwal", "Biratnagar"]
        for (title, must, nice, exp, edu, about), city in zip(jobs, cities):
            Job.objects.update_or_create(recruiter=rec, title=title, defaults=dict(
                company="TechNepal", description=about, location=city,
                required_skills=must, nice_to_have_skills=nice, min_experience_years=exp, required_education=edu,
                expires_at=nepal_today() + datetime.timedelta(days=30)))
        self.stdout.write(self.style.SUCCESS(
            "Demo ready. Logins: admin/admin12345, recruiter/demo12345, candidate/demo12345"))
