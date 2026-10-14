const UNMAPPED_DISPLAY_STOPWORDS = new Set([
  "a",
  "an",
  "and",
  "for",
  "from",
  "hour",
  "hours",
  "in",
  "is",
  "male",
  "female",
  "minute",
  "minutes",
  "of",
  "old",
  "on",
  "patient",
  "the",
  "to",
  "with",
  "year",
  "years",
]);

function displayUnmappedTerms(terms = []) {
  return (terms || []).filter((term) => {
    const normalized = String(term || "").trim().toLowerCase();
    return normalized && !/^\d+(?:\.\d+)?$/.test(normalized) && !UNMAPPED_DISPLAY_STOPWORDS.has(normalized);
  });
}

export function complaintMappingNotice(complaintMapping, suggestedSpecialty) {
  if (!complaintMapping) return null;

  const coveragePercent = Math.round((complaintMapping.coverage || 0) * 100);
  const mappedTerms = complaintMapping.mapped_terms || [];
  const unmappedTerms = displayUnmappedTerms(complaintMapping.unmapped_terms || []);
  const specialtyRecognized =
    suggestedSpecialty && suggestedSpecialty.fallback === false;

  if (
    complaintMapping.floor_changed_result ||
    complaintMapping.reason_code === "DANGER_TERM_UNMAPPED"
  ) {
    const reviewMessage = mappedTerms.length > 0
      ? "Complaint partly matched - please review."
      : "No complaint recognised - please review.";
    return {
      tone: "warning",
      message:
        complaintMapping.reason_code === "DANGER_TERM_UNMAPPED"
          ? "Safety-critical term not mapped - please review."
          : reviewMessage,
      mappedTerms,
      unmappedTerms,
      coveragePercent,
      specialtyRecognized,
    };
  }

  if (
    complaintMapping.reason_code &&
    (mappedTerms.length > 0 || unmappedTerms.length > 0)
  ) {
    return {
      tone: "info",
      message: `Complaint partly matched (${coveragePercent}%), severity unaffected.`,
      mappedTerms,
      unmappedTerms,
      coveragePercent,
      specialtyRecognized,
    };
  }

  return unmappedTerms.length
    ? {
        tone: "info",
        message: `Complaint partly matched (${coveragePercent}%), severity unaffected.`,
        mappedTerms,
        unmappedTerms,
        coveragePercent,
        specialtyRecognized,
      }
    : null;
}

export function visibleMatchedRules(matchedRules = [], complaintMapping = null) {
  return (matchedRules || []).filter((rule) => {
    const text = String(rule || "");
    const isComplaintReview = text.includes("complaint not recognised");
    return !isComplaintReview || complaintMapping?.floor_changed_result === true;
  });
}
