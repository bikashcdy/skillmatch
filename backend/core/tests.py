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
    def login(self, username, password="pass12345"):
        r = self.client.post("/api/auth/login/", {"username": username, "password": password})
        self.assertEqual(r.status_code, 200, r.content)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")

    def register(self, **kw):
        self.client.credentials()
        r = self.client.post("/api/auth/register/", {"password": "pass12345", **kw})
        self.assertEqual(r.status_code, 201, r.content)

    def post_job(self, **kw):
        r = self.client.post("/api/recruiter/jobs/", kw, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        return r.data["id"]

    def test_full_flow(self):
        # --- recruiter posts 3 jobs
        self.register(username="rec", email="r@x.com", role="recruiter", company_name="Acme")
        self.login("rec")
        backend = self.post_job(title="Backend Dev", description="d", required_skills=["Python", "Django", "SQL"],
                                min_experience_years=1, required_education="bachelor")
        frontend = self.post_job(title="Frontend Dev", description="d", required_skills=["ReactJS", "JavaScript", "CSS"],
                                 min_experience_years=1, required_education="bachelor")
        ml = self.post_job(title="ML Engineer", description="d", required_skills=["machine learning", "python", "pandas", "docker", "aws"],
                           min_experience_years=3, required_education="master")

        qa = self.post_job(title="QA Automation", description="d", required_skills=["python", "testing", "git"],
                           min_experience_years=1, required_education="bachelor")

        # --- two candidates
        self.register(username="strong", email="s@x.com", role="candidate")
        self.register(username="weak", email="w@x.com", role="candidate")

        self.login("strong")
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

        self.login("weak")
        weak_cv = "Diploma holder, 1 year experience. Knows Python and some Excel."
        r = self.client.post(f"/api/jobs/{backend}/apply/", {"resume": make_docx(weak_cv)}, format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        print("weak ->", r.data[0]["match_percentage"], r.data[0]["missing_skills"])
        self.assertLess(r.data[0]["match_percentage"], 60)

        # --- recruiter sees ranking and selects best
        self.login("rec")
        r = self.client.get(f"/api/recruiter/jobs/{backend}/candidates/")
        self.assertEqual([a["candidate_name"] for a in r.data], ["strong", "weak"])
        r = self.client.post(f"/api/recruiter/jobs/{backend}/select-best/")
        self.assertEqual(r.data["candidate_name"], "strong")
        self.assertEqual(Application.objects.get(job_id=backend, candidate__username="strong").status, "selected")

        # --- permissions
        self.assertEqual(self.client.get("/api/admin/stats/").status_code, 403)
        self.login("weak")
        self.assertEqual(self.client.post("/api/recruiter/jobs/", {"title": "x"}, format="json").status_code, 403)

        # --- admin
        User.objects.create_user("boss", password="pass12345", role="admin")
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
        self.assertIn("Remote", meta["locations"])

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
        cities = [c["name"] for c in self.client.get("/api/jobs/meta/").data["cities"]]
        self.assertIn("Pokhara", cities)
        self.assertIn("Butwal", cities)
