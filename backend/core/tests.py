import io
import tempfile

import docx
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework.test import APITestCase

from .models import Application, Resume, User

TEST_MEDIA = tempfile.mkdtemp(prefix="skillmatch_test_media_")


def make_docx(text):
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return SimpleUploadedFile("resume.docx", buf.getvalue())


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
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"title": "x", "description": "d", "required_skills": ["python"]},
                                          format="json").status_code, 403)       # not approved yet
        User.objects.filter(username="recruiter1").update(is_approved=True)
        self.login("recruiter1")
        backend = self.post_job(title="Backend Dev", description="d", required_skills=["Python", "Django", "SQL"],
                                min_experience_years=1, required_education="bachelor")
        frontend = self.post_job(title="Frontend Dev", description="d", required_skills=["ReactJS", "JavaScript", "CSS"],
                                 min_experience_years=1, required_education="bachelor")
        ml = self.post_job(title="ML Engineer", description="d", required_skills=["machine learning", "python", "pandas", "docker", "aws"],
                           min_experience_years=3, required_education="master")

        qa = self.post_job(title="QA Automation", description="d", required_skills=["python", "testing", "git"],
                           min_experience_years=1, required_education="bachelor")

        # --- two candidates
        self.register(username="strongone", email="s@x.com", role="candidate")
        self.register(username="weakone", email="w@x.com", role="candidate")

        self.login("strongone")
        strong_cv = "BCA graduate. 3 years experience building Django REST APIs in Python with MySQL, Git and unit testing."
        r = self.client.post(f"/api/jobs/{backend}/apply/",
                             {"resume": make_docx(strong_cv), "auto_apply_related": "true"}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        by_title = {a["job_title"]: a for a in r.data}
        print("\nstrong ->", {k: (v["match_percentage"], v["status"]) for k, v in by_title.items()})
        self.assertEqual(by_title["Backend Dev"]["match_percentage"], 100.0)
        self.assertEqual(by_title["Backend Dev"]["status"], "applied")
        self.assertEqual(by_title["QA Automation"]["status"], "auto")   # related job -> auto-applied
        self.assertEqual(by_title["QA Automation"]["match_percentage"], 100.0)
        self.assertNotIn("Frontend Dev", by_title)           # unrelated, below threshold
        self.assertNotIn("ML Engineer", by_title)

        self.login("weakone")
        weak_cv = "Diploma holder, 1 year experience. Knows Python and some Excel."
        r = self.client.post(f"/api/jobs/{backend}/apply/", {"resume": make_docx(weak_cv)}, format="multipart")
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
    try:
        import pytesseract

        from .matching import _require_ocr

        _require_ocr()
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class UnreadableResumeTest(APITestCase):
    def setUp(self):
        rec = User.objects.create_user("rec", password="pass12345", role="recruiter", company_name="Acme")
        self.job = self.make_job(rec)
        User.objects.create_user("cand", password="pass12345")
        r = self.client.post("/api/auth/login/", {"username": "cand", "password": "pass12345"})
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def make_job(self, rec):
        from .models import Job

        return Job.objects.create(
            recruiter=rec, title="Web Dev", company="Acme", description="d",
            required_skills=["html", "css", "javascript", "php", "sql"],
            min_experience_years=1, required_education="bachelor",
        )

    def apply(self, upload):
        return self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume": upload}, format="multipart")

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
        r = self.apply(make_png(lines))
        self.assertEqual(r.status_code, 201, r.content)
        app = r.data[0]
        print("\nimage resume ->", app["match_percentage"], app["matched_skills"], app["missing_skills"])
        self.assertGreaterEqual(app["match_percentage"], 90)


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
        base = {"description": "d", "min_experience_years": 0, "required_education": "none"}
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
            r = self.client.post(f"/api/jobs/{self.j1}/apply/",
                                 {"resume": make_docx("I know Python and Django. " * 3)}, format="multipart")
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
        from .models import Job
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
        ok = self.client.post("/api/resume/", {"resume": make_docx("I know Python and Django. BCA student. " * 2)},
                              format="multipart")
        self.assertEqual(ok.status_code, 201, ok.content)
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
        base = {"title": "Backend", "description": "d", "location": "Pokhara", "min_experience_years": 0,
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
            self.client.post("/api/resume/", {"resume": self.cv()}, format="multipart")
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
            self.post_job(title=f"Job {i}")
        self.login("cand")
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            j = self.client.get("/api/jobs/").data[0]["id"]
            self.client.post(f"/api/jobs/{j}/apply/", {"resume": self.cv(), "auto_apply_related": "true"}, format="multipart")
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
        from .matching import extract_skills, normalize_skill
        from .recommendations import resume_health
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
        base = {"title": "Dev", "description": "Build things", "location": "Pokhara", "required_skills": ["python"],
                "min_experience_years": 0, "required_education": "bachelor"}
        return self.client.post("/api/recruiter/jobs/", {**base, **kw}, format="json")

    def test_default_deadline_fresher_and_past_date_rejected(self):
        import datetime
        from .models import nepal_today
        r = self.post()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(r.data["min_experience_years"], 0)                       # fresher
        self.assertEqual(r.data["expires_at"], str(nepal_today() + datetime.timedelta(days=30)))
        self.assertEqual(r.data["days_left"], 30)
        past = self.post(expires_at=str(nepal_today() - datetime.timedelta(days=1)))
        self.assertEqual(past.status_code, 400)

    def test_expired_jobs_disappear_for_candidates(self):
        import datetime
        from .models import Job, nepal_today
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
        self.client.post("/api/resume/", {"resume": make_docx("I know Python. BCA 2021-2025. " * 5)}, format="multipart")
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
        from .models import User as U
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
        from .models import Job
        self.rec = User.objects.create_user("recruiter1", email="r@x.com", password="pass12345", role=User.RECRUITER, company_name="Acme")
        self.rec2 = User.objects.create_user("recruiter2", email="r2@x.com", password="pass12345", role=User.RECRUITER, company_name="Other")
        self.cand = User.objects.create_user("candidate1", email="c@x.com", password="pass12345")
        User.objects.create_user("stranger1", email="s@x.com", password="pass12345")
        self.admin = User.objects.create_user("admin1", email="a@x.com", password="pass12345", role=User.ADMIN)
        self.job = Job.objects.create(recruiter=self.rec, title="Dev", company="Acme", description="d", location="Pokhara",
                                      required_skills=["python"])
        self.login("candidate1")
        self.client.post(f"/api/jobs/{self.job.id}/apply/", {"resume": make_docx("Python developer. BCA 2022. " * 5)}, format="multipart")
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
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"title": "x", "description": "d", "required_skills": ["python"]},
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
