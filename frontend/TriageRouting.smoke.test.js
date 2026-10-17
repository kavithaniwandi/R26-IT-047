/**
 * Smoke test - triageRouting.js
 * Run from frontend/: node TriageRouting.smoke.test.js
 */

import fs from "node:fs";
import path from "node:path";
import {
  chooseRoutedMO,
  findRecommendedMO,
  isSpecialtyUnmatched,
  routeMO,
  ROUTED_BY_NLP,
  ROUTED_BY_SUGGESTED_SPECIALTY,
  specialtyUnmatchedWarningText,
} from "./src/utils/triageRouting.js";

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

const fixturePath = path.resolve(
  "..",
  "backend",
  "tests",
  "fixtures",
  "triage_sample_cases.json"
);
const cases = JSON.parse(fs.readFileSync(fixturePath, "utf8"));
const original15 = [
  "critical_respiratory_distress",
  "crush_injury",
  "stroke",
  "pregnancy_bleeding",
  "paediatric_dehydration",
  "infected_wound",
  "fracture",
  "leptospirosis_fever",
  "minor_cut",
  "medication_need",
  "safety_severe_headache_neuro_red_flag",
  "safety_headache_hypoxia_tachycardia",
  "safety_insulin_confused_drowsy",
  "safety_gibberish",
  "case8_negated_chest_sob_mild_headache",
];
const severity = {
  critical_respiratory_distress: "CRITICAL",
  crush_injury: "CRITICAL",
  stroke: "CRITICAL",
  pregnancy_bleeding: "HIGH",
  paediatric_dehydration: "HIGH",
  infected_wound: "MEDIUM",
  fracture: "MEDIUM",
  leptospirosis_fever: "MEDIUM",
  minor_cut: "MEDIUM",
  medication_need: "LOW",
  safety_severe_headache_neuro_red_flag: "HIGH",
  safety_headache_hypoxia_tachycardia: "HIGH",
  safety_insulin_confused_drowsy: "HIGH",
  safety_gibberish: "MEDIUM",
  case8_negated_chest_sob_mild_headache: "LOW",
};
const currentNlpSpecialty = {
  critical_respiratory_distress: "Respiratory",
  crush_injury: "Trauma & Surgery",
  stroke: "Neurological",
  pregnancy_bleeding: "Obstetric & Gynecologic",
  paediatric_dehydration: "Pediatric",
  infected_wound: "Trauma & Surgery",
  fracture: "Orthopedic",
  leptospirosis_fever: "Infection & Systemic",
  minor_cut: "Trauma & Surgery",
  medication_need: "Neurological",
  safety_severe_headache_neuro_red_flag: "Neurological",
  safety_headache_hypoxia_tachycardia: "Neurological",
  safety_insulin_confused_drowsy: "Endocrine & Metabolic",
  safety_gibberish: "General Practice",
  case8_negated_chest_sob_mild_headache: "Cardiovascular",
};
const specialties = [
  "Emergency Medicine",
  "General Practice",
  "Pediatric",
  "Obstetric & Gynecologic",
  "Cardiovascular",
  "Respiratory",
  "Neurological",
  "Orthopedic",
  "Trauma & Surgery",
  "Infection & Systemic",
  "Endocrine & Metabolic",
  "Gastrointestinal",
  "Geriatric",
];
const mos = specialties.map((specialty, index) => ({
  id: `MO-${index + 1}`,
  name: `Dr ${specialty}`,
  role: "Senior MO",
  specialty,
  skills: [],
  supervisor: "yes",
  queueDepth: 0,
}));

console.log("\n-- 1. Flag-off routing snapshot --");
for (const caseId of original15) {
  const testCase = cases.find((item) => item.id === caseId);
  const direct = routeMO(mos, severity[caseId], currentNlpSpecialty[caseId]);
  const routed = chooseRoutedMO(
    mos,
    severity[caseId],
    currentNlpSpecialty[caseId],
    {
      primary: testCase.expected_specialty_primary,
      secondary: testCase.acceptable_secondary || [],
    },
    false
  );
  assert(`${caseId} flag-off equals routeMO`, routed.mo?.id === direct?.id);
  assert(`${caseId} flag-off audit label`, routed.auditLabel === ROUTED_BY_NLP);
}

