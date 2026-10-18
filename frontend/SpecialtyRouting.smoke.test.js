import assert from "node:assert/strict";
import { chooseRoutedMO, findRecommendedMO, useSuggestedSpecialtyRoutingFlag as routingEnabled } from "./src/utils/triageRouting.js";

const roster = [
  { id: "resp", role: "Senior MO", specialty: "Respiratory", skills: [], queueDepth: 0 },
  { id: "gi-busy", role: "Senior MO", specialty: "Gastrointestinal", skills: [], queueDepth: 5 },
  { id: "gi-free", role: "Senior MO", specialty: "Gastrointestinal", skills: [], queueDepth: 0 },
  { id: "gp", role: "Senior MO", specialty: "General Practice", skills: [], queueDepth: 0 },
];
const suggestion = { primary: "Gastrointestinal", secondary: [] };
assert.equal(routingEnabled({}), true);
assert.equal(routingEnabled({ VITE_USE_SUGGESTED_SPECIALTY_ROUTING: "false" }), false);
assert.equal(chooseRoutedMO(roster, "MEDIUM", "Respiratory", suggestion).mo.id, "gi-free");
assert.equal(chooseRoutedMO(roster, "MEDIUM", "Respiratory", suggestion, false).mo.id, "resp");

const fallback = chooseRoutedMO(roster.filter((mo) => !mo.id.startsWith("gi")), "MEDIUM", "Respiratory", suggestion);
assert.equal(fallback.mo.id, "gp");
assert.equal(fallback.source, "suggested_specialty_fallback");
assert.match(fallback.auditLabel, /roster fallback/);

const secondary = chooseRoutedMO(roster, "MEDIUM", "Respiratory", { primary: "Pediatric", secondary: ["Gastrointestinal"] });
assert.equal(secondary.mo.id, "gi-free");

const empty = chooseRoutedMO([], "HIGH", "Respiratory", suggestion);
assert.equal(empty.mo, null);
assert.match(empty.auditLabel, /manual assignment required/);

const supervised = [
  { id: "junior", role: "Intern", supervisor: "no", specialty: "Gastrointestinal", skills: [], queueDepth: 0 },
  roster[3],
];
assert.equal(chooseRoutedMO(supervised, "HIGH", "Respiratory", suggestion).mo.id, "gp");

const lowRoster = [
  { ...roster[2], skills: [{ name: "General Practice" }], queueDepth: 0 },
  { ...roster[3], queueDepth: 10 },
];
assert.equal(chooseRoutedMO(lowRoster, "LOW", "Gastrointestinal", suggestion).mo.id, "gp");
assert.equal(findRecommendedMO(lowRoster, suggestion, "LOW").id, "gp");
assert.equal(chooseRoutedMO(lowRoster, "MEDIUM", "Gastrointestinal", suggestion).mo.id, "gi-free");
assert.equal(chooseRoutedMO(roster.filter((mo) => mo.id !== "gp"), "LOW", "Respiratory", suggestion).mo.id, "gi-free");
for (const specialty of ["Pediatric", "Obstetric & Gynecologic"]) {
  const exceptionRoster = [...lowRoster, { id: "exception", role: "Senior MO", specialty, skills: [], queueDepth: 0 }];
  assert.equal(chooseRoutedMO(exceptionRoster, "LOW", specialty, { primary: specialty }).mo.id, "exception");
}
console.log("PASS specialty routing defaults, explicit rollback, primary/secondary matching, load, fallback and eligibility");
console.log("PASS LOW prioritizes General Practice primary MOs; recommendations agree; Pediatric/Obstetric and unavailable-GP fallbacks remain");
