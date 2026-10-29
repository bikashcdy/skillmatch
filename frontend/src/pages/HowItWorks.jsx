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
          <li><b>Text:</b> PDF, DOCX and TXT are read directly. Photos and scanned PDFs are read with OCR (text recognition).</li>
          <li><b>Skills:</b> the text is checked against a dictionary of about 50 skills with aliases (<code>reactjs</code> and <code>react.js</code> both mean React). Matching uses whole words, so "java" is not found inside "javascript".</li>
          <li><b>Implied skills:</b> some skills imply others. Django implies Python, React implies JavaScript, Laravel implies PHP.</li>
          <li><b>Experience:</b> the largest "N years" phrase, for example "3 years" or "2+ yrs".</li>
          <li><b>Education:</b> the highest level found: diploma/+2, bachelor (BCA, BSc), master, PhD.</li>
        </ul>
      </section>

      <section className="card stack">
        <h2>2. The match percentage</h2>
        <div className="tablewrap"><table>
          <thead><tr><th>Part</th><th>Weight</th><th>How it is scored</th></tr></thead>
          <tbody>
            <Row k="Skills" w="60%">matched required skills ÷ all required skills</Row>
            <Row k="Experience" w="25%">your years ÷ the job's minimum years (maximum 100%)</Row>
            <Row k="Education" w="15%">your level ÷ the level the job asks for (maximum 100%)</Row>
          </tbody>
        </table></div>
        <p><b>Example.</b> A job needs Python, Django, SQL, Git (4 skills), 2 years, a bachelor degree. Your resume has Python, Django, Git, 1 year and a bachelor degree:</p>
        <p className="formula">skills 3/4 = 75% · experience 1/2 = 50% · education 100%<br />
          match = 0.60 × 75 + 0.25 × 50 + 0.15 × 100 = <b>72.5%</b></p>
      </section>

      <section className="card stack">
        <h2>3. What happens with the score</h2>
        <ul>
          <li>Applying to one job can also apply you to up to 5 related jobs where you score 50% or more (optional).</li>
          <li>Recruiters see applicants ranked by match, with matched and missing skills and the full resume.</li>
          <li>A recruiter gets an email when someone matches 80% or more. A candidate gets an email when they are selected or rejected, when the recruiter sends a message, and (if alerts are on) when a new job matches 70% or more.</li>
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
