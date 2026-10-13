import { buildVitalsPayload } from "./src/utils/vitalsPayload.js";

let passed = 0;
let failed = 0;

function assertDeepEqual(name, actual, expected) {
  const actualJson = JSON.stringify(actual);
  const expectedJson = JSON.stringify(expected);
  if (actualJson !== expectedJson) {
    failed += 1;
    console.error(`FAIL ${name}`);
    console.error(`  expected ${expectedJson}`);
    console.error(`  actual   ${actualJson}`);
    return;
  }
  passed += 1;
  console.log(`PASS ${name}`);
}

const form = {
  age: "29",
  symptoms: "Small cut on the hand, mild pain",
  clinicalNote:
    "Superficial 2 cm laceration from broken glass, bleeding controlled. Wound cleaned and dressed. Vitals stable.",
  vital_hr: "78",
  vital_spo2: "99",
  vital_sbp: "122",
  vital_rr: "16",
  vital_temp: "36.7",
  pain_score: "2",
};

assertDeepEqual(
  "buildVitalsPayload uses backend vital keys and percent-scale SpO2",
  buildVitalsPayload(form),
  {
    vital_hr: 78,
    vital_spo2: 99,
    vital_sbp: 122,
    vital_rr: 16,
    vital_temp: 36.7,
    pain_score: 2,
  }
);

console.log(`\n${passed} passed | ${failed} failed | ${passed + failed} total`);
if (failed) process.exit(1);
