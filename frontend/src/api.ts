export type MatchPrediction = {
  prob_home_win: number;
  prob_draw: number;
  prob_away_win: number;
  recommended_outcome: string;
  confidence_score: number;
  reason: string;
};

export type BookmakerTip = {
  recommended_outcome: string;
  confidence_score: number;
  odds_home: number;
  odds_draw: number;
  odds_away: number;
  implied_home: number;
  implied_draw: number;
  implied_away: number;
  source: string;
  best_value_outcome?: string | null;
  best_value_edge_pct?: number | null;
  best_value_ev_pct?: number | null;
};

export type Match = {
  id: number;
  home_team_name: string;
  away_team_name: string;
  kickoff_at: string;
  stage: string;
  group?: string;
  status: string;
  prediction: MatchPrediction;
  bookmaker_tip?: BookmakerTip | null;
};

export type LeaderboardEntry = {
  display_name: string;
  total_points: number;
};

export type RegisteredUser = {
  id: number;
  email: string;
  display_name: string;
};

export async function fetchMatches(): Promise<Match[]> {
  const res = await fetch("/api/v1/matches/");
  if (!res.ok) throw new Error("Failed to fetch matches");
  return res.json();
}

export async function postTip(matchId: number, predicted_outcome: string) {
  const res = await fetch(`/api/v1/matches/${matchId}/tips`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ predicted_outcome })
  });
  if (!res.ok) throw new Error("Failed to post tip");
  return res.json();
}

export async function fetchLeaderboard(): Promise<LeaderboardEntry[]> {
  const res = await fetch("/api/v1/leaderboard/global");
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return res.json();
}

export async function loginUser(email: string, password: string): Promise<RegisteredUser> {
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) throw new Error("Login failed");
  return res.json();
}

export async function registerUser(email: string, password: string, displayName: string): Promise<RegisteredUser> {
  const res = await fetch("/api/v1/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, display_name: displayName })
  });
  if (!res.ok) {
    throw new Error("Failed to register user");
  }
  return res.json();
}
