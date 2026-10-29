# How JobMitra matching works (for your report / viva)

## Pipeline
1. **Extract text**: PDF (pypdf), DOCX (python-docx), TXT; photos and scanned PDFs through OCR (Tesseract).
2. **Extract skills**: lower-case the text; for each of ~50 canonical skills check its aliases with
   whole-word regular expressions (`(?<![\w+])term(?![\w+])`) so "java" does not match "javascript".
   Implied skills are added (Django -> Python, React -> JavaScript, Laravel -> PHP).
3. **Extract experience**: largest number before "year(s)/yr(s)". **Education**: highest level keyword found.
4. **Normalise recruiter input**: aliases, plurals and small typos map to the canonical skill
   ("ReactJS", "Javascripts", "javascipt" -> javascript) using exact lookup then `difflib` (cutoff 0.86).
5. **Score**: `match = 0.60 * skills + 0.25 * experience + 0.15 * education` (each part 0-100%).
   - skills = matched required skills / required skills
   - experience = min(candidate years / required years, 1)
   - education = min(candidate level / required level, 1)  (none 0, diploma 1, bachelor 2, master 3, PhD 4)
6. **Use**: rank applicants; auto-apply to related jobs at 50% or more (max 5); email recruiter at 80%+;
   alert candidates at 70%+ for new jobs.

## Career plan
For every skill a candidate is missing, the app re-scores each open job as if the skill were learned.
The **average gain**, the **number of jobs needing it** and the jobs that would **cross 75%** decide the
order. Learning links come from a curated list in `backend/core/recommendations.py`.

## Resume check (score out of 100)
Email 10, phone 10, skills section 15, education 10, experience 10, projects 15, dates 10,
GitHub/LinkedIn link 10, enough detail (150+ words) 10. Each failed check shows a fix.

## Why weights 60/25/15?
Skills are the best signal for entry-level roles and are the most reliable to extract, so they get the most
weight. Experience is next. Education is a threshold, not a quality signal, so it is lowest. The weights are
constants (`W_SKILLS`, `W_EXPERIENCE`, `W_EDUCATION` in `matching.py`) and can be tuned.

## Limitations (say these before the examiner does)
- Keyword matching can be gamed by keyword stuffing and cannot judge depth of skill.
- Skills outside the dictionary only match when spelled identically.
- OCR quality depends on the photo; experience is read only from "N years" style text.
- A percentage is a sorting aid, not a hiring decision: recruiters see the full resume and decide.
- Possible next step: TF-IDF / sentence embeddings (spaCy, sentence-transformers) for semantic matching.
