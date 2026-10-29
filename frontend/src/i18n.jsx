import { createContext, useContext, useState } from "react";

const en = {
  findJobs: "Find jobs", myApps: "My applications", careerPlan: "Career plan", myJobs: "My jobs", admin: "Admin",
  logout: "Log out", login: "Log in", signup: "Sign up", howItWorks: "How matching works",
  heroTitle: "Find a job that matches your skills",
  heroSub: "Search by what you do best and where you want to work. Your resume match shows on every job.",
  searchPh: "Job title, skill or company", cityPh: "City or remote", allSkills: "All skills", searchBtn: "Search Jobs",
  trending: "Trending:", popularCities: "Popular cities:", moreCities: "More cities", fewer: "Fewer", viewAll: "View All",
  jobsAvail: "Jobs available", companies: "Companies hiring", jobsFound: "{n} jobs found", jobFound: "1 job found",
  searching: "Searching…", clear: "Clear filters", applyNow: "Apply now", yourMatch: "your match",
  jobType: "Job type", allTypes: "All types", full_time: "Full-time", part_time: "Part-time", internship: "Internship",
  contract: "Contract", anySalary: "Any salary", savedOnly: "Saved jobs", alertsOn: "Job alerts: on", alertsOff: "Job alerts: off",
  noJobs: "No jobs match your search", noJobsSub: "Try a different skill or location, or clear the filters.",
  negotiable: "Salary negotiable", perMonth: "/ month", save: "Save job", unsave: "Remove from saved", saved: "Saved",
  applyTo: "Apply", chooseResume: "Choose your resume", resumeHint: "PDF, DOCX, TXT or photo (leave empty to reuse your last resume)",
  alsoApply: "Also apply to related jobs I match (50%+)", submit: "Submit application", scanning: "Scanning resume…",
  sent: "Application sent 🎉", viewMyApps: "View my applications", done: "Done",
  welcomeBack: "Welcome back", username: "Username", password: "Password", signingIn: "Signing in…", noAccount: "No account?",
  createOne: "Create one", createAccount: "Create your account", lookingJob: "I'm looking for a job", hiring: "I'm hiring",
  email: "Email", passwordMin: "Password (min 8 characters)", company: "Company name", creating: "Creating…",
  haveAccount: "Already registered?", joinTitle: "Join JobMitra",
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
};

