import assert from "node:assert/strict";
import { loadTriageCamps } from "./src/utils/triageCamps.js";

const reliefCamp = {
  id: "507f1f77bcf86cd799439011",
  name: "Test relief camp",
  dsArea: "Kaduwela",
  gnDivision: "Ranala",
  maxCapacityPersons: 120,
};
let mongoCalls = 0;
const api = {
  async getReliefCamps() {
    mongoCalls += 1;
    return [reliefCamp];
  },
  async getCamps() {
    assert.fail("Triage must not load SQL medical camps");
  },
};

const [camp] = await loadTriageCamps(api);
assert.equal(mongoCalls, 1);
assert.equal(camp.id, reliefCamp.id, "Mongo IDs must survive session persistence");
assert.equal(camp.ds_division, "Kaduwela");
assert.equal(camp.gn_division, "Ranala");
assert.equal(camp.estimated_capacity, 120);
assert.deepEqual(reliefCamp, {
  id: "507f1f77bcf86cd799439011",
  name: "Test relief camp",
  dsArea: "Kaduwela",
  gnDivision: "Ranala",
  maxCapacityPersons: 120,
});

assert.deepEqual(await loadTriageCamps({ getReliefCamps: async () => [] }), []);
await assert.rejects(
  loadTriageCamps({ getReliefCamps: async () => ({}) }),
  /invalid relief-camp list/,
);
const unavailable = new Error("Relief camps unavailable");
await assert.rejects(
  loadTriageCamps({ ...api, getReliefCamps: async () => { throw unavailable; } }),
  (error) => error === unavailable,
);
console.log("PASS: Mongo camp IDs, location/capacity mapping, and no SQL fallback");
