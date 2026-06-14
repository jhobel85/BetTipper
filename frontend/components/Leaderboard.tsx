import React, { useEffect, useState } from "react";
import { fetchLeaderboard, LeaderboardEntry } from "../src/api";

export const Leaderboard: React.FC = () => {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchLeaderboard()
      .then(setEntries)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div>Loading leaderboard...</div>;
  if (error) return <div style={{ color: "red" }}>{error}</div>;

  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <thead>
        <tr>
          <th style={{ textAlign: "left" }}>Rank</th>
          <th style={{ textAlign: "left" }}>Name</th>
          <th style={{ textAlign: "left" }}>Points</th>
        </tr>
      </thead>
      <tbody>
        {entries.map((entry, index) => (
          <tr key={entry.display_name}>
            <td>{index + 1}</td>
            <td>{entry.display_name}</td>
            <td>{entry.total_points}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};
