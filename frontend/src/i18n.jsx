import { createContext, useContext } from "react";

// English only. Every visible text lives here so it is easy to find and change.
const en = {
  findJobs: "Find jobs", myApps: "My applications", careerPlan: "Career plan", myJobs: "My jobs", admin: "Admin", profile: "Profile",
  logout: "Log out", login: "Log in", signup: "Sign up", howItWorks: "How matching works",
  heroTitle: "Find a job that matches your skills",
  heroSub: "Search by what you do best and where you want to work. Your resume match shows on every job.",
  searchPh: "Job title, skill or company", cityPh: "City (type any city)", allSkills: "All skills", searchBtn: "Search Jobs",
  trending: "Trending:", viewAll: "View All",
  jobsAvail: "Jobs available", companies: "Companies hiring", jobsFound: "{n} jobs found", jobFound: "1 job found",
  searching: "Searching…", clear: "Clear filters", applyNow: "Apply now", yourMatch: "your match",
  jobType: "Job type", allTypes: "All types", full_time: "Full-time", part_time: "Part-time", internship: "Internship", contract: "Contract",
  anySalary: "Any salary",
  noJobs: "No result found", noJobsSub: "No jobs match your search. Check the spelling of the city or skill, or clear the filters.",
  negotiable: "Salary negotiable", perMonth: "/ month",
  applyTo: "Apply", chooseResume: "Choose your resume", resumeHint: "PDF, DOCX, TXT or photo (leave empty to reuse your last resume)",
  alsoApply: "Also apply to related jobs I match (50%+)", submit: "Submit application", scanning: "Scanning resume…",
  sent: "Application sent 🎉", viewMyApps: "View my applications", done: "Done",
  welcomeBack: "Welcome back", username: "Username", password: "Password", signingIn: "Signing in…", noAccount: "No account?",
  createOne: "Create one", createAccount: "Create your account", lookingJob: "I'm looking for a job", hiring: "I'm hiring",
  email: "Email", company: "Company name", creating: "Creating…", haveAccount: "Already registered?", joinTitle: "Join JobMitra",
  myAppsTitle: "My applications", noApps: "No applications yet", noAppsSub: "Find a job you like and upload your resume.",
  skills: "Skills", experience: "Experience", education: "Education", fromRecruiter: "Message from the recruiter",
  planTitle: "Your career plan", planSub: "Based on your latest resume and {n} open jobs", uploadNewer: "Upload a newer resume",
  uploadScan: "Upload & scan resume", scanFirst: "Scan your resume to get your personal plan",
  skillsToLearn: "Skills to learn, in order of impact", closest: "Jobs closest to you", other: "Other things to improve",
  howLearn: "How to actually learn", resumeCheck: "Resume check", resumeScore: "Resume score", fixThese: "Fix these to improve your resume",
  avgNow: "average match now", avgAfter: "after learning {n} skills", boost: "avg match boost", now: "now", afterPlan: "after plan",
  postJob: "Post a job", editJob: "Edit job", publish: "Publish job", saveChanges: "Save changes", saving: "Saving…",
  rankedCands: "Ranked candidates", edit: "Edit", close: "Close", reopen: "Reopen", del: "Delete",
  jobTitle: "Job title", description: "Description", location: "Location", reqSkills: "Required skills (press Enter after each)",
  minExp: "Min experience (years)", salaryMin: "Salary from (NPR/month)", salaryMax: "Salary to (NPR/month)", anyEdu: "Any",
  selectBest: "Select highest match", select: "Select", reject: "Reject", restore: "Restore", details: "Details", message: "Message",
  hideDetails: "Hide details", resume: "Resume", back: "Back to my jobs", highestFirst: "Highest match first",
  msgTitle: "Message to candidate", msgHint: "Short note the candidate will see (and get by email).", sendMsg: "Send message",
  tplInterview: "We would like to interview you on ___ at ___.", tplDocs: "Please bring your original documents.",
  tplThanks: "Thank you for applying. We will contact you soon.",
  statusApplied: "Applied", statusAuto: "Auto-applied", statusSelected: "Selected", statusRejected: "Rejected",
  fresher: "Fresher (no experience needed)", fresherShort: "Fresher", months: "{n} months", years: "{n} years", year1: "1 year", expYears: "{n}+ years",
  posted: "Posted", expires: "Apply before", noDeadline: "No deadline", daysLeft: "{n} days left", dayLeft: "1 day left", lastDay: "Last day to apply",
  expired: "Expired", today: "today", yesterday: "yesterday", daysAgo: "{n} days ago",
  jobDetails: "Job details", viewDetails: "View details", requirements: "Requirements", qualification: "Qualification", experienceReq: "Experience",
  requiredSkills: "Required skills", yourResume: "How your resume matches", uploadForMatch: "Upload a resume with Apply to see how well you match.",
  backToJobs: "Back to jobs", alreadyApplied: "You already applied to this job", expiryDate: "Expiry date (last day to apply)",
  edu_none: "Any qualification", edu_diploma: "Diploma / +2", edu_bachelor: "Bachelor's degree", edu_master: "Master's degree", edu_phd: "PhD",
  jobGone: "This job is no longer available", jobGoneSub: "It may have expired or been closed by the recruiter.",
  matchedSkills: "Skills you have", missingSkills: "Skills to add", expiredBadge: "Expired", extendHint: "Edit the job and set a new expiry date to show it again.",
};

const Ctx = createContext({ t: (k) => en[k] || k });
export const useT = () => useContext(Ctx);
const t = (key, vars = {}) => (en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
export function LangProvider({ children }) {
  return <Ctx.Provider value={{ t, lang: "en" }}>{children}</Ctx.Provider>;
}
