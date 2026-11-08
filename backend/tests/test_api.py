import io
import os
import unittest
import tempfile

import docx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APITestCase

from core.models import Application, Resume, User

TEST_MEDIA = tempfile.mkdtemp(prefix="skillmatch_test_media_")


def make_docx(text):
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return SimpleUploadedFile("resume.docx", buf.getvalue())


def upload_confirm(client, upload):
    """Upload a resume and confirm what was scanned, like a candidate does. Returns the last response."""
    up = client.post("/api/resume/", {"resume": upload}, format="multipart")
    if up.status_code != 201:
        return up
    d = up.data
    return client.post(f"/api/resumes/{d['id']}/confirm/", {
        "skills": d["extracted_skills"], "experience_years": d["experience_years"],
        "education_level": d["education_level"], "projects": d["projects"], "certifications": d["certifications"],
    }, format="json")


def apply_file(client, job_id, upload, **extra):
    """Upload + confirm a resume, then apply to the job with it."""
    done = upload_confirm(client, upload)
    if done.status_code != 200:
        return done
    return client.post(f"/api/jobs/{job_id}/apply/", {"resume_id": done.data["id"], **extra}, format="multipart")


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class FullFlowTest(APITestCase):
    def login(self, username, password="Pass@12345"):
        r = self.client.post("/api/auth/login/", {"username": username, "password": password})
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def register(self, **kw):
        self.client.credentials()
        r = self.client.post("/api/auth/register/", {"password": "Pass@12345", **kw})
        self.assertEqual(r.status_code, 201, r.content)

    def post_job(self, **kw):
        r = self.client.post("/api/recruiter/jobs/", kw, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["id"]

    def test_full_flow(self):
        # --- recruiter posts 3 jobs
        self.register(username="recruiter1", email="r@x.com", role="recruiter", company_name="Acme")
        self.login("recruiter1")
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"description": "Build and maintain the company web applications with the team", "title": "Web Developer", "required_skills": ["python"]},
                                          format="json").status_code, 403)       # not approved yet
        User.objects.filter(username="recruiter1").update(is_approved=True)
        self.login("recruiter1")
        backend = self.post_job(title="Backend Dev", description="Build and maintain the company web applications with the team", required_skills=["Python", "Django", "SQL"],
                                min_experience_years=1, required_education="bachelor")
        frontend = self.post_job(title="Frontend Dev", description="Build and maintain the company web applications with the team", required_skills=["ReactJS", "JavaScript", "CSS"],
                                 min_experience_years=1, required_education="bachelor")
        ml = self.post_job(title="ML Engineer", description="Build and maintain the company web applications with the team", required_skills=["machine learning", "python", "pandas", "docker", "aws"],
                           min_experience_years=3, required_education="master")

        qa = self.post_job(title="QA Automation", description="Build and maintain the company web applications with the team", required_skills=["python", "testing", "git"],
                           min_experience_years=1, required_education="bachelor")

        # --- two candidates
        self.register(username="strongone", email="s@x.com", role="candidate")
        self.register(username="weakone", email="w@x.com", role="candidate")

        self.login("strongone")
        strong_cv = "BCA graduate. 3 years experience building Django REST APIs in Python with MySQL, Git and unit testing."
        r = apply_file(self.client, backend, make_docx(strong_cv), auto_apply_related="true")
        self.assertEqual(r.status_code, 201, r.content)
        by_title = {a["job_title"]: a for a in r.data}
        print("\nstrong ->", {k: (v["match_percentage"], v["status"]) for k, v in by_title.items()})
        self.assertGreaterEqual(by_title["Backend Dev"]["match_percentage"], 75.0)
        self.assertFalse(by_title["Backend Dev"]["knockout"])
        self.assertEqual(by_title["Backend Dev"]["skill_score"], 100.0)
        self.assertGreater(by_title["Backend Dev"]["text_score"], 0)
        self.assertIsNone(by_title["Backend Dev"]["preference_score"])   # no preferences set
        self.assertEqual(by_title["Backend Dev"]["status"], "applied")
        self.assertEqual(by_title["QA Automation"]["status"], "auto")   # related job -> auto-applied
        self.assertGreaterEqual(by_title["QA Automation"]["match_percentage"], 75.0)
        self.assertNotIn("Frontend Dev", by_title)           # unrelated, below threshold
        self.assertNotIn("ML Engineer", by_title)

        self.login("weakone")
        weak_cv = "Diploma holder, 1 year experience. Knows Python and some Excel."
        r = apply_file(self.client, backend, make_docx(weak_cv))
        self.assertEqual(r.status_code, 201, r.content)
        print("weak ->", r.data[0]["match_percentage"], r.data[0]["missing_skills"])
        self.assertLess(r.data[0]["match_percentage"], 60)

        # --- recruiter sees ranking and selects best
        self.login("recruiter1")
        r = self.client.get(f"/api/recruiter/jobs/{backend}/candidates/")
        self.assertEqual([a["candidate_name"] for a in r.data], ["strongone", "weakone"])
        r = self.client.post(f"/api/recruiter/jobs/{backend}/select-best/")
        self.assertEqual(r.data["candidate_name"], "strongone")
        self.assertEqual(Application.objects.get(job_id=backend, candidate__username="strongone").status, "selected")

        # --- permissions
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)
        self.login("weakone")
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"title": "x"}, format="json").status_code, 403)

        # --- admin
        User.objects.create_user("boss", password="Pass@12345", role="admin")
        self.login("boss")
        r = self.client.get("/api/admin/stats/")
        self.assertEqual(r.data["applications"], 3)
        self.assertEqual(r.data["recruiters"], 1)


