/**
 * Smoke test - CampSetup.jsx
 * Run from frontend/: node CampSetup.smoke.test.js
 * No test framework needed - plain Node.js assertions.
 */

let passed = 0;
let failed = 0;

function assert(label, condition, detail = "") {
  if (condition) {
    console.log(`  PASS  ${label}`);
    passed++;
  } else {
    console.error(`  FAIL  ${label}${detail ? `\n        ${detail}` : ""}`);
    failed++;
  }
}

const SPECIALTIES = [
  "Emergency Medicine", "Cardiovascular", "Respiratory", "Neurological",
  "Gastrointestinal", "Trauma & Surgery", "Orthopedic", "Rheumatology",
  "Pediatric", "Geriatric", "Infection & Systemic",
  "Renal & Urinary", "Mental & Behavioral", "Obstetric & Gynecologic",
  "Endocrine & Metabolic", "Allergy & Immunology", "General Practice",
];

const SECONDARY_SKILLS = [
  "Cardiovascular", "Respiratory", "Neurological", "Gastrointestinal",
  "Trauma & Surgery", "Orthopedic", "Rheumatology", "Pediatric", "Geriatric",
  "Infection & Systemic", "Renal & Urinary",
  "Mental & Behavioral", "Obstetric & Gynecologic", "Endocrine & Metabolic",
  "Allergy & Immunology", "Emergency Medicine",
];

const ROLES = ["Medical Administrator", "Senior MO", "Medical Officer", "Resident", "Intern"];

const SHIFT_HOURS = Array.from({ length: 24 }, (_, hour) => {
  const value = String(hour).padStart(2, "0");
  const period = hour < 12 ? "AM" : "PM";
  const displayHour = hour % 12 || 12;
  return { value, label: `${displayHour} ${period}` };
});

const SHIFT_MINUTES = ["00", "15", "30", "45"];

const SHIFT_PRESETS = [
  { label: "Noon", value: "12:00" },
  { label: "3:00 PM", value: "15:00" },
  { label: "6:00 PM", value: "18:00" },
  { label: "9:00 PM", value: "21:00" },
];

const BLANK_MO = {
  name: "",
  staffId: "",
  role: "",
  specialty: "",
  skills: [],
  supervisor: "",
  shift: "",
};

const NLP_REQUIRED_SPECIALTIES = [
  "Orthopedic", "Rheumatology", "Pediatric", "Geriatric",
];

const NLP_REQUIRED_SKILLS = [
  "Orthopedic", "Rheumatology", "Pediatric", "Geriatric",
];

function validateMOForm(form) {
  const name = form.name.trim();
  const staffId = form.staffId.trim();
  const shift = form.shift.trim();
  if (!name) return "Full name is required.";
  if (name.length < 3 || !/[a-zA-Z]/.test(name)) return "Enter a valid name with at least 3 letters.";
  if (staffId && !/^\d{3,20}$/.test(staffId)) return "Staff ID must be 3-20 digits only.";
  if (!form.role) return "Select the officer role.";
  if (!form.specialty) return "Select a primary specialty.";
  if (form.skills.length === 0) return "Select at least one secondary skill.";
  if (!form.supervisor) return "Choose supervisor availability.";
  if (shift && !/^([01]?\d|2[0-3])[:.]([0-5]\d)$/.test(shift)) {
    return "Shift end time must use 24-hour time, for example 15:00.";
  }
  return "";
}

const campSubtitle = (camp) =>
  [camp.district, camp.ds_division].filter(Boolean).join(" \u00b7 ");

const initials = (name) =>
  name.trim().split(" ").map((word) => word[0]).slice(0, 2).join("").toUpperCase() || "?";

const makeSessionId = (camp, timestamp = Date.now()) => `${camp.id}-${timestamp}`;

function updateShiftPart(currentShift, part, value) {
  const [shiftHour = "", shiftMinute = ""] = currentShift ? currentShift.split(":") : ["", ""];
  const nextHour = part === "hour" ? value : shiftHour;
  const nextMinute = part === "minute" ? value : shiftMinute;

  if (!nextHour && !nextMinute) {
    return "";
  }

  return `${nextHour || "00"}:${nextMinute || "00"}`;
}

console.log("\n-- 1. SPECIALTIES array --");
assert("No duplicate entries", new Set(SPECIALTIES).size === SPECIALTIES.length);
assert("Count is 17", SPECIALTIES.length === 17, `Got ${SPECIALTIES.length}`);
assert("No empty strings", SPECIALTIES.every((specialty) => specialty.trim().length > 0));
NLP_REQUIRED_SPECIALTIES.forEach((term) => {
  assert(`NLP term present as specialty: ${term}`, SPECIALTIES.includes(term));
});
[
  "Emergency Medicine", "Cardiovascular", "Respiratory", "Neurological",
  "General Practice", "Trauma & Surgery", "Mental & Behavioral",
].forEach((specialty) => {
  assert(`Core specialty present: ${specialty}`, SPECIALTIES.includes(specialty));
});

