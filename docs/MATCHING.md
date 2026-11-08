# JobMitra matching engine (v5)

Pure Python, no Django: `backend/matching/engine/`. Django only feeds it data (`backend/matching/services.py`).

## Score
`score = 100 × (0.40·Skills + 0.20·Text + 0.20·Experience + 0.10·Education + 0.10·Preferences)`

* A part that cannot be computed (candidate set no preferences) is dropped and the other weights are rescaled to sum to 1.
* **Knock-out (pseudocode rule):** if any *must-have* skill is completely missing (value 0), the score is capped at 60. A related skill (same group, value 0.5) is *not* missing.
* Skills: must-have importance 2, nice-to-have 1. exact = 1, related = 0.5, missing = 0. Skill gap % = completely missing skills ÷ all job skills.
* Experience = min(years ÷ required, 1). Education = min(level ÷ required, 1). Preferences = share of satisfied preferences (city, job type).

## Skill extraction
Lower-case tokens (c++, c#, .net, node.js, ci/cd kept whole) → n-grams up to 3, longest first, via hash map → overlap removal → implied skills (Django ⇒ Python). Normaliser: synonym table → plural → Levenshtein similarity ≥ 0.85 (words of 5+ letters).

## TF-IDF: what was wrong and the fix
The textbook IDF `ln(N / (1 + DF))` is **negative** when a word appears in every document of a small corpus (N=3, DF=3 → ln(3/4) < 0), so common words *subtracted* from the score. Also raw term frequency lets a candidate repeat a keyword 20 times to inflate the score.

Fix (same as scikit-learn's defaults):
* **Smoothed IDF** `ln((1+N)/(1+DF)) + 1` — always ≥ 1, never negative, never divides by zero.
* **Sublinear TF** `1 + ln(count)` — the 20th repetition adds almost nothing.
* L2 normalisation, then cosine similarity. Stop-words removed. The corpus is all active job texts; the compared pair is added if missing.
`tests/test_engine.py` compares the result with scikit-learn (`pip install -r requirements-dev.txt`).

## Grid search (weight tuning)
All 10,626 combinations of five weights in steps of 0.05 (sum = 1); best average NDCG@5 on the *tuning* ratings; ties → closest to default; reported on the unseen *test* ratings.
Data fixes: ratings are grouped as ranked lists per resume **and** per job (a list needs ≥ 2 items), a tuning/test split exists, recruiter decisions can be imported (selected = 3, rejected = 0), and warnings appear for small datasets (< 30 pairs), missing test sets and all-equal ratings.
Caveat: imported decisions are biased because recruiters saw the engine's own ranking — add manual ratings.

## Other parts
Top-K recommender (min-heap, O(J log K)) with a score cache; learning path by topological sort of skill prerequisites (cycle-safe); what-if simulation; metrics Precision@k, NDCG@k, Spearman, Cohen's kappa, P/R/F1.

## OCR
`resumes/ocr.py`: fix rotation, grayscale, enlarge to ~2000 px, auto-contrast, sharpen; Tesseract with page-segmentation modes 3/6/11 (best wins). PDFs are read page by page (text pages as is; picture pages rendered at 300 dpi and OCR'd). Needs the Tesseract program installed.

## Apps
accounts · profiles · resumes · jobs · applications · matching (+engine) · recommendations · analytics. `core` keeps the shared migrations, admin, commands and the URL list. Every model is registered with app label `core`, so tables and migrations did not change.
