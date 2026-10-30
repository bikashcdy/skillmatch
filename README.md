# JobMitra

Resume-matching hiring platform. Recruiters post jobs, candidates apply with a resume, and the
system scans the resume, scores it against the job's requirements, ranks applicants, and
auto-applies candidates to related jobs.

**Stack:** Django 5 + Django REST Framework + JWT (backend), React 18 + Vite (frontend), SQLite (dev DB).

## Run it

Backend (terminal 1):

```bash
cd backend
python -m venv venv && source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo                             # demo users + 5 sample jobs
python manage.py runserver                             # http://localhost:8000
```

Frontend (terminal 2):

```bash
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```

Demo logins (created by `seed_demo`):

| Role      | Username    | Password     |
|-----------|-------------|--------------|
| Admin     | `admin`     | `admin12345` |
| Recruiter | `recruiter` | `demo12345`  |
| Candidate | `candidate` | `demo12345`  |

Run the automated end-to-end test: `python manage.py test core`

## How it works

### 1. Resume scanning (`backend/core/matching.py`)
1. **Text extraction**: `pypdf` for PDF, `python-docx` for DOCX, plain read for TXT.
2. **Skill extraction**: the text is lower-cased and checked against a skill dictionary where each
   canonical skill has aliases (`reactjs`, `react.js` -> `react`; `mysql`, `postgres` -> `sql`).
   Matching uses word boundaries so "java" does not match inside "javascript" and "c++" works.
3. **Experience**: finds phrases like "3 years" / "2+ yrs" and takes the largest.
4. **Education**: finds the highest level mentioned (diploma/+2 < bachelor/BCA < master < PhD).

### 2. Match percentage
```
match % = 60% x skill score + 25% x experience score + 15% x education score
skill score      = matched required skills / total required skills
experience score = min(candidate years / job minimum years, 1)
education score  = min(candidate level / required level, 1)
```
Recruiter-typed skills go through the same alias normalisation, so "ReactJS" in a job and "React.js"
in a resume still match. The weights are constants at the bottom of `matching.py`.

### 3. Apply + automatic related-job applications (`backend/core/services.py`)
When a candidate applies and ticks "also apply to related jobs", the same resume is scored against
every other open job. Jobs scoring >= 50% (best 5) get an application with status `auto`.
Tune `RELATED_THRESHOLD` and `MAX_AUTO_APPLY`.

### 4. Selecting the best candidate
Recruiters see applicants ranked by match % with a skills / experience / education breakdown and
matched vs missing skills. "Select highest match" marks the top application as `selected`.

### Roles and permissions
- **Candidate**: browse jobs, apply, see own applications and scores.
- **Recruiter**: post/edit own jobs, see ranked applicants for own jobs only, select best.
- **Admin**: platform stats, activate/deactivate users. Create with `createsuperuser` and set role
  to `admin` (the `seed_demo` admin already has it).

## API summary
`POST /api/auth/register|login/` · `GET /api/jobs/` · `POST /api/jobs/<id>/apply/` ·
`GET /api/my-applications/` · `GET|POST /api/recruiter/jobs/` ·
`GET /api/recruiter/jobs/<id>/candidates/` · `POST /api/recruiter/jobs/<id>/select-best/` ·
`GET /api/admin/stats|users/` · `GET /api/jobs/?q=&location=&skill=` · `GET /api/jobs/meta/` ·
`POST /api/recruiter/applications/<id>/status/` · `POST /api/resume/` · `GET /api/recommendations/`

## Update v2: what is new
- **Email notifications** (`core/notifications.py`): candidate when selected/rejected or messaged by a recruiter;
  recruiter when someone matches 80%+.
  With no setup, emails are **printed in the backend terminal**. For real emails paste
  `docs/EMAIL_AND_DEPLOY_SNIPPET.py` at the bottom of `backend/config/settings.py` and fill in `EMAIL_HOST_USER`
  and `EMAIL_HOST_PASSWORD` (Gmail app password).
