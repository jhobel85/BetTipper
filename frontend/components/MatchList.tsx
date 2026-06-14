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
          {m.bookmaker_tip ? (
            <div style={{ marginTop: "6px", background: "#f7f8fa", padding: "6px 8px", borderRadius: "4px" }}>
              Bookmaker tip ({m.bookmaker_tip.source}):{" "}
              <strong>{m.bookmaker_tip.recommended_outcome}</strong> (confidence margin{" "}
              {m.bookmaker_tip.confidence_score.toFixed(1)}%) | Odds 1 {m.bookmaker_tip.odds_home.toFixed(2)} / X{" "}
              {m.bookmaker_tip.odds_draw.toFixed(2)} / 2 {m.bookmaker_tip.odds_away.toFixed(2)}
              {m.bookmaker_tip.best_value_outcome &&
              m.bookmaker_tip.best_value_ev_pct !== null &&
              m.bookmaker_tip.best_value_ev_pct !== undefined ? (
                <div style={{ marginTop: "4px", color: "#0a5b18", fontWeight: 600 }}>
                  Best opportunity: {m.bookmaker_tip.best_value_outcome} (EV{" "}
                  {m.bookmaker_tip.best_value_ev_pct.toFixed(1)}%, edge{" "}
                  {(m.bookmaker_tip.best_value_edge_pct ?? 0).toFixed(1)}%)
                </div>
              ) : (
                <div style={{ marginTop: "4px", color: "#666" }}>
                  No positive value edge against model probabilities.
                </div>
              )}
            </div>
          ) : (
            <div style={{ marginTop: "6px", color: "#666", fontSize: "0.9em" }}>
              Bookmaker tip: not available for this match.
            </div>
          )}
          <TipForm matchId={m.id} />
        </div>
      ))}
    </div>
  );
};
