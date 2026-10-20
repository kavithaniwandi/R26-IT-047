// Triage uses the Mongo relief-camp registry; other workflows retain /camps.
export const triageCampLocation = (camp) =>
  [camp.ds_division, camp.gn_division].filter(Boolean).join(" · ");

export async function loadTriageCamps(api) {
  const camps = await api.getReliefCamps();
  if (!Array.isArray(camps)) {
    throw new Error("The server returned an invalid relief-camp list.");
  }

  return camps.map((camp) => ({
    ...camp,
    ds_division: camp.dsArea,
    gn_division: camp.gnDivision,
    estimated_capacity: camp.maxCapacityPersons,
  }));
}