const ne = {
  findJobs: "जागिर खोज्नुहोस्", myApps: "मेरा आवेदन", careerPlan: "क्यारियर योजना", myJobs: "मेरा जागिर", admin: "एडमिन",
  logout: "बाहिर निस्कनुहोस्", login: "लगइन", signup: "साइन अप", howItWorks: "मिलान कसरी काम गर्छ",
  heroTitle: "आफ्नो सीपसँग मिल्ने जागिर खोज्नुहोस्",
  heroSub: "तपाईं के राम्रो गर्नुहुन्छ र कहाँ काम गर्न चाहनुहुन्छ भनेर खोज्नुहोस्। हरेक जागिरमा तपाईंको रिजुमे मिलान देखिन्छ।",
  searchPh: "जागिरको नाम, सीप वा कम्पनी", cityPh: "सहर वा रिमोट", allSkills: "सबै सीप", searchBtn: "जागिर खोज्नुहोस्",
  trending: "लोकप्रिय:", popularCities: "प्रमुख सहरहरू:", moreCities: "थप सहर", fewer: "कम", viewAll: "सबै हेर्नुहोस्",
  jobsAvail: "उपलब्ध जागिर", companies: "भर्ना गर्ने कम्पनी", jobsFound: "{n} जागिर भेटियो", jobFound: "१ जागिर भेटियो",
  searching: "खोज्दै…", clear: "फिल्टर हटाउनुहोस्", applyNow: "आवेदन दिनुहोस्", yourMatch: "तपाईंको मिलान",
  jobType: "जागिरको प्रकार", allTypes: "सबै प्रकार", full_time: "पूर्णकालीन", part_time: "आंशिक समय", internship: "इन्टर्नसिप",
  contract: "करार", anySalary: "कुनै पनि तलब", savedOnly: "सुरक्षित जागिर", alertsOn: "जागिर अलर्ट: खुला", alertsOff: "जागिर अलर्ट: बन्द",
  noJobs: "तपाईंको खोजीसँग मिल्ने जागिर भेटिएन", noJobsSub: "अर्को सीप वा सहर प्रयास गर्नुहोस्, वा फिल्टर हटाउनुहोस्।",
  negotiable: "तलब छलफलमा", perMonth: "/ महिना", save: "जागिर सुरक्षित गर्नुहोस्", unsave: "सुरक्षितबाट हटाउनुहोस्", saved: "सुरक्षित",
  applyTo: "आवेदन", chooseResume: "आफ्नो रिजुमे छान्नुहोस्", resumeHint: "PDF, DOCX, TXT वा फोटो (खाली राखे अघिल्लो रिजुमे प्रयोग हुन्छ)",
  alsoApply: "मैले मिल्ने (५०%+) अन्य जागिरमा पनि आवेदन दिनुहोस्", submit: "आवेदन पठाउनुहोस्", scanning: "रिजुमे स्क्यान हुँदैछ…",
  sent: "आवेदन पठाइयो 🎉", viewMyApps: "मेरा आवेदन हेर्नुहोस्", done: "सकियो",
  welcomeBack: "फेरि स्वागत छ", username: "प्रयोगकर्ता नाम", password: "पासवर्ड", signingIn: "प्रवेश गर्दै…", noAccount: "खाता छैन?",
  createOne: "खाता बनाउनुहोस्", createAccount: "आफ्नो खाता बनाउनुहोस्", lookingJob: "म जागिर खोज्दैछु", hiring: "म भर्ना गर्दैछु",
  email: "इमेल", passwordMin: "पासवर्ड (कम्तीमा ८ अक्षर)", company: "कम्पनीको नाम", creating: "बनाउँदै…",
  haveAccount: "पहिले नै खाता छ?", joinTitle: "जबमित्रमा सामेल हुनुहोस्",
  myAppsTitle: "मेरा आवेदन", noApps: "अहिलेसम्म कुनै आवेदन छैन", noAppsSub: "मनपर्ने जागिर खोज्नुहोस् र रिजुमे अपलोड गर्नुहोस्।",
  skills: "सीप", experience: "अनुभव", education: "शिक्षा", fromRecruiter: "भर्ना गर्नेको सन्देश",
  planTitle: "तपाईंको क्यारियर योजना", planSub: "तपाईंको पछिल्लो रिजुमे र {n} खुला जागिरमा आधारित", uploadNewer: "नयाँ रिजुमे अपलोड गर्नुहोस्",
  uploadScan: "रिजुमे अपलोड र स्क्यान", scanFirst: "आफ्नो योजना पाउन रिजुमे स्क्यान गर्नुहोस्",
  skillsToLearn: "सिक्नुपर्ने सीप (प्रभावको क्रममा)", closest: "तपाईंसँग सबैभन्दा नजिकका जागिर", other: "अरू सुधार्नुपर्ने कुरा",
  howLearn: "वास्तवमै कसरी सिक्ने", resumeCheck: "रिजुमे जाँच", resumeScore: "रिजुमे स्कोर", fixThese: "रिजुमे राम्रो बनाउन यी सुधार्नुहोस्",
  avgNow: "अहिलेको औसत मिलान", avgAfter: "{n} सीप सिकेपछि", boost: "औसत मिलान वृद्धि", now: "अहिले", afterPlan: "योजनापछि",
  postJob: "जागिर राख्नुहोस्", editJob: "जागिर सम्पादन", publish: "जागिर प्रकाशित गर्नुहोस्", saveChanges: "परिवर्तन सुरक्षित गर्नुहोस्", saving: "सुरक्षित गर्दै…",
  rankedCands: "क्रमबद्ध उम्मेदवार", edit: "सम्पादन", close: "बन्द", reopen: "फेरि खोल्नुहोस्", del: "मेटाउनुहोस्",
  jobTitle: "जागिरको नाम", description: "विवरण", location: "स्थान", reqSkills: "आवश्यक सीप (प्रत्येकपछि Enter थिच्नुहोस्)",
  minExp: "न्यूनतम अनुभव (वर्ष)", salaryMin: "तलब देखि (रु/महिना)", salaryMax: "तलब सम्म (रु/महिना)", anyEdu: "कुनै पनि",
  selectBest: "उच्चतम मिलान छान्नुहोस्", select: "छान्नुहोस्", reject: "अस्वीकार", restore: "पुनःस्थापना", details: "विवरण", message: "सन्देश",
  hideDetails: "विवरण लुकाउनुहोस्", resume: "रिजुमे", back: "मेरा जागिरमा फर्कनुहोस्", highestFirst: "उच्च मिलान पहिला",
  msgTitle: "उम्मेदवारलाई सन्देश", msgHint: "उम्मेदवारले देख्ने (र इमेलमा पाउने) छोटो सन्देश।", sendMsg: "सन्देश पठाउनुहोस्",
  tplInterview: "हामी तपाईंको अन्तर्वार्ता ___ मा ___ बजे लिन चाहन्छौं।", tplDocs: "कृपया आफ्ना मूल कागजात ल्याउनुहोस्।",
  tplThanks: "आवेदन दिनुभएकोमा धन्यवाद। हामी चाँडै सम्पर्क गर्नेछौं।",
  statusApplied: "आवेदन दिइएको", statusAuto: "स्वतः आवेदन", statusSelected: "छानिएको", statusRejected: "अस्वीकृत",
};

const DICT = { en, ne };
const Ctx = createContext({ lang: "en", setLang: () => {}, t: (k) => en[k] || k });
export const useT = () => useContext(Ctx);

export function LangProvider({ children }) {
  const [lang, setLangState] = useState(() => {
    try { return localStorage.getItem("lang") || "en"; } catch { return "en"; }
  });
  const setLang = (l) => { setLangState(l); try { localStorage.setItem("lang", l); } catch {} };
  const t = (key, vars = {}) =>
    (DICT[lang][key] ?? en[key] ?? key).replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ""));
  return <Ctx.Provider value={{ lang, setLang, t }}>{children}</Ctx.Provider>;
}
