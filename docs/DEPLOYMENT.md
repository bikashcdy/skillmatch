# Putting JobMitra online (free)

> I could not deploy this for you (it needs your own accounts), so these steps follow each
> platform's normal workflow but are **not tested live**. Menu names change; if a screen differs,
> use the platform's own Django docs. Do a trial run before your viva/demo day.

Two parts go online separately:

| Part | Where (free) | Why |
|---|---|---|
| Backend (Django + MySQL) | **PythonAnywhere** | Django and MySQL are built in, no credit card |
| Frontend (React) | **Netlify** or **Vercel** | Static hosting, a link in seconds |

**Limits:** (1) Photo/scanned resumes need Tesseract OCR, which free hosts do not install, so online
only text PDF / DOCX / TXT resumes work. (2) Free plans sleep or restrict outgoing internet, so
Gmail emails may not send on PythonAnywhere free; the app keeps working without them.

## Before you start (on your PC)
1. Paste the block from `docs/EMAIL_AND_DEPLOY_SNIPPET.py` at the bottom of `backend/config/settings.py`.
2. Run `py manage.py migrate` locally once (this update adds new tables/fields).
3. Put the project on GitHub (private repo is fine). Do **not** commit `venv`, `node_modules`, `media`.

## Part 1: Backend on PythonAnywhere
1. Create a free account at pythonanywhere.com (your username becomes `yourname.pythonanywhere.com`).
2. **Databases** tab: set a MySQL password, create a database named `jobmitra`. Note the host
   (`yourname.mysql.pythonanywhere-services.com`) and the full name (`yourname$jobmitra`).
3. **Consoles** tab, open a Bash console:
   ```bash
   git clone https://github.com/<you>/<repo>.git jobmitra
   cd jobmitra/backend
   mkvirtualenv jobmitra --python=python3.10     # pick a Python version listed on your Web tab
   pip install -r requirements.txt
   ```
4. **Web** tab: *Add a new web app* -> *Manual configuration* -> choose the same Python version.
   - Source code: `/home/yourname/jobmitra/backend`
   - Virtualenv: `/home/yourname/.virtualenvs/jobmitra`
   - (Do NOT map `/media/`: resumes are private and served through the API.)
5. Open the **WSGI configuration file** (link on the Web tab). Replace its contents with:
   ```python
   import os, sys
   sys.path.insert(0, "/home/yourname/jobmitra/backend")
   os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
   os.environ["DJANGO_DEBUG"] = "0"
   os.environ["DJANGO_SECRET_KEY"] = "put-a-long-random-string-here"
   os.environ["DJANGO_ALLOWED_HOSTS"] = "yourname.pythonanywhere.com"
   os.environ["FRONTEND_URL"] = "https://YOUR-SITE.netlify.app"      # fill in after Part 2
   os.environ["DB_NAME"] = "yourname$jobmitra"
   os.environ["DB_USER"] = "yourname"
   os.environ["DB_PASSWORD"] = "your-mysql-password"
   os.environ["DB_HOST"] = "yourname.mysql.pythonanywhere-services.com"
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
6. In the Bash console (with the same environment variables exported, or run `python manage.py ...`
   after `export` of the same values), create the tables and demo data:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser        # then set its role to "admin" in /admin
   ```
7. Click **Reload** on the Web tab. Visit `https://yourname.pythonanywhere.com/` — you should see
   "JobMitra API is running".

## Part 2: Frontend on Netlify
1. Netlify -> *Add new site* -> *Import from GitHub* -> pick the repo.
2. Base directory `frontend`, build command `npm run build`, publish directory `frontend/dist`.
3. *Site settings -> Environment variables*: `VITE_API_URL` = `https://yourname.pythonanywhere.com/api`
4. Deploy. Copy the site URL, put it in `FRONTEND_URL` in the WSGI file (Part 1, step 5) and Reload.
   (`frontend/public/_redirects` is already included so page refreshes work. For Vercel,
   `frontend/vercel.json` does the same.)

## Checklist before you share the link
- [ ] `DEBUG` is off and `SECRET_KEY` is your own random string
- [ ] Demo passwords changed or demo users deleted (do **not** run `seed_demo` online with the default passwords)
- [ ] Register a new recruiter and candidate on the live site and apply once end to end
- [ ] Say in your report that photo resumes work locally with OCR but not on the free host
