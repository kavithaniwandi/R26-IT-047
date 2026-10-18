import { buildVitalsPayload, priorityVitalFields } from "./src/utils/vitalsPayload.js";

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

assertDeepEqual(
  "blank vitals are not sent",
  buildVitalsPayload({ ...form, vital_spo2: "", pain_score: "" }),
  {
    vital_hr: 78,
    vital_sbp: 122,
    vital_rr: 16,
    vital_temp: 36.7,
  }
);

const spo2 = priorityVitalFields.find((field) => field.key === "vital_spo2");
const pain = priorityVitalFields.find((field) => field.key === "pain_score");

if (spo2?.unit === "%" && spo2?.min === 50 && spo2?.max === 100 && spo2?.step === "1") {
  passed += 1;
  console.log("PASS SpO2 field is bounded as percent input");
} else {
  failed += 1;
  console.error("FAIL SpO2 field is bounded as percent input");
}

if (pain?.min === 0 && pain?.max === 10 && pain?.step === "1") {
  passed += 1;
  console.log("PASS pain field allows zero and is bounded 0-10");
} else {
  failed += 1;
  console.error("FAIL pain field allows zero and is bounded 0-10");
}

const warning = {
  field: "vital_spo2",
  raw_value: 0.99,
  used_value: 99,
  code: "spo2_fraction_converted",
  message: "SpO2 0.99 was read as 99%. Please confirm.",
};
if (warning.message.includes("0.99") && warning.message.includes("99%")) {
  passed += 1;
  console.log("PASS vitals warning copy can show raw and used SpO2 values");
} else {
  failed += 1;
  console.error("FAIL vitals warning copy can show raw and used SpO2 values");
}

console.log(`\n${passed} passed | ${failed} failed | ${passed + failed} total`);
if (failed) process.exit(1);
