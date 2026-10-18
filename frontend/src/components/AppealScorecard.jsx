import React from "react";
import "./AppealScorecard.css";

export default function AppealScorecard({ result }) {
  if (!result) return null;
  const label = result.final_label ?? result.quality_label ?? result.label ?? result.status;
  const score = result.quality_score ?? result.score;
  return <div className="appeal-scorecard">
    <div className="appeal-scorecard-main">
      <strong className="appeal-scorecard-label">{label}</strong>
      <span className="appeal-scorecard-score">{Number(score).toFixed(2)}</span>
    </div>
  </div>;
}
