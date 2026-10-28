"""Career recommendations: which skills to learn to raise the candidate's match %."""

from types import SimpleNamespace

from .matching import EDUCATION_LEVELS, SKILLS, score_match

NEPAL_CITIES = [
    "Kathmandu", "Lalitpur", "Bhaktapur", "Pokhara", "Biratnagar", "Birgunj",
    "Bharatpur", "Butwal", "Dharan", "Hetauda", "Janakpur", "Nepalgunj",
    "Itahari", "Dhangadhi", "Bhairahawa", "Birtamod", "Damak", "Ghorahi",
    "Tulsipur", "Kirtipur", "Remote",
]

# skill -> (what it is / why it matters, weeks to a job-ready basic level, [(label, url)])
RESOURCES = {
    "python": ("General-purpose language used for web, data and automation.", 6, [
        ("Official Python Tutorial", "https://docs.python.org/3/tutorial/"),
        ("freeCodeCamp: Python course (YouTube)", "https://www.youtube.com/@freecodecamp"),
        ("Kaggle Learn: Python", "https://www.kaggle.com/learn/python")]),
    "django": ("Python web framework for building secure backends and APIs quickly.", 6, [
        ("Official Django tutorial", "https://docs.djangoproject.com/en/stable/intro/tutorial01/"),
        ("Django REST Framework docs", "https://www.django-rest-framework.org/tutorial/quickstart/"),
        ("MDN Django tutorial", "https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django")]),
    "flask": ("Lightweight Python web framework, good for small APIs.", 3, [
        ("Flask tutorial", "https://flask.palletsprojects.com/en/stable/tutorial/")]),
    "javascript": ("The language of the browser; required for any interactive website.", 6, [
        ("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide"),
        ("javascript.info", "https://javascript.info/"),
        ("freeCodeCamp curriculum", "https://www.freecodecamp.org/learn/")]),
    "typescript": ("JavaScript with types; common in larger React/Node teams.", 3, [
        ("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html")]),
    "react": ("Most popular library for building user interfaces.", 6, [
        ("react.dev Learn", "https://react.dev/learn"),
        ("Scrimba: Learn React (free)", "https://scrimba.com/learn/learnreact")]),
    "node.js": ("JavaScript on the server for APIs and tooling.", 4, [
        ("Node.js Learn", "https://nodejs.org/en/learn"),
        ("The Odin Project: NodeJS", "https://www.theodinproject.com/paths/full-stack-javascript/courses/nodejs")]),
    "html": ("The structure of every web page.", 2, [
        ("MDN: Learn HTML", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Structuring_content"),
        ("web.dev Learn HTML", "https://web.dev/learn/html")]),
    "css": ("Styling and responsive layout for the web.", 3, [
        ("web.dev Learn CSS", "https://web.dev/learn/css"),
        ("MDN: CSS first steps", "https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Styling_basics")]),
    "sql": ("Query and design relational databases (MySQL, PostgreSQL).", 3, [
        ("SQLBolt interactive lessons", "https://sqlbolt.com/"),
        ("Mode SQL tutorial", "https://mode.com/sql-tutorial/"),
        ("Kaggle Learn: Intro to SQL", "https://www.kaggle.com/learn/intro-to-sql")]),
    "mongodb": ("Popular NoSQL document database.", 3, [
        ("MongoDB University (free)", "https://learn.mongodb.com/")]),
    "php": ("Server-side language behind WordPress and Laravel; common in Nepal.", 6, [
        ("PHP manual: Getting started", "https://www.php.net/manual/en/getting-started.php"),
        ("Laravel documentation", "https://laravel.com/docs")]),
    "java": ("Typed, enterprise-grade language for backends and Android.", 8, [
        ("dev.java Learn", "https://dev.java/learn/")]),
    "c++": ("Systems language; strong for algorithms and performance.", 8, [
        ("learncpp.com", "https://www.learncpp.com/")]),
    "flutter": ("Build Android and iOS apps from one Dart codebase.", 6, [
        ("Flutter documentation & codelabs", "https://docs.flutter.dev/get-started/codelab"),
        ("Dart language tour", "https://dart.dev/language")]),
    "git": ("Version control; every team expects it.", 1, [
        ("Pro Git book (free)", "https://git-scm.com/book/en/v2"),
        ("GitHub Skills", "https://skills.github.com/")]),
    "docker": ("Package apps into containers so they run the same everywhere.", 2, [
        ("Docker Get Started", "https://docs.docker.com/get-started/")]),
    "aws": ("Leading cloud platform; hosting, storage, databases.", 6, [
        ("AWS Skill Builder (free tier)", "https://skillbuilder.aws/"),
        ("AWS Cloud Practitioner Essentials", "https://aws.amazon.com/training/")]),
    "rest api": ("Designing and consuming HTTP APIs, the glue between frontend and backend.", 2, [
        ("restfulapi.net", "https://restfulapi.net/"),
        ("Django REST Framework quickstart", "https://www.django-rest-framework.org/tutorial/quickstart/")]),
    "machine learning": ("Training models that learn from data.", 12, [
        ("Google ML Crash Course", "https://developers.google.com/machine-learning/crash-course"),
        ("Kaggle Learn: Intro to ML", "https://www.kaggle.com/learn/intro-to-machine-learning"),
        ("scikit-learn user guide", "https://scikit-learn.org/stable/user_guide.html")]),
    "data analysis": ("Cleaning, exploring and presenting data (Excel, pandas, Power BI).", 6, [
        ("Kaggle Learn: Pandas", "https://www.kaggle.com/learn/pandas"),
        ("Kaggle Learn: Data Visualization", "https://www.kaggle.com/learn/data-visualization"),
        ("Microsoft Learn: Power BI", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi")]),
    "testing": ("Finding bugs systematically: manual, automated and unit tests.", 4, [
        ("Test Automation University (free)", "https://testautomationu.com/"),
        ("Selenium documentation", "https://www.selenium.dev/documentation/"),
        ("pytest getting started", "https://docs.pytest.org/en/stable/getting-started.html")]),
    "communication": ("Clear writing, teamwork and presenting your work.", 4, [
        ("Toastmasters", "https://www.toastmasters.org/"),
        ("Write a project README or blog post for every project you build", "https://www.freecodecamp.org/news/")]),
}

GENERAL_IDEAS = [
    "Build 2-3 small projects that use the skills you are learning and publish them on GitHub.",
    "Follow a structured path on roadmap.sh (https://roadmap.sh/) so you know what comes next.",
    "Contribute to a small open-source project or build something for a local business or your campus.",
    "Look for internships, freelance gigs or volunteer work in Kathmandu, Lalitpur or Pokhara tech companies to gain experience.",
]


def _resume_view(resume, extra_skills=()):
    return SimpleNamespace(
        extracted_skills=sorted(set(resume.extracted_skills) | set(extra_skills)),
        experience_years=resume.experience_years,
        education_level=resume.education_level,
    )


def _resources_for(skill):
    info = RESOURCES.get(skill)
    if info:
        why, weeks, links = info
        return why, weeks, [{"label": l, "url": u} for l, u in links]
    q = skill.replace(" ", "+")
    return (
        f"Required by employers on SkillMatch for {skill}.",
        4,
        [
            {"label": f"Search free {skill} courses on YouTube", "url": f"https://www.youtube.com/results?search_query=learn+{q}+full+course"},
            {"label": "roadmap.sh learning paths", "url": "https://roadmap.sh/"},
        ],
    )


def build_recommendations(resume, jobs):
    """Return skill gaps (ranked by impact), best-fit jobs and experience/education tips."""
    have = set(resume.extracted_skills)
    baseline = {j.id: score_match(resume, j) for j in jobs}

    gaps = {}
    for j in jobs:
        for s in baseline[j.id]["missing_skills"]:
            gaps.setdefault(s, []).append(j)

    skill_gaps = []
    for skill, needing in gaps.items():
        view = _resume_view(resume, [skill])
        gains, unlocks = [], []
        for j in needing:
            new = score_match(view, j)["match_percentage"]
            old = baseline[j.id]["match_percentage"]
            gains.append(new - old)
            if old < 75 <= new:
                unlocks.append(j.title)
        why, weeks, links = _resources_for(skill)
        avg = sum(gains) / len(gains)
        skill_gaps.append({
            "skill": skill,
            "why": why,
            "jobs_needing": len(needing),
            "avg_gain": round(avg, 1),
            "unlocks": unlocks[:3],
            "weeks": weeks,
            "priority_score": round(avg * len(needing), 1),
            "resources": links,
            "job_titles": [j.title for j in needing][:4],
        })
    skill_gaps.sort(key=lambda g: (-g["priority_score"], g["skill"]))
    skill_gaps = skill_gaps[:8]
    for i, g in enumerate(skill_gaps):
        g["rank"] = i + 1

    # What if the top 3 skills were learned?
    top3 = [g["skill"] for g in skill_gaps[:3]]
    future = _resume_view(resume, top3)
    best = []
    for j in jobs:
        now = baseline[j.id]
        after = score_match(future, j)["match_percentage"]
        best.append({
            "id": j.id, "title": j.title, "company": j.company, "location": j.location,
            "match": now["match_percentage"], "match_after": after,
            "matched_skills": now["matched_skills"], "missing_skills": now["missing_skills"],
        })
    best.sort(key=lambda b: -b["match"])

    tips = []
    max_exp = max((j.min_experience_years for j in jobs), default=0)
    if resume.experience_years < max_exp:
        tips.append({
            "area": "Experience",
            "text": (f"Your resume shows {resume.experience_years:g} year(s); some jobs ask for up to {max_exp:g}. "
                     "If you have worked, interned or freelanced, write it as '2 years' or '6 months' so the scanner can read it. "
                     "Otherwise build real projects and look for internships."),
        })
    top_edu = max((EDUCATION_LEVELS.get((j.required_education or "none").lower(), 0) for j in jobs), default=0)
    mine = EDUCATION_LEVELS.get(resume.education_level or "none", 0)
    if mine < top_edu:
        names = {v: k for k, v in EDUCATION_LEVELS.items()}
        tips.append({
            "area": "Education",
            "text": (f"Some jobs prefer a {names[top_edu]} degree and your resume shows '{resume.education_level}'. "
                     "Make sure your degree (BCA, BSc CSIT, +2, diploma) is written clearly. Certificates help your profile, "
                     "but the match score only counts the degree level."),
        })
    if len(have) < 5:
        tips.append({"area": "Resume", "text": "Only a few skills were detected. List your tools and technologies in a Skills section using common names (Python, React, SQL, Git)."})

    avg_now = round(sum(b["match"] for b in best[:5]) / max(len(best[:5]), 1), 1)
    avg_after = round(sum(b["match_after"] for b in best[:5]) / max(len(best[:5]), 1), 1)
    return {
        "skills_have": sorted(have),
        "skill_gaps": skill_gaps,
        "best_jobs": best[:6],
        "tips": tips,
        "ideas": GENERAL_IDEAS,
        "focus": top3,
        "avg_now": avg_now,
        "avg_after": avg_after,
        "weeks_total": sum(g["weeks"] for g in skill_gaps[:3]),
    }
