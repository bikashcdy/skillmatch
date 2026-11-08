import { Link } from "react-router-dom";

const Row = ({ k, w, children }) => (
  <tr><td><b>{k}</b></td><td>{w}</td><td className="muted">{children}</td></tr>
);

export default function HowItWorks() {
  return (
    <div className="stack doc">
      <h1>How JobMitra matches resumes to jobs</h1>
      <p className="muted">A plain explanation of the scoring, so candidates and recruiters know what the percentage means, and what it does not.</p>

      <section className="card stack">
        <h2>1. Reading the resume</h2>
        <ul>
          <li><b>Text:</b> PDF, DOCX and TXT are read directly. Photos and scanned PDFs are read with OCR (text recognition); the picture is cleaned first (straightened, enlarged, sharpened).</li>
          <li><b>You confirm it.</b> After reading, you see the skills, years, education, projects and certifications that were found. Fix anything wrong, then confirm. Only a confirmed resume is used for matching. If the file cannot be read, you can type your details instead.</li>
          <li><b>Skills:</b> found with a dictionary of aliases (<code>reactjs</code> = React). Longer names win (“machine learning” before “learning”), small typos are fixed with edit distance, and implied skills are added (Django implies Python).</li>
        </ul>
      </section>

      <section className="card stack">
        <h2>2. The match percentage</h2>
        <div className="tablewrap"><table>
          <thead><tr><th>Part</th><th>Weight</th><th>How it is scored</th></tr></thead>
          <tbody>
            <Row k="Skills" w="40%">must-have skills count double, nice-to-have count once. Exact skill = 1, related skill (React for Vue) = 0.5, missing = 0</Row>
            <Row k="Text fit" w="20%">TF-IDF + cosine similarity between your resume text and the job text. Rare words count more than common ones, and repeating a word does not help</Row>
            <Row k="Experience" w="20%">your years ÷ the job's minimum years (maximum 100%)</Row>
            <Row k="Education" w="10%">your level ÷ the level the job asks for (maximum 100%)</Row>
            <Row k="Preferences" w="10%">your preferred city and job type. If you set none, this part is left out and the others share its weight</Row>
          </tbody>
        </table></div>
        <p><b>Must-have rule.</b> If a must-have skill is <i>completely</i> missing (no exact and no related skill), the score is capped at 60%. A related skill is not “missing”.</p>
        <p className="formula">match = 100 × (0.40 × Skills + 0.20 × Text + 0.20 × Experience + 0.10 × Education + 0.10 × Preferences)<br />
          Example: skills 0.75, text 0.60, experience 0.50, education 1, preferences 1 → <b>75.0%</b></p>
        <p>The weights above are the defaults. An admin can tune them with a grid search on rated examples.</p>
      </section>

      <section className="card stack">
        <h2>3. What happens with the score</h2>
        <ul>
          <li>You see <i>why</i> you got a score: every part, the matched / related / missing skills and the skill gap.</li>
          <li>The Career plan shows the best order to learn skills (prerequisites first), and a “What if I learn…?” tool shows how your score would change.</li>
          <li>Applying to one job can also apply you to up to 5 related jobs where you score 50% or more and no must-have skill is missing (optional).</li>
          <li>Recruiters see applicants ranked by match with the same breakdown. A recruiter gets one email when a candidate matches 70% or more.</li>
        </ul>
      </section>

      <section className="card stack">
        <h2>4. Limits you should know</h2>
        <ul>
          <li><b>Keywords, not meaning.</b> The scanner finds words. It cannot tell how well someone used a skill, and a resume stuffed with keywords can score high.</li>
          <li><b>Spelling matters.</b> A skill missing from the dictionary can only match the exact same word. Common spellings and small typos are handled.</li>
          <li><b>Photo resumes</b> depend on picture quality. Blurry photos may lose words.</li>
          <li><b>Experience</b> is only read from phrases like "2 years". Dates alone are not counted.</li>
          <li><b>Not a verdict.</b> The percentage helps sort a long list. Recruiters should always open the resume and decide themselves, and candidates should not be discouraged by a low score. Use the Career plan to see what to improve.</li>
        </ul>
      </section>

      <p className="muted">Ready? <Link to="/" style={{ color: "var(--accent)", fontWeight: 600 }}>Go to the app</Link></p>
    </div>
  );
}