console.log("\n-- 2. Flag-on routing snapshot --");
for (const caseId of original15) {
  const testCase = cases.find((item) => item.id === caseId);
  const routed = chooseRoutedMO(
    mos,
    severity[caseId],
    currentNlpSpecialty[caseId],
    {
      primary: testCase.expected_specialty_primary,
      secondary: testCase.acceptable_secondary || [],
    },
    true
  );
  assert(
    `${caseId} routes to expected suggested primary`,
    routed.mo?.specialty === testCase.expected_specialty_primary,
    `Got ${routed.mo?.specialty}`
  );
  assert(`${caseId} flag-on audit label`, routed.auditLabel === ROUTED_BY_SUGGESTED_SPECIALTY);
}

console.log("\n-- 3. Fallbacks and load --");
const noEmergency = mos.filter((mo) => mo.specialty !== "Emergency Medicine");
const criticalFallback = chooseRoutedMO(
  noEmergency,
  "CRITICAL",
  "Respiratory",
  { primary: "Emergency Medicine", secondary: ["Respiratory"] },
  true
);
assert("CRITICAL without Emergency Medicine falls to secondary", criticalFallback.mo?.specialty === "Respiratory");

const loadedRoster = [
  { id: "ENDO-5", name: "Busy Endo", role: "Senior MO", specialty: "Endocrine & Metabolic", skills: [], supervisor: "yes", queueDepth: 5 },
  { id: "ENDO-0", name: "Free Endo", role: "Senior MO", specialty: "Endocrine & Metabolic", skills: [], supervisor: "yes", queueDepth: 0 },
];
const loadRouted = chooseRoutedMO(
  loadedRoster,
  "LOW",
  "Neurological",
  { primary: "Endocrine & Metabolic", secondary: [] },
  true
);
assert("Lower queueDepth wins within suggested specialty", loadRouted.mo?.id === "ENDO-0");

const recommendation = findRecommendedMO(loadedRoster, { primary: "Endocrine & Metabolic" }, "LOW");
assert("Recommended MO uses same lower queueDepth preference", recommendation?.id === "ENDO-0");

console.log("\n-- 4. Specialty unmatched warning --");
const gpOnlyRoster = [
  {
    id: "GP-1",
    name: "Dr General",
    role: "Senior MO",
    specialty: "General Practice",
    skills: [],
    supervisor: "yes",
    queueDepth: 0,
  },
];
const emergencySuggestion = { primary: "Emergency Medicine", secondary: [] };
const gpAssigned = gpOnlyRoster[0];
const warningText = specialtyUnmatchedWarningText(
  gpOnlyRoster,
  emergencySuggestion,
  gpAssigned
);
const savedEntry = {
  routing_source: "nlp",
  specialty_unmatched: isSpecialtyUnmatched(gpOnlyRoster, emergencySuggestion),
};
assert("Emergency suggestion is unmatched on GP-only roster", savedEntry.specialty_unmatched === true);
assert(
  "Unmatched warning text is shown",
  warningText ===
    "No Emergency Medicine MO on the current roster. Assigned to General Practice by fallback. Consider escalating or adding an MO.",
  `Got ${warningText}`
);

const emergencyRoster = [
  ...gpOnlyRoster,
  {
    id: "EM-1",
    name: "Dr Emergency",
    role: "Senior MO",
    specialty: "Emergency Medicine",
    skills: [],
    supervisor: "yes",
    queueDepth: 0,
  },
];
assert("Matching Emergency Medicine MO suppresses unmatched flag", isSpecialtyUnmatched(emergencyRoster, emergencySuggestion) === false);
assert("Matching Emergency Medicine MO suppresses warning", specialtyUnmatchedWarningText(emergencyRoster, emergencySuggestion, gpAssigned) === "");

console.log("\n------------------------------------------------------------");
console.log(`  ${passed} passed | ${failed} failed | ${passed + failed} total`);
console.log("------------------------------------------------------------\n");

if (failed > 0) {
  process.exit(1);
}