console.log("\n-- 2. SECONDARY_SKILLS array --");
assert("No duplicate entries", new Set(SECONDARY_SKILLS).size === SECONDARY_SKILLS.length);
assert("Count is 16", SECONDARY_SKILLS.length === 16, `Got ${SECONDARY_SKILLS.length}`);
assert("No empty strings", SECONDARY_SKILLS.every((skill) => skill.trim().length > 0));
NLP_REQUIRED_SKILLS.forEach((term) => {
  assert(`NLP term present as skill: ${term}`, SECONDARY_SKILLS.includes(term));
});
assert("Emergency Medicine present as skill", SECONDARY_SKILLS.includes("Emergency Medicine"));
assert("General Practice not in secondary skills", !SECONDARY_SKILLS.includes("General Practice"));

console.log("\n-- 3. ROLES array --");
assert("No duplicates", new Set(ROLES).size === ROLES.length);
assert("Count is 5", ROLES.length === 5, `Got ${ROLES.length}`);
["Medical Administrator", "Senior MO", "Medical Officer", "Resident", "Intern"].forEach((role) => {
  assert(`Role present: ${role}`, ROLES.includes(role));
});

console.log("\n-- 4. Shift end-time controls --");
assert("24 hour options exist", SHIFT_HOURS.length === 24, `Got ${SHIFT_HOURS.length}`);
assert("Midnight label is friendly", SHIFT_HOURS[0].value === "00" && SHIFT_HOURS[0].label === "12 AM");
assert("Noon label is friendly", SHIFT_HOURS[12].value === "12" && SHIFT_HOURS[12].label === "12 PM");
assert("23:00 label is friendly", SHIFT_HOURS[23].value === "23" && SHIFT_HOURS[23].label === "11 PM");
assert("Minute options are quarter-hour increments", SHIFT_MINUTES.join(",") === "00,15,30,45");
assert("Preset values remain HH:MM", SHIFT_PRESETS.every((preset) => /^\d{2}:\d{2}$/.test(preset.value)));
assert("Hour selection writes HH:MM", updateShiftPart("", "hour", "15") === "15:00");
assert("Minute selection writes HH:MM", updateShiftPart("15:00", "minute", "30") === "15:30");
assert("Empty hour keeps selected minute with 00 fallback", updateShiftPart("15:30", "hour", "") === "00:30");

console.log("\n-- 5. BLANK_MO shape --");
["name", "staffId", "role", "specialty", "skills", "supervisor", "shift"].forEach((key) => {
  assert(`BLANK_MO has field: ${key}`, key in BLANK_MO);
});
assert("skills is empty array", Array.isArray(BLANK_MO.skills) && BLANK_MO.skills.length === 0);
assert(
  "all string fields are empty string",
  ["name", "staffId", "role", "specialty", "supervisor", "shift"].every((key) => BLANK_MO[key] === "")
);

console.log("\n-- 6. validateMOForm valid inputs --");
const validMO = {
  name: "Dr. Nimal Perera",
  staffId: "12345",
  role: "Medical Officer",
  specialty: "Emergency Medicine",
  skills: [{ name: "Cardiovascular", confidence: 2 }],
  supervisor: "yes",
  shift: "15:00",
};
assert("Valid MO returns no error", validateMOForm(validMO) === "");
NLP_REQUIRED_SPECIALTIES.forEach((specialty) => {
  assert(`Specialty passes validation: ${specialty}`, validateMOForm({ ...validMO, specialty }) === "");
});
NLP_REQUIRED_SKILLS.forEach((skill) => {
  assert(`Skill passes validation: ${skill}`, validateMOForm({ ...validMO, skills: [{ name: skill, confidence: 2 }] }) === "");
});
SHIFT_PRESETS.forEach((preset) => {
  assert(`Preset passes validation: ${preset.label}`, validateMOForm({ ...validMO, shift: preset.value }) === "");
});

