import React, { useEffect, useState } from "react";
import { fetchMatches, Match } from "../src/api";
import { TipForm } from "./TipForm";

export const MatchList: React.FC = () => {
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMatches()
      .then(setMatches)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading matches...</div>;
  if (error) return <div style={{ color: "red" }}>Error loading matches: {error}</div>;

  return (
    <div>
      {matches.map((m) => (
        <div key={m.id} style={{ border: "1px solid #ccc", margin: "8px", padding: "8px" }}>
          <div>
            <strong>
              {m.home_team_name} vs {m.away_team_name}
            </strong>
          </div>
          <div>Stage: {m.stage} {m.group && `(Group ${m.group})`}</div>
          <div>
            Probabilities: 1 {(m.prediction.prob_home_win * 100).toFixed(1)}% | X{" "}
            {(m.prediction.prob_draw * 100).toFixed(1)}% | 2{" "}
            {(m.prediction.prob_away_win * 100).toFixed(1)}%
          </div>
          <div>
            Model tip: <strong>{m.prediction.recommended_outcome}</strong> (confidence margin{" "}
            {m.prediction.confidence_score.toFixed(1)}%)
          </div>
          <div style={{ marginTop: "4px", color: "#444", fontSize: "0.95em" }}>
            Why: {m.prediction.reason}
          </div>
          <TipForm matchId={m.id} />
        </div>
      ))}
    </div>
  );
};