- **Better scanner**: ~50 skills incl. Laravel, WordPress, Figma, digital marketing, accounting; implied skills;
  typo/plural matching for recruiter input; old resumes are re-scanned automatically.
- **Resume check**: score out of 100 with a fix list on the Career plan page.
- **Job type** (full-time/part-time/internship/contract), **salary range** and filters.
- **Recruiter messages** to candidates (shown in My applications and emailed).
- A **How matching works** page.
- `docs/DEPLOYMENT.md` (going online) and `docs/MATCHING.md` (explanation for your report).
- **Database change:** run `py manage.py migrate` once after copying the files.

## Update v3: job details, expiry, fresher
- Clicking a job opens a **details page**: description, requirements, qualification, experience, posted date
  ("2 days ago"), apply-before date with days left, salary, and how your resume matches.
- Jobs have an **expiry date** (default 30 days, set by the recruiter). Expired jobs disappear for candidates
  automatically (no scheduler needed) and stay in the recruiter's list marked "Expired"; edit the job to extend it.
- Recruiters can choose **Fresher** (no experience needed) as the experience level.
- **Database change:** run `py manage.py migrate` once.

## Update v4: accounts, privacy and control
- **Forgot password:** emailed single-use reset link (valid 3 days). Without Gmail settings the link is printed in the backend terminal.
- **Registration rules** (checked in the browser and again on the server, with live "already taken" checks):
  username 4-20 chars (letters, numbers, `_` `.`), valid email, password 8-64 chars with upper + lower case, number,
  symbol, no spaces, not containing the username/email. Rules live in `backend/core/validators.py` and `frontend/src/validate.js`.
- **Email verification is intentionally not included.**
- **Recruiters need admin approval** before posting; admins can also remove fake jobs. Existing recruiters stay approved.
- **Private resumes:** files are no longer reachable by a public `/media/` link; only the owner, a recruiter who received that application, or an admin can open them.
- Candidates can **withdraw an application, delete a resume, edit their profile** and change password.
- Recruiters get **one summary email** per upload for strong matches (not one per job).
- Removed: saved jobs, job alerts, Nepali language, and the city chips (location is a typed search; no match shows "No results found").
- **Database change:** run `py manage.py migrate` once.

## Career plan (recommendations)
Candidates open **Career plan** to upload/scan a resume and see: skills found, the skills to learn in
order of impact (average match boost across open jobs, jobs it unlocks, weeks to get started), free
learning links, the jobs closest to them (before -> after the plan) and tips on experience/education.
Logic is in `backend/core/recommendations.py` (edit `RESOURCES` to add skills or links).
Locations: jobs use Nepal city names (`NEPAL_CITIES` in the same file) with city quick-filters.

## Scanned resumes and photos (OCR)

PDFs that are really a photo or scan (for example a WhatsApp image saved as PDF) contain no
text, so they need OCR. Supported uploads: PDF, DOCX, TXT, PNG, JPG. Text-based PDF/DOCX/TXT
files work without any extra setup. For scans and photos:

1. Install the **Tesseract** program (Windows): https://github.com/UB-Mannheim/tesseract/wiki
   and keep the default folder `C:\Program Files\Tesseract-OCR\`
   (or set the environment variable `TESSERACT_CMD` to the full path of `tesseract.exe`).
2. With the venv active: `pip install -r requirements-ocr.txt`
3. Restart `py manage.py runserver`.

If OCR is not installed, uploading a scan shows a clear message instead of a 0% match.

## Known limitations / next steps
- Keyword matching can be gamed by keyword-stuffed resumes; semantic matching (TF-IDF or spaCy /
  sentence embeddings) would help.
- OCR accuracy depends on image quality; blurry or tiny photos may miss words.
- Before production: switch to PostgreSQL, set `DEBUG=False`, move `SECRET_KEY` to an env var,
  restrict CORS, add email notifications and file-size limits.
