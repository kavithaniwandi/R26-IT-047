/**
 * Smoke test - triageMappingDisplay.js
 * Run from frontend/: node TriageMappingDisplay.smoke.test.js
 */

import {
  complaintMappingNotice,
  visibleMatchedRules,
} from "./src/utils/triageMappingDisplay.js";

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

console.log("\n-- Complaint mapping banner logic --");

const warning = complaintMappingNotice(
  {
    mapped_terms: [],
    unmapped_terms: ["xqzv", "blorp"],
    coverage: 0,
    threshold: 0.6,
    floor_applied: true,
    floor_changed_result: true,
    reason_code: "NO_MAPPING",
  },
  { primary: "General Practice", fallback: true }
);
assert("Floor-changed mapping issue is warning", warning?.tone === "warning");
assert("Warning uses review copy", warning?.message === "No complaint recognised - please review.");

const info = complaintMappingNotice(
  {
    mapped_terms: ["vaginal bleeding"],
    unmapped_terms: ["pregnant"],
    coverage: 0.4,
    threshold: 0.6,
    floor_applied: true,
    floor_changed_result: false,
    reason_code: "LOW_COVERAGE",
  },
  { primary: "Obstetric & Gynecologic", fallback: false }
);
assert("Unaffected floor is quiet info", info?.tone === "info");
assert("Info includes coverage percent", info?.message === "Complaint partly matched (40%), severity unaffected.");
assert("Info carries mapped terms", info?.mappedTerms.includes("vaginal bleeding"));
assert("Info carries unmapped terms", info?.unmappedTerms.includes("pregnant"));
assert("Info notes specialty recognition", info?.specialtyRecognized === true);

const hidden = complaintMappingNotice(
  {
    mapped_terms: ["chest pain"],
    unmapped_terms: [],
    coverage: 1,
    threshold: 0.6,
    floor_applied: false,
    floor_changed_result: false,
    reason_code: null,
  },
  { primary: "Cardiovascular", fallback: false }
);
assert("Full match has no banner", hidden === null);

const danger = complaintMappingNotice(
  {
    mapped_terms: [],
    unmapped_terms: ["cyanosis"],
    coverage: 0,
    threshold: 0.5,
    floor_applied: true,
    floor_changed_result: true,
    reason_code: "DANGER_TERM_UNMAPPED",
  },
  { primary: "General Practice", fallback: true }
);
assert("Danger term mapping issue is warning", danger?.tone === "warning");
assert(
  "Danger term warning uses safety copy",
  danger?.message === "Safety-critical term not mapped - please review."
);

console.log("\n-- Matched rules display cleanup --");
const legacyRule = "complaint not recognised - review";
assert(
  "Legacy complaint review rule is hidden when severity unaffected",
  visibleMatchedRules([legacyRule, "red_flag_override"], {
    floor_changed_result: false,
  }).join(",") === "red_flag_override"
);
assert(
  "Legacy complaint review rule is shown when floor changed result",
  visibleMatchedRules([legacyRule], { floor_changed_result: true }).join(",") === legacyRule
);

console.log("\n------------------------------------------------------------");
console.log(`  ${passed} passed | ${failed} failed | ${passed + failed} total`);
console.log("------------------------------------------------------------\n");

if (failed > 0) {
  process.exit(1);
}