console.log("\n-- 7. validateMOForm invalid inputs --");
[
  [{ ...validMO, name: "" }, "Full name is required."],
  [{ ...validMO, name: "AB" }, "Enter a valid name with at least 3 letters."],
  [{ ...validMO, name: "123" }, "Enter a valid name with at least 3 letters."],
  [{ ...validMO, staffId: "12" }, "Staff ID must be 3-20 digits only."],
  [{ ...validMO, staffId: "AB123" }, "Staff ID must be 3-20 digits only."],
  [{ ...validMO, role: "" }, "Select the officer role."],
  [{ ...validMO, specialty: "" }, "Select a primary specialty."],
  [{ ...validMO, skills: [] }, "Select at least one secondary skill."],
  [{ ...validMO, supervisor: "" }, "Choose supervisor availability."],
  [{ ...validMO, shift: "25:00" }, "Shift end time must use 24-hour time, for example 15:00."],
  [{ ...validMO, shift: "abc" }, "Shift end time must use 24-hour time, for example 15:00."],
].forEach(([form, expectedError]) => {
  const error = validateMOForm(form);
  assert(`Rejects: ${expectedError}`, error === expectedError, `Got: ${error}`);
});
assert("Blank staffId is allowed", validateMOForm({ ...validMO, staffId: "" }) === "");
assert("Blank shift is allowed", validateMOForm({ ...validMO, shift: "" }) === "");
assert("Shift 15.30 with dot is valid", validateMOForm({ ...validMO, shift: "15.30" }) === "");

console.log("\n-- 8. Helpers --");
assert("campSubtitle both fields", campSubtitle({ district: "Colombo", ds_division: "Kaduwela" }) === "Colombo \u00b7 Kaduwela");
assert("campSubtitle missing ds_division", campSubtitle({ district: "Colombo", ds_division: null }) === "Colombo");
assert("campSubtitle missing district", campSubtitle({ district: null, ds_division: "Kaduwela" }) === "Kaduwela");
assert("campSubtitle both missing", campSubtitle({ district: null, ds_division: null }) === "");
assert("initials two-word name", initials("Nimal Perera") === "NP");
assert("initials three-word name takes first two", initials("Dr Nimal Perera") === "DN");
assert("initials single word", initials("Nimal") === "N");
assert("initials empty string", initials("") === "?");

console.log("\n-- 9. Session object shape --");
const mockCamp = {
  id: 42,
  name: "Nawagamuwa Primary School",
  district: "Colombo",
  ds_division: "Kaduwela",
  gn_division: "Wekewatta",
  estimated_capacity: 200,
};
const mockMO = {
  id: "12345",
  name: "Dr. Nimal Perera",
  role: "Medical Officer",
  specialty: "Emergency Medicine",
  skills: [{ name: "Cardiovascular", confidence: 2 }],
  supervisor: "yes",
  shift: "15:00",
  queueDepth: 0,
  patients: [],
};
const sessionObj = {
  session_id: makeSessionId(mockCamp, 1234567890),
  startedAt: new Date().toISOString(),
  camp: {
    id: mockCamp.id,
    name: mockCamp.name,
    district: mockCamp.district,
    ds_division: mockCamp.ds_division,
    gn_division: mockCamp.gn_division,
    estimated_capacity: mockCamp.estimated_capacity,
  },
  mos: [mockMO],
};
assert("session_id starts with camp id", sessionObj.session_id.startsWith("42-"));
assert("session_id has timestamp suffix", /^\d+-\d+$/.test(sessionObj.session_id));
assert("camp.id is integer", Number.isInteger(sessionObj.camp.id));
assert("camp has all required fields", ["id", "name", "district", "ds_division", "gn_division", "estimated_capacity"].every((key) => key in sessionObj.camp));
assert("mos is non-empty array", Array.isArray(sessionObj.mos) && sessionObj.mos.length > 0);
assert("MO has queueDepth: 0", sessionObj.mos[0].queueDepth === 0);
assert("MO has patients: []", Array.isArray(sessionObj.mos[0].patients));
assert("startedAt is ISO string", !Number.isNaN(Date.parse(sessionObj.startedAt)));

console.log("\n-- 10. Activation state keying --");
const mockCamps = [
  { id: 1, name: "Camp A", district: "Colombo", ds_division: "Kaduwela" },
  { id: 2, name: "Camp B", district: "Kandy", ds_division: "Pasbage Korale" },
];
const savedMap = { 1: true };
const merged = Object.fromEntries(mockCamps.map((camp) => [camp.id, savedMap[camp.id] ?? false]));
assert("Activation keyed by integer id", 1 in merged && 2 in merged);
assert("Previously active camp preserved", merged[1] === true);
assert("New camp defaults to false", merged[2] === false);
assert("No legacy camp-code key leaking in", !("KDW-001" in merged));

console.log("\n------------------------------------------------------------");
console.log(`  ${passed} passed | ${failed} failed | ${passed + failed} total`);
console.log("------------------------------------------------------------\n");

if (failed > 0) {
  process.exit(1);
}