def make_png(lines=None):
    """A PNG: blank if `lines` is None, else the given text drawn large and clear."""
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1400, 700), "white")
    if lines:
        font = ImageFont.load_default(size=44)
        draw = ImageDraw.Draw(img)
        for i, line in enumerate(lines):
            draw.text((40, 30 + i * 70), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return SimpleUploadedFile("resume.png", buf.getvalue(), content_type="image/png")


def ocr_installed():
    from resumes.ocr import ocr_status

    return ocr_status()["available"]


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class UnreadableResumeTest(APITestCase):
    def setUp(self):
        rec = User.objects.create_user("rec", password="pass12345", role="recruiter", company_name="Acme")
        self.job = self.make_job(rec)
        User.objects.create_user("cand", password="pass12345")
        r = self.client.post("/api/auth/login/", {"username": "cand", "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def make_job(self, rec):
        from core.models import Job

        return Job.objects.create(
            recruiter=rec, title="Web Dev", company="Acme", description="d",
            required_skills=["html", "css", "javascript", "php", "sql"],
            min_experience_years=1, required_education="bachelor",
        )

    def apply(self, upload):
        return self.client.post("/api/resume/", {"resume": upload}, format="multipart")

    def test_unsupported_file_type_is_rejected(self):
        r = self.apply(SimpleUploadedFile("virus.exe", b"MZ..."))
        self.assertEqual(r.status_code, 400)
        self.assertIn("Unsupported", r.data["detail"])

    def test_blank_image_gives_clear_error_and_leaves_no_trace(self):
        r = self.apply(make_png())
        self.assertEqual(r.status_code, 400, r.content)
        self.assertTrue(r.data["detail"])
        self.assertEqual(Resume.objects.count(), 0)
        self.assertEqual(Application.objects.count(), 0)

    def test_image_resume_is_read_with_ocr(self):
        if not ocr_installed():
            self.skipTest("OCR (pytesseract + Tesseract program) not installed")
        lines = [
            "BCA Student - PHP Developer",
            "Skills: HTML, CSS, JavaScript, PHP, MySQL, Git",
            "1 Year Experience as a web developer",
            "Bachelor's Degree (Running)",
        ]
        r = apply_file(self.client, self.job.id, make_png(lines))
        self.assertEqual(r.status_code, 201, r.content)
        app = r.data[0]
        print("\nimage resume ->", app["match_percentage"], app["matched_skills"], app["missing_skills"])
        self.assertGreaterEqual(app["match_percentage"], 75)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class SearchAndStatusTest(APITestCase):
    def login(self, username):
        r = self.client.post("/api/auth/login/", {"username": username, "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def setUp(self):
        User.objects.create_user("rec", email="r@x.com", password="pass12345",
                                 role=User.RECRUITER, company_name="Acme")
        for n in ("c1", "c2"):
            User.objects.create_user(n, email=f"{n}@x.com", password="pass12345", role=User.CANDIDATE)
        self.login("rec")
        base = {"description": "Build and maintain the company web applications with the team", "min_experience_years": 0, "required_education": "none"}
        self.j1 = self.client.post("/api/recruiter/jobs/", {**base, "title": "Django Dev",
            "location": "Kathmandu", "required_skills": ["Python", "Django"]}, format="json").data["id"]
        self.client.post("/api/recruiter/jobs/", {**base, "title": "Designer",
            "location": "Remote", "required_skills": ["CSS", "HTML"]}, format="json")

    def test_filters_and_meta(self):
        self.login("c1")
        get = lambda **p: [j["title"] for j in self.client.get("/api/jobs/", p).data]
        self.assertEqual(len(get()), 2)
        self.assertEqual(get(location="kath"), ["Django Dev"])
        self.assertEqual(get(skill="python"), ["Django Dev"])
        self.assertEqual(get(q="css"), ["Designer"])
        meta = self.client.get("/api/jobs/meta/").data
        self.assertEqual(meta["stats"]["jobs"], 2)
        self.assertNotIn("locations", meta)           # candidates get no city list

    def test_duplicate_apply_missing_job_and_single_selected(self):
        for n in ("c1", "c2"):
            self.login(n)
            r = apply_file(self.client, self.j1, make_docx("I know Python and Django. " * 3))
            self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(self.client.post(f"/api/jobs/{self.j1}/apply/").status_code, 400)
        self.assertEqual(self.client.post("/api/jobs/9999/apply/").status_code, 404)
        self.login("rec")
        apps = self.client.get(f"/api/recruiter/jobs/{self.j1}/candidates/").data
        for a in apps:
            self.assertEqual(self.client.post(f"/api/recruiter/applications/{a['id']}/status/",
                                              {"status": "selected"}, format="json").status_code, 200)
        self.assertEqual(Application.objects.filter(status="selected").count(), 1)
        self.assertEqual(self.client.get("/api/recruiter/jobs/9999/candidates/").status_code, 404)
        admin = User.objects.create_user("adm", password="pass12345", role=User.ADMIN)
        self.login("adm")
        self.assertEqual(self.client.post(f"/api/admin/users/{admin.id}/toggle/").status_code, 400)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class RecommendationTest(APITestCase):
    def setUp(self):
        rec = User.objects.create_user("rec", email="r@x.com", password="pass12345",
                                       role=User.RECRUITER, company_name="Acme")
        User.objects.create_user("cand", email="c@x.com", password="pass12345", role=User.CANDIDATE)
        from core.models import Job
        for t, sk, city in [("Backend", ["python", "django", "docker"], "Pokhara"),
                            ("Fullstack", ["python", "django", "react", "docker"], "Kathmandu")]:
            Job.objects.create(recruiter=rec, title=t, company="Acme", description="d", location=city,
                               required_skills=sk, min_experience_years=2, required_education="bachelor")
        r = self.client.post("/api/auth/login/", {"username": "cand", "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def test_no_resume_then_recommendations(self):
        self.assertFalse(self.client.get("/api/recommendations/").data["has_resume"])
        bad = self.client.post("/api/resume/", {"resume": SimpleUploadedFile("a.exe", b"x")}, format="multipart")
        self.assertEqual(bad.status_code, 400)
        ok = upload_confirm(self.client, make_docx("I know Python and Django. BCA student. " * 2))
        self.assertEqual(ok.status_code, 200, ok.content)
        d = self.client.get("/api/recommendations/").data
        self.assertTrue(d["has_resume"])
        self.assertEqual(d["skill_gaps"][0]["skill"], "docker")      # needed by both jobs
        self.assertEqual(d["skill_gaps"][0]["jobs_needing"], 2)
        self.assertGreater(d["skill_gaps"][0]["avg_gain"], 0)
        self.assertTrue(d["skill_gaps"][0]["resources"][0]["url"].startswith("https://"))
        self.assertGreaterEqual(d["avg_after"], d["avg_now"])
        self.assertTrue(any(t["area"] == "Experience" for t in d["tips"]))
        cities = self.client.get("/api/jobs/meta/").data["cities"]
        self.assertIn("Pokhara", cities)
        self.assertIn("Butwal", cities)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class V2FeaturesTest(APITestCase):
    def login(self, username):
        r = self.client.post("/api/auth/login/", {"username": username, "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def setUp(self):
        User.objects.create_user("rec", email="rec@x.com", password="pass12345",
                                 role=User.RECRUITER, company_name="Acme")
        User.objects.create_user("cand", email="cand@x.com", password="pass12345", role=User.CANDIDATE)
        self.cv = lambda: make_docx("Python Django developer. Skills: python django git sql. BCA 2021-2025. " * 2)

    def post_job(self, **kw):
        base = {"title": "Backend", "description": "Build and maintain the company web applications with the team", "location": "Pokhara", "min_experience_years": 0,
                "required_education": "none", "required_skills": ["Python", "Django"]}
        r = self.client.post("/api/recruiter/jobs/", {**base, **kw}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["id"]

    def test_emails_strong_match_decision_note_and_reply_to(self):
        from django.core import mail
        self.login("rec")
        job = self.post_job()
        self.login("cand")
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            upload_confirm(self.client, self.cv())
            self.assertEqual(self.client.post(f"/api/jobs/{job}/apply/").status_code, 201)
        self.assertEqual([m.to for m in mail.outbox], [["rec@x.com"]])            # ONE strong-match email to the recruiter
        self.assertEqual(mail.outbox[0].reply_to, ["cand@x.com"])

        self.login("rec")
        app = self.client.get(f"/api/recruiter/jobs/{job}/candidates/").data[0]["id"]
        mail.outbox.clear()
        r = self.client.post(f"/api/recruiter/applications/{app}/note/", {"note": "Interview on Sunday"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.client.post(f"/api/recruiter/applications/{app}/status/", {"status": "selected"}, format="json")
        self.assertIn("selected", mail.outbox[-1].subject.lower())
        self.assertIn("Interview on Sunday", mail.outbox[-1].body)
        for m in mail.outbox[-2:]:                      # sent "from" the recruiter's company, replies go to them
            self.assertTrue(m.from_email.startswith("Acme via JobMitra"))
            self.assertEqual(m.reply_to, ["rec@x.com"])
        self.login("cand")
        self.assertEqual(self.client.get("/api/my-applications/").data[0]["recruiter_note"], "Interview on Sunday")

    def test_many_strong_matches_send_one_email(self):
        from django.core import mail
        self.login("rec")
        for i in range(3):
            self.post_job(title="Engineer " + chr(65 + i))
        self.login("cand")
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            j = self.client.get("/api/jobs/").data[0]["id"]
            apply_file(self.client, j, self.cv(), auto_apply_related="true")
        self.assertEqual(len(mail.outbox), 1)                                      # not 3
        self.assertIn("3 strong matches", mail.outbox[0].subject)

    def test_filters(self):
        self.login("rec")
        self.post_job(title="Intern", job_type="internship", salary_min=10000, salary_max=15000)
        self.post_job(title="Senior", job_type="full_time", salary_min=80000, salary_max=120000, location="Kathmandu")
        bad = self.client.post("/api/recruiter/jobs/", {"title": "x", "description": "d", "required_skills": ["python"],
                               "salary_min": 50, "salary_max": 10}, format="json")
        self.assertEqual(bad.status_code, 400)
        self.login("cand")
        titles = lambda **p: sorted(j["title"] for j in self.client.get("/api/jobs/", p).data)
        self.assertEqual(titles(job_type="internship"), ["Intern"])
        self.assertEqual(titles(min_salary=50000), ["Senior"])
        self.assertEqual(titles(location="Kathmandu"), ["Senior"])
        self.assertEqual(titles(location="Dharan"), [])                            # no jobs there -> empty result

    def test_scanner_and_health(self):
        from matching.engine import extract_skills, normalize_skill
        from resumes.health import resume_health
        self.assertEqual(normalize_skill("Javascripts"), "javascript")
        self.assertEqual(normalize_skill("Laravel"), "laravel")
        skills = extract_skills("Figma, SEO, Tally and Django")
        for s in ("figma", "digital marketing", "accounting", "django", "python"):   # python is implied
            self.assertIn(s, skills)
        weak = resume_health("I am a student.")
        good = resume_health("Ram ram@x.com 9841234567 skills python education BCA 2021-2025 projects built github.com/r " + "word " * 160)
        self.assertLess(weak["score"], 30)
        self.assertGreater(good["score"], 80)
        self.assertTrue(any(not c["ok"] and c["tip"] for c in weak["checks"]))

    def test_upload_returns_health_and_recommendations_has_it(self):
        self.login("cand")
        r = self.client.post("/api/resume/", {"resume": self.cv()}, format="multipart")
        self.assertIn("score", r.data["health"])
        self.assertFalse(r.data["confirmed"])  # must be reviewed first
        self.assertFalse(self.client.get("/api/recommendations/").data["has_resume"])
        self.client.post(f"/api/resumes/{r.data['id']}/confirm/", {"skills": r.data["extracted_skills"]}, format="json")
        self.assertIn("health", self.client.get("/api/recommendations/").data)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ExpiryAndDetailTest(APITestCase):
    def login(self, username):
        r = self.client.post("/api/auth/login/", {"username": username, "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def setUp(self):
        User.objects.create_user("rec", email="r@x.com", password="pass12345", role=User.RECRUITER, company_name="Acme")
        User.objects.create_user("cand", email="c@x.com", password="pass12345", role=User.CANDIDATE)
        self.login("rec")

    def post(self, **kw):
        base = {"title": "Dev", "description": "Build and maintain the company web applications with the team", "location": "Pokhara", "required_skills": ["python"],
                "min_experience_years": 0, "required_education": "bachelor"}
        return self.client.post("/api/recruiter/jobs/", {**base, **kw}, format="json")

    def test_default_deadline_fresher_and_past_date_rejected(self):
        import datetime
        from core.models import nepal_today
        r = self.post()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["min_experience_years"], 0)                       # fresher
        self.assertEqual(r.data["expires_at"], str(nepal_today() + datetime.timedelta(days=30)))
        self.assertEqual(r.data["days_left"], 30)
        past = self.post(expires_at=str(nepal_today() - datetime.timedelta(days=1)))
        self.assertEqual(past.status_code, 400)

    def test_expired_jobs_disappear_for_candidates(self):
        import datetime
        from core.models import Job, nepal_today
        keep = self.post(title="Keep").data["id"]
        gone = self.post(title="Gone").data["id"]
        today_job = self.post(title="LastDay", expires_at=str(nepal_today())).data["id"]   # still valid today
        Job.objects.filter(pk=gone).update(expires_at=nepal_today() - datetime.timedelta(days=1))
        self.login("cand")
        titles = sorted(j["title"] for j in self.client.get("/api/jobs/").data)
        self.assertEqual(titles, ["Keep", "LastDay"])
        self.assertEqual(self.client.get(f"/api/jobs/{gone}/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/jobs/{gone}/apply/").status_code, 404)
        self.assertEqual(self.client.get("/api/jobs/meta/").data["stats"]["jobs"], 2)
        # recruiter still sees (and can extend) the expired job
        self.login("rec")
        mine = {j["title"]: j for j in self.client.get("/api/recruiter/jobs/").data}
        self.assertTrue(mine["Gone"]["is_expired"])
        ok = self.client.patch(f"/api/recruiter/jobs/{gone}/",
                               {"expires_at": str(nepal_today() + datetime.timedelta(days=7))}, format="json")
        self.assertEqual(ok.status_code, 200, ok.content)
        self.login("cand")
        self.assertEqual(self.client.get(f"/api/jobs/{gone}/").status_code, 200)

    def test_detail_has_everything_and_match_breakdown(self):
        job = self.post(title="Backend", required_skills=["python", "django"], min_experience_years=2).data["id"]
        self.login("cand")
        upload_confirm(self.client, make_docx("I know Python. BCA 2021-2025. " * 5))
        d = self.client.get(f"/api/jobs/{job}/").data
        for key in ("description", "required_skills", "required_education", "min_experience_years",
                    "created_at", "expires_at", "days_left", "location", "company"):
            self.assertIn(key, d)
        self.assertEqual(d["match_detail"]["matched_skills"], ["python"])
        self.assertEqual(d["match_detail"]["missing_skills"], ["django"])
        self.assertIsNotNone(d["resume_match"])


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class AccountRulesTest(APITestCase):
    GOOD = {"username": "ram_sharma", "email": "Ram.Sharma@Example.com", "password": "Strong@123", "role": "candidate"}

    def post(self, **kw):
        self.client.credentials()
        return self.client.post("/api/auth/register/", {**self.GOOD, **kw}, format="json")

    def login(self, username, password="Strong@123"):
        r = self.client.post("/api/auth/login/", {"username": username, "password": password})
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        return r

    def test_username_rules(self):
        for bad in ("abc", "a" * 21, "ram sharma", "1ram_sharma", "ram-sharma", "ram@sharma", "_ramsharma", ""):
            r = self.post(username=bad)
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("username", r.data, bad)
        self.assertEqual(self.post().status_code, 201)
        dup = self.post(username="RAM_SHARMA", email="other@example.com")           # case-insensitive duplicate
        self.assertEqual(dup.status_code, 400)
        self.assertIn("already taken", str(dup.data["username"]))

    def test_email_rules(self):
        for bad in ("", "ram", "ram@", "ram@gmail", "@gmail.com", "ram@gmail..com", "ram sharma@gmail.com", "ram@@gmail.com"):
            r = self.post(email=bad)
            self.assertEqual(r.status_code, 400, bad)
            self.assertIn("email", r.data, bad)
        self.assertEqual(self.post().status_code, 201)
        dup = self.post(username="someone_else", email="ram.sharma@example.com")    # same email, different case
        self.assertEqual(dup.status_code, 400)
        self.assertIn("already exists", str(dup.data["email"]))
        from core.models import User as U
        self.assertEqual(U.objects.get(username="ram_sharma").email, "ram.sharma@example.com")  # stored lower-case

    def test_password_rules(self):
        cases = {"Short@1": "8-64", "alllower@123": "uppercase", "ALLUPPER@123": "lowercase", "NoNumber@abc": "number",
                 "NoSpecial123": "special", "Has Space@123": "spaces", "Ram_sharma@123": "username", "Ram.Sharma@123": "email"}
        for pw, word in cases.items():
            r = self.post(password=pw)
            self.assertEqual(r.status_code, 400, pw)
            self.assertIn(word, str(r.data["password"]), pw)
        self.assertEqual(self.post().status_code, 201)

    def test_recruiter_needs_company_and_approval(self):
        r = self.post(role="recruiter", company_name="A")
        self.assertEqual(r.status_code, 400)
        self.assertIn("company_name", r.data)
        r = self.post(role="recruiter", company_name="TechNepal")
        self.assertEqual(r.status_code, 201)
        self.assertTrue(r.data["waiting_for_approval"])
        self.assertEqual(self.post(role="admin", username="evil_admin", email="e@example.com").status_code, 400)

    def test_live_check_endpoint(self):
        self.post()
        r = self.client.post("/api/auth/check/", {"username": "ram_sharma", "email": "nope"}, format="json")
        self.assertIn("already taken", str(r.data["username"]))
        self.assertTrue(r.data["email"])
        self.assertEqual(self.client.post("/api/auth/check/", {"username": "fresh_name", "email": "fresh@example.com"},
                                          format="json").data, {"username": [], "email": []})

    def test_forgot_and_reset_password(self):
        from django.core import mail
        import re
        self.post()
        mail.outbox.clear()
        r = self.client.post("/api/auth/forgot-password/", {"email": "nobody@example.com"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)                                       # same answer, no email, nobody revealed
        self.client.post("/api/auth/forgot-password/", {"email": "RAM.SHARMA@example.com"}, format="json")
        self.assertEqual(len(mail.outbox), 1)
        link = re.search(r"uid=([^&\s]+)&token=(\S+)", mail.outbox[0].body)
        uid, token = link.group(1), link.group(2)
        weak = self.client.post("/api/auth/reset-password/", {"uid": uid, "token": token, "password": "weak"}, format="json")
        self.assertEqual(weak.status_code, 400)
        bad_token = self.client.post("/api/auth/reset-password/", {"uid": uid, "token": "x-y", "password": "Brand@New99"}, format="json")
        self.assertEqual(bad_token.status_code, 400)
        ok = self.client.post("/api/auth/reset-password/", {"uid": uid, "token": token, "password": "Brand@New99"}, format="json")
        self.assertEqual(ok.status_code, 200, ok.content)
        self.login("ram_sharma", "Brand@New99")
        again = self.client.post("/api/auth/reset-password/", {"uid": uid, "token": token, "password": "Another@99x"}, format="json")
        self.assertEqual(again.status_code, 400)                                    # a link works only once

    def test_change_password_and_profile(self):
        self.post()
        self.login("ram_sharma")
        self.assertEqual(self.client.post("/api/auth/change-password/", {"old_password": "wrong", "new_password": "Brand@New99"},
                                          format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/auth/change-password/", {"old_password": "Strong@123", "new_password": "weak"},
                                          format="json").status_code, 400)
        self.assertEqual(self.client.post("/api/auth/change-password/", {"old_password": "Strong@123", "new_password": "Brand@New99"},
                                          format="json").status_code, 200)
        self.login("ram_sharma", "Brand@New99")
        self.assertEqual(self.client.patch("/api/auth/me/", {"email": "bad"}, format="json").status_code, 400)
        r = self.client.patch("/api/auth/me/", {"email": "new.mail@example.com"}, format="json")
        self.assertEqual(r.data["email"], "new.mail@example.com")


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class PrivacyAndAdminTest(APITestCase):
    def login(self, username):
        r = self.client.post("/api/auth/login/", {"username": username, "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def setUp(self):
        from core.models import Job
        self.rec = User.objects.create_user("recruiter1", email="r@x.com", password="pass12345", role=User.RECRUITER, company_name="Acme")
        self.rec2 = User.objects.create_user("recruiter2", email="r2@x.com", password="pass12345", role=User.RECRUITER, company_name="Other")
        self.cand = User.objects.create_user("candidate1", email="c@x.com", password="pass12345")
        User.objects.create_user("stranger1", email="s@x.com", password="pass12345")
        self.admin = User.objects.create_user("admin1", email="a@x.com", password="pass12345", role=User.ADMIN)
        self.job = Job.objects.create(recruiter=self.rec, title="Dev", company="Acme", description="d", location="Pokhara",
                                      required_skills=["python"])
        self.login("candidate1")
        apply_file(self.client, self.job.id, make_docx("Python developer. BCA 2022. " * 5))
        self.resume = Resume.objects.get(user=self.cand)

    def test_resume_files_are_private(self):
        url = f"/api/resumes/{self.resume.id}/file/"
        self.client.credentials()
        self.assertEqual(self.client.get(url).status_code, 401)                      # not logged in
        self.assertEqual(self.client.get("/media/" + self.resume.file.name).status_code, 404)   # no public media route
        for who, code in (("candidate1", 200), ("recruiter1", 200), ("admin1", 200), ("recruiter2", 404), ("stranger1", 404)):
            self.login(who)
            self.assertEqual(self.client.get(url).status_code, code, who)

    def test_withdraw_and_delete_resume(self):
        self.login("candidate1")
        self.assertEqual(self.client.delete(f"/api/resumes/{self.resume.id}/").status_code, 400)    # still used
        app = Application.objects.get(candidate=self.cand)
        self.assertEqual(self.client.delete(f"/api/my-applications/{app.id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/resumes/{self.resume.id}/").status_code, 204)
        self.assertFalse(Resume.objects.filter(pk=self.resume.id).exists())
        self.assertEqual(self.client.get("/api/resumes/").data, [])

    def test_cannot_withdraw_when_selected_or_someone_elses(self):
        app = Application.objects.get(candidate=self.cand)
        app.status = "selected"; app.save()
        self.login("candidate1")
        self.assertEqual(self.client.delete(f"/api/my-applications/{app.id}/").status_code, 400)
        self.login("stranger1")
        self.assertEqual(self.client.delete(f"/api/my-applications/{app.id}/").status_code, 404)

    def test_admin_approval_and_job_removal(self):
        from django.core import mail
        self.rec.is_approved = False; self.rec.save()
        self.login("candidate1")
        self.assertEqual(self.client.get("/api/jobs/").data, [])                     # unapproved recruiter's jobs are hidden
        self.login("recruiter1")
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"description": "Build and maintain the company web applications with the team", "title": "Web Developer", "required_skills": ["python"]},
                                          format="json").status_code, 403)
        self.login("candidate1")
        self.assertEqual(self.client.post(f"/api/admin/users/{self.rec.id}/approve/").status_code, 403)
        self.login("admin1")
        mail.outbox.clear()
        r = self.client.post(f"/api/admin/users/{self.rec.id}/approve/", {"approved": True}, format="json")
        self.assertTrue(r.data["is_approved"])
        self.assertEqual(mail.outbox[0].to, ["r@x.com"])
        users = {u["username"]: u for u in self.client.get("/api/admin/users/").data}
        self.assertIn("company_name", users["recruiter1"])
        self.assertEqual(len(self.client.get("/api/admin/jobs/").data), 1)
        self.assertEqual(self.client.delete(f"/api/admin/jobs/{self.job.id}/").status_code, 204)
        self.assertEqual(self.client.get("/api/admin/jobs/").data, [])
        self.login("candidate1")
        self.assertEqual(self.client.get("/api/admin/jobs/").status_code, 403)


class JobPostValidationTest(APITestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        U = get_user_model()
        self.rec = U.objects.create_user("hirer_a", "hirer_a@example.com", "Pass@12345", role="recruiter",
                                         company_name="Acme", is_approved=True)
        self.client.force_authenticate(self.rec)
        self.ok = {"title": "Python Developer", "description": "Build and maintain our web applications with the team",
                   "location": "Pokhara", "required_skills": ["python"], "min_experience_years": 0}

    def post(self, **over):
        return self.client.post("/api/recruiter/jobs/", {**self.ok, **over}, format="json")

    def test_valid_job_is_accepted(self):
        self.assertEqual(self.post().status_code, 201)

    def test_bad_titles_rejected(self):
        for t in ["12345", "Dev 99", "ab", "!!!", "   ", "x" * 81]:
            r = self.post(title=t)
            self.assertEqual(r.status_code, 400, t)
            self.assertIn("title", r.data)

    def test_bad_descriptions_rejected(self):
        for d in ["short", "1234567890 1234567890 1234567890 1234567890", "aa aa aa aa aa aa aa aa aa aa aa aa", "x" * 3001]:
            r = self.post(description=d)
            self.assertEqual(r.status_code, 400, d)
            self.assertIn("description", r.data)

    def test_bad_locations_rejected(self):
        for loc in ["12345", "Pokhara 44", "@@"]:
            self.assertEqual(self.post(location=loc).status_code, 400, loc)

    def test_deactivated_recruiter_jobs_disappear(self):
        job_id = self.post().data["id"]
        cand = __import__("django.contrib.auth", fromlist=["x"]).get_user_model().objects.create_user(
            "cand_a", "cand_a@example.com", "Pass@12345", role="candidate")
        self.client.force_authenticate(cand)
        self.assertEqual(self.client.get("/api/jobs/").data and len(self.client.get("/api/jobs/").data), 1)
        self.rec.is_active = False
        self.rec.save()
        self.assertEqual(len(self.client.get("/api/jobs/").data), 0)
        self.assertEqual(self.client.get(f"/api/jobs/{job_id}/").status_code, 404)
        self.rec.is_active = True
        self.rec.save()
        self.assertEqual(len(self.client.get("/api/jobs/").data), 1)


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class AlgorithmIntegrationTest(APITestCase):
    """The new matching rules through the API: confirm step, nice-to-have skills, preferences, tuning."""

    CV = "BCA graduate. 2 years experience. Skills: Python, Django, MySQL, Git.\nProjects:\n- Built a job portal with Django\nCertifications:\n- Python course by Coursera\n"

    def setUp(self):
        from core.models import Job

        self.rec = User.objects.create_user("hirer", email="h@x.com", password="Pass@12345", role=User.RECRUITER,
                                            company_name="Acme", is_approved=True)
        self.cand = User.objects.create_user("seeker", email="s@x.com", password="Pass@12345", role=User.CANDIDATE)
        self.admin = User.objects.create_user("boss", email="b@x.com", password="Pass@12345", role=User.ADMIN)
        desc = "Build and maintain the company web applications with the team"
        self.job = Job.objects.create(recruiter=self.rec, title="Backend Developer", company="Acme", description=desc,
                                      location="Pokhara", required_skills=["python", "django"],
                                      nice_to_have_skills=["docker"], min_experience_years=1, required_education="bachelor")
        self.docker_job = Job.objects.create(recruiter=self.rec, title="DevOps Engineer", company="Acme", description=desc,
                                             location="Kathmandu", required_skills=["docker", "python"], job_type="internship")
        self.client.force_authenticate(self.cand)

    def upload(self, text=None):
        return self.client.post("/api/resume/", {"resume": make_docx(text or self.CV)}, format="multipart")

    def test_scan_extracts_sections_and_needs_confirmation(self):
        r = self.upload()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertFalse(r.data["confirmed"])
        self.assertIn("python", r.data["extracted_skills"])
        self.assertEqual(r.data["projects"], ["Built a job portal with Django"])
        self.assertEqual(r.data["certifications"], ["Python course by Coursera"])
        apply = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume_id": r.data["id"]}, format="json")
        self.assertEqual(apply.status_code, 400)  # not confirmed yet
        self.assertIn("confirm", apply.data["detail"])

    def test_applying_with_a_file_directly_is_refused(self):
        r = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume": make_docx(self.CV)}, format="multipart")
        self.assertEqual(r.status_code, 400)

    def test_candidate_corrections_are_kept_and_validated(self):
        r = self.upload()
        rid = r.data["id"]
        bad = self.client.post(f"/api/resumes/{rid}/confirm/", {"skills": [], "experience_years": -3,
                                                               "education_level": "wizard"}, format="json")
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(set(bad.data), {"skills", "experience_years", "education_level"})
        ok = self.client.post(f"/api/resumes/{rid}/confirm/", {
            "skills": ["python", "django", "ReactJS"], "experience_years": 3, "education_level": "master",
            "projects": ["My project"], "certifications": []}, format="json")
        self.assertEqual(ok.status_code, 200, ok.content)
        self.assertTrue(ok.data["confirmed"])
        self.assertIn("react", ok.data["extracted_skills"])  # ReactJS was normalised
        # opening the job list re-scans resumes, but the candidate's edited skills must survive
        self.client.get("/api/jobs/")
        self.assertIn("react", Resume.objects.get(pk=rid).extracted_skills)
        self.assertNotIn("git", Resume.objects.get(pk=rid).extracted_skills)

    def test_manual_entry_fallback(self):
        blank = self.client.post("/api/resume/", {"resume": make_png()}, format="multipart")
        self.assertEqual(blank.status_code, 400)
        self.assertTrue(blank.data["manual_entry"])
        r = self.client.post("/api/resume/manual/", {"skills": ["python", "sql"], "experience_years": 1,
                                                     "education_level": "bachelor"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(r.data["manual"] and r.data["confirmed"])
        apply = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume_id": r.data["id"]}, format="json")
        self.assertEqual(apply.status_code, 201, apply.content)
        self.assertGreater(apply.data[0]["match_percentage"], 0)

    def test_knockout_nice_to_have_and_breakdown_are_stored(self):
        done = upload_confirm(self.client, make_docx(self.CV))
        ok = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume_id": done.data["id"]}, format="json").data[0]
        self.assertFalse(ok["knockout"])  # docker is only nice-to-have here
        self.assertEqual(ok["missing_skills"], ["docker"])
        self.assertEqual(ok["skill_gap"], round(100 / 3, 1))
        blocked = self.client.post(f"/api/jobs/{self.docker_job.id}/apply/", {"resume_id": done.data["id"]}, format="json").data[0]
        self.assertTrue(blocked["knockout"])
        self.assertLessEqual(blocked["match_percentage"], 60)

    def test_related_jobs_skip_knocked_out_jobs(self):
        done = upload_confirm(self.client, make_docx(self.CV))
        r = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume_id": done.data["id"], "auto_apply_related": "true"}, format="json")
        titles = [a["job_title"] for a in r.data]
        self.assertEqual(titles, ["Backend Developer"])  # DevOps misses must-have docker

    def test_preferences_are_validated_and_scored(self):
        self.assertEqual(self.client.patch("/api/auth/me/", {"preferred_location": "Pokhara 99"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch("/api/auth/me/", {"preferred_job_type": "forever"}, format="json").status_code, 400)
        ok = self.client.patch("/api/auth/me/", {"preferred_location": "Pokhara", "preferred_job_type": "full_time"}, format="json")
        self.assertEqual((ok.data["preferred_location"], ok.data["preferred_job_type"]), ("Pokhara", "full_time"))
        done = upload_confirm(self.client, make_docx(self.CV))
        app = self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume_id": done.data["id"]}, format="json").data[0]
        self.assertEqual(app["preference_score"], 100.0)
        other = self.client.post(f"/api/jobs/{self.docker_job.id}/apply/", {"resume_id": done.data["id"]}, format="json").data[0]
        self.assertEqual(other["preference_score"], 0.0)

    def test_recruiter_nice_to_have_is_saved_without_duplicates(self):
        self.client.force_authenticate(self.rec)
        r = self.client.post("/api/recruiter/jobs/", {
            "title": "Frontend Developer", "description": "Build and maintain the company web applications with the team",
            "location": "Pokhara", "required_skills": ["react"], "nice_to_have_skills": ["ReactJS", "typescript", "css"],
            "min_experience_years": 0}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["nice_to_have_skills"], ["css", "typescript"])  # react is already must-have

    def test_what_if_and_learning_path(self):
        upload_confirm(self.client, make_docx(self.CV))
        r = self.client.post("/api/recommendations/what-if/", {"skills": ["docker"]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertGreaterEqual(r.data["avg_after"], r.data["avg_before"])
        self.assertIn("docker", r.data["skills"])
        self.assertTrue(any(row["title"] == "DevOps Engineer" and row["after"] > row["before"] for row in r.data["jobs"]))
        self.assertEqual(self.client.post("/api/recommendations/what-if/", {"skills": []}, format="json").status_code, 400)
        rec = self.client.get("/api/recommendations/").data
        self.assertIn("learning_path", rec)
        path = [p["skill"] for p in rec["learning_path"]]
        self.assertEqual(path, sorted(set(path), key=path.index))  # no duplicates
        # the candidate's real skills were not changed by the simulation
        self.assertNotIn("docker", Resume.objects.get(user=self.cand).extracted_skills)

    def test_admin_tuning_flow(self):
        done = upload_confirm(self.client, make_docx(self.CV))
        rid = done.data["id"]
        self.assertEqual(self.client.get("/api/admin/weights/").status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post("/api/admin/weights/tune/").status_code, 400)  # nothing rated yet
        self.assertEqual(self.client.post("/api/admin/ratings/", {"resume": rid, "job": self.job.id, "rating": 7}, format="json").status_code, 400)
        for job, rating in ((self.job, 3), (self.docker_job, 0)):
            self.assertEqual(self.client.post("/api/admin/ratings/", {"resume": rid, "job": job.id, "rating": rating}, format="json").status_code, 201)
        tuned = self.client.post("/api/admin/weights/tune/")
        self.assertEqual(tuned.status_code, 201, tuned.content)
        self.assertAlmostEqual(sum(tuned.data["weights"].values()), 1.0, places=6)
        self.assertEqual(tuned.data["tuning_ndcg"], 1.0)
        data = self.client.get("/api/admin/weights/").data
        self.assertEqual(data["counts"]["tune"], 2)
        self.assertIsNotNone(data["evaluation"]["ndcg_at_5"])
        self.assertEqual(data["active_version"], 0)  # tuned weights are not live until activated
        cid = tuned.data["config"]["id"]
        self.assertEqual(self.client.post(f"/api/admin/weights/{cid}/activate/").status_code, 200)
        self.assertEqual(self.client.get("/api/admin/weights/").data["active_version"], tuned.data["config"]["version"])
        self.assertEqual(self.client.post("/api/admin/weights/reset/").status_code, 200)
        self.assertEqual(self.client.get("/api/admin/weights/").data["active_version"], 0)


@unittest.skipUnless(ocr_installed(), "OCR (pytesseract + Tesseract program) not installed")
class OcrReadingTest(SimpleTestCase):
    """Photos and scanned resumes are read with OCR."""

    LINES = ["Anita Sharma - Python Developer", "Skills: Python, Django, MySQL, Git", "BCA 2024 - 2 years experience"]

    def image(self, width=1400):
        from PIL import Image

        img = Image.open(io.BytesIO(make_png(self.LINES).read()))
        if width != 1400:  # a smaller, lower quality copy like a quick phone screenshot
            img = img.resize((width, int(img.height * width / 1400)))
        return img

    def path(self, name, save):
        os.makedirs(TEST_MEDIA, exist_ok=True)
        path = os.path.join(TEST_MEDIA, name)
        save(path)
        return path

    def assertRead(self, text):
        low = text.lower()
        for word in ("python", "django", "mysql", "bca"):
            self.assertIn(word, low)

    def test_photo_png(self):
        from resumes.parser import extract_text

        self.assertRead(extract_text(self.path("ocr1.png", lambda p: self.image().save(p))))

    def test_small_low_quality_jpeg_is_enlarged_and_read(self):
        from resumes.parser import extract_text

        self.assertRead(extract_text(self.path("ocr2.jpg", lambda p: self.image(700).save(p, quality=50))))

    def test_scanned_pdf_is_read_page_by_page(self):
        from resumes.parser import extract_text

        def save(p):
            first, second = self.image(), self.image()
            first.save(p, "PDF", save_all=True, append_images=[second])

        text = extract_text(self.path("ocr3.pdf", save))
        self.assertRead(text)
        self.assertGreaterEqual(text.lower().count("python"), 2)  # both pages were read

    def test_status_reports_available(self):
        from resumes.ocr import ocr_status

        self.assertTrue(ocr_status()["available"])
