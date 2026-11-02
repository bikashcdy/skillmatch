// Same rules as backend/core/validators.py. The server always re-checks them.
export const usernameErrors = (v = "") => {
  const e = [];
  if (!v.trim()) return ["Username is required."];
  if (/\s/.test(v)) e.push("Username cannot contain spaces.");
  const t = v.trim();
  if (t.length < 4 || t.length > 20) e.push("Username must be 4-20 characters.");
  if (/[^A-Za-z0-9_\s]/.test(v)) e.push("Only letters, numbers and underscore (_) are allowed.");
  if (!/^[A-Za-z]/.test(t)) e.push("Username must start with a letter.");
  return e;
};

export const emailErrors = (v = "") => {
  const t = v.trim();
  if (!t) return ["Email is required."];
  if (t.length > 254 || !/^[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$/.test(t) || t.includes(".."))
    return ["Enter a valid email address, for example name@gmail.com."];
  return [];
};

// Each rule is a line in the live checklist.
export const passwordRules = (v = "", username = "", email = "") => {
  const local = email.split("@")[0];
  return [
    { label: "8 to 64 characters", ok: v.length >= 8 && v.length <= 64 },
    { label: "One uppercase letter (A-Z)", ok: /[A-Z]/.test(v) },
    { label: "One lowercase letter (a-z)", ok: /[a-z]/.test(v) },
    { label: "One number (0-9)", ok: /\d/.test(v) },
    { label: "One special character (@ # $ ! …)", ok: /[^A-Za-z0-9]/.test(v) },
    { label: "No spaces", ok: v.length > 0 && !/\s/.test(v) },
    { label: "Does not contain your username or email name",
      ok: v.length > 0 && !(username.length >= 3 && v.toLowerCase().includes(username.toLowerCase())) &&
          !(local.length >= 4 && v.toLowerCase().includes(local.toLowerCase())) },
  ];
};
export const passwordOk = (v, u, e) => passwordRules(v, u, e).every((r) => r.ok);
export const companyErrors = (v = "") => (v.trim().length >= 2 && v.trim().length <= 100 ? [] : ["Company name must be 2-100 characters."]);

export const jobTitleErrors = (v = "") => {
  const t = v.trim().replace(/\s+/g, " ");
  if (!t) return ["Job title is required."];
  const e = [];
  if (t.length < 3 || t.length > 80) e.push("Job title must be 3-80 characters.");
  if (/\d/.test(t)) e.push("Job title cannot contain numbers.");
  if (/[^A-Za-z\s&.,/+#()-]/.test(t.replace(/\d/g, ""))) e.push("Job title can only use letters and & . , / + # ( ) -");
  if ((t.match(/[A-Za-z]/g) || []).length < 3) e.push("Job title must contain real words, for example Python Developer.");
  return e;
};

export const jobDescriptionErrors = (v = "") => {
  const t = v.trim();
  if (!t) return ["Description is required."];
  const e = [];
  if (t.length < 30) e.push("Description must be at least 30 characters.");
  if (t.length > 3000) e.push("Description must be at most 3000 characters.");
  const words = t.match(/[A-Za-z]{2,}/g) || [];
  if (words.length < 5) e.push("Description needs at least 5 real words, not just numbers or symbols.");
  else if (new Set(words.map((w) => w.toLowerCase())).size < 4) e.push("Description looks repeated. Describe the role, duties and requirements.");
  return e;
};

export const jobLocationErrors = (v = "") => {
  const t = v.trim().replace(/\s+/g, " ");
  if (!t) return ["Location is required."];
  const e = [];
  if (t.length < 2 || t.length > 60) e.push("Location must be 2-60 characters.");
  if (/[^A-Za-z\s.,-]/.test(t)) e.push("Location can only contain letters (no numbers or symbols).");
  return e;
};
