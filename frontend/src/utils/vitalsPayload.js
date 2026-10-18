export const priorityVitalFields = [
  { key: "vital_hr", label: "Heart rate", unit: "bpm", min: 20, max: 250, step: "1" },
  { key: "vital_spo2", label: "SpO2", unit: "%", min: 50, max: 100, step: "1" },
  { key: "vital_sbp", label: "Systolic BP", unit: "mmHg", min: 50, max: 300, step: "1" },
  { key: "vital_rr", label: "Respiratory rate", unit: "/min", min: 4, max: 80, step: "1" },
  { key: "vital_temp", label: "Temperature", unit: "C", min: 30, max: 43, step: "0.1" },
  { key: "pain_score", label: "Pain", unit: "0-10", min: 0, max: 10, step: "1" },
];

export function buildVitalsPayload(form) {
  return Object.fromEntries(
    priorityVitalFields
      .filter(({ key }) => form[key] !== "")
      .map(({ key }) => [key, Number(form[key])])
  );
}
