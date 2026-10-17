const ROLE_WEIGHT = {
  "Senior MO": 1.0,
  "Medical Officer": 0.85,
  Resident: 0.65,
  Intern: 0.45,
};

export const ROUTED_BY_NLP = "routed by NLP";
export const ROUTED_BY_SUGGESTED_SPECIALTY = "routed by suggested specialty";

export function useSuggestedSpecialtyRoutingFlag(env = import.meta.env) {
  return String(
    env?.VITE_USE_SUGGESTED_SPECIALTY_ROUTING ||
      env?.USE_SUGGESTED_SPECIALTY_ROUTING ||
      ""
  ).toLowerCase() === "true";
}

function eligibleMOs(mos, severity) {
  return (mos || []).filter((mo) => {
    const isJuniorWithoutSupervisor =
      ["Intern", "Resident"].includes(mo.role) && mo.supervisor !== "yes";
    return !(severity === "HIGH" && isJuniorWithoutSupervisor);
  });
}

export function specialtyMatches(candidate, target) {
  if (!candidate || !target) return false;
  return candidate.toLowerCase() === target.toLowerCase();
}

function moMatchesSpecialty(mo, specialty) {
  const primaryMatch = specialtyMatches(mo.specialty, specialty);
  const skillMatch = (mo.skills || []).some((skill) =>
    specialtyMatches(skill.name, specialty)
  );
  return primaryMatch || skillMatch;
}

export function hasSuggestedSpecialtyMatch(mos, suggestion) {
  if (!Array.isArray(mos) || !suggestion?.primary) return false;

  const suggestedSpecialties = [
    suggestion.primary,
    ...(suggestion.secondary || []),
  ].filter(Boolean);

  return suggestedSpecialties.some((specialty) =>
    mos.some((mo) => moMatchesSpecialty(mo, specialty))
  );
}

export function isSpecialtyUnmatched(mos, suggestion) {
  return Boolean(suggestion?.primary) && !hasSuggestedSpecialtyMatch(mos, suggestion);
}

export function specialtyUnmatchedWarningText(mos, suggestion, assignedMO) {
  if (!isSpecialtyUnmatched(mos, suggestion)) return "";

  return `No ${suggestion.primary} MO on the current roster. Assigned to ${
    assignedMO?.specialty || "fallback"
  } by fallback. Consider escalating or adding an MO.`;
}

export function routeMO(mos, severity, conditionGroup) {
  const eligible = eligibleMOs(mos, severity);

  if (!eligible.length) return null;

  const scored = eligible.map((mo) => {
    const condition = conditionGroup.toLowerCase();
    const specMatch =
      mo.specialty.toLowerCase().includes(condition) ||
      mo.skills.some((skill) => skill.name.toLowerCase().includes(condition));
    const roleScore = ROLE_WEIGHT[mo.role] || 0.5;
    const loadScore = 1 / (1 + (mo.queueDepth || 0));

    return {
      mo,
      score: roleScore * (0.5 + 0.5 * Number(specMatch)) * loadScore,
    };
  });

  scored.sort((first, second) => second.score - first.score);
  return scored[0].mo;
}

export function findRecommendedMO(mos, suggestion, severity = "LOW") {
  if (!Array.isArray(mos) || !suggestion?.primary) return null;

  const preferredSpecialties = [
    suggestion.primary,
    ...(suggestion.secondary || []),
  ].filter(Boolean);
  const eligible = eligibleMOs(mos, severity);

  for (const specialty of preferredSpecialties) {
    const matches = eligible.filter((mo) => moMatchesSpecialty(mo, specialty));

    if (matches.length) {
      return [...matches].sort(
        (first, second) => (first.queueDepth || 0) - (second.queueDepth || 0)
      )[0];
    }
  }

  return null;
}

export function chooseRoutedMO(
  mos,
  severity,
  nlpSpecialty,
  suggestedSpecialty,
  useSuggestedSpecialtyRouting = false
) {
  if (useSuggestedSpecialtyRouting && suggestedSpecialty?.primary) {
    const preferredSpecialties = [
      suggestedSpecialty.primary,
      ...(suggestedSpecialty.secondary || []),
      "General Practice",
    ].filter(Boolean);
    const eligible = eligibleMOs(mos, severity);

    for (const specialty of preferredSpecialties) {
      const matches = eligible.filter((mo) => moMatchesSpecialty(mo, specialty));
      if (matches.length) {
        const mo = [...matches].sort(
          (first, second) => (first.queueDepth || 0) - (second.queueDepth || 0)
        )[0];
        return {
          mo,
          source: "suggested_specialty",
          auditLabel: ROUTED_BY_SUGGESTED_SPECIALTY,
          specialty,
        };
      }
    }
  }

  return {
    mo: routeMO(mos, severity, nlpSpecialty),
    source: "nlp",
    auditLabel: ROUTED_BY_NLP,
    specialty: nlpSpecialty,
  };
}
