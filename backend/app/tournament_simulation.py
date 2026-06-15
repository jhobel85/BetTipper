import math
import random
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from .model import DEFAULT_PARAMS, MatchFeatures, predict_match
from .models import Match, ModelPrediction, Team


@dataclass
class _TableStats:
    points: int = 0
    goals_for: int = 0
    goals_against: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against


def _normalize_group(value: str | None) -> str | None:
    if not value:
        return None
    text = value.strip()
    if text.startswith("GROUP_") and len(text) > 6:
        return text.split("_", 1)[1]
    return text


def _safe_float(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _team_overall(team: Team) -> float:
    if team.rating_overall is not None:
        return _safe_float(team.rating_overall, 2.0)
    return _safe_float(team.rating_attack, 1.0) + _safe_float(team.rating_defense, 1.0)


def _team_attack(team: Team) -> float:
    return _safe_float(team.rating_attack, 1.0)


def _sample_poisson(lam: float, rng: random.Random) -> int:
    lam = max(0.01, lam)
    l_value = math.exp(-lam)
    k_value = 0
    p_value = 1.0
    while p_value > l_value:
        k_value += 1
        p_value *= rng.random()
    return max(0, k_value - 1)


def _apply_result(home: _TableStats, away: _TableStats, goals_home: int, goals_away: int) -> None:
    home.goals_for += goals_home
    home.goals_against += goals_away
    away.goals_for += goals_away
    away.goals_against += goals_home
    if goals_home > goals_away:
        home.points += 3
        home.wins += 1
        away.losses += 1
    elif goals_home < goals_away:
        away.points += 3
        away.wins += 1
        home.losses += 1
    else:
        home.points += 1
        away.points += 1
        home.draws += 1
        away.draws += 1


def _h2h_summary(
    team_id: int,
    tied_ids: list[int],
    h2h_table: dict[int, dict[int, _TableStats]],
) -> tuple[int, int, int]:
    points = 0
    gd = 0
    gf = 0
    for opp_id in tied_ids:
        if opp_id == team_id:
            continue
        stats = h2h_table.get(team_id, {}).get(opp_id)
        if not stats:
            continue
        points += stats.points
        gd += stats.goal_diff
        gf += stats.goals_for
    return points, gd, gf


def _rank_group(
    group_team_ids: list[int],
    table: dict[int, _TableStats],
    h2h_table: dict[int, dict[int, _TableStats]],
    team_by_id: dict[int, Team],
) -> list[int]:
    points_buckets: dict[int, list[int]] = defaultdict(list)
    for team_id in group_team_ids:
        points_buckets[table[team_id].points].append(team_id)

    ranking: list[int] = []
    for points in sorted(points_buckets.keys(), reverse=True):
        bucket = points_buckets[points]
        if len(bucket) == 1:
            ranking.extend(bucket)
            continue
        bucket_sorted = sorted(
            bucket,
            key=lambda team_id: (
                -_h2h_summary(team_id, bucket, h2h_table)[0],
                -_h2h_summary(team_id, bucket, h2h_table)[1],
                -_h2h_summary(team_id, bucket, h2h_table)[2],
                -table[team_id].goal_diff,
                -table[team_id].goals_for,
                -table[team_id].wins,
                team_by_id[team_id].fifa_code or team_by_id[team_id].name,
            ),
        )
        ranking.extend(bucket_sorted)
    return ranking


def _pair_prediction(
    home: Team,
    away: Team,
    pair_cache: dict[tuple[int, int], dict[str, float]],
) -> dict[str, float]:
    key = (home.id, away.id)
    cached = pair_cache.get(key)
    if cached:
        return cached
    features = MatchFeatures(
        rating_home=_team_overall(home),
        rating_away=_team_overall(away),
        xg_home=_team_attack(home) * 0.9,
        xg_away=_team_attack(away) * 0.9,
        home_advantage=0.0,
    )
    predicted = predict_match(features, DEFAULT_PARAMS)
    result = {
        "lambda_home": float(predicted["lambda_home"]),
        "lambda_away": float(predicted["lambda_away"]),
        "prob_home_win": float(predicted["prob_home_win"]),
        "prob_draw": float(predicted["prob_draw"]),
        "prob_away_win": float(predicted["prob_away_win"]),
    }
    pair_cache[key] = result
    return result


def _simulate_match_goals(
    prediction: dict[str, float],
    rng: random.Random,
) -> tuple[int, int]:
    return _sample_poisson(prediction["lambda_home"], rng), _sample_poisson(prediction["lambda_away"], rng)


def _simulate_knockout_winner(
    team_home: Team,
    team_away: Team,
    pair_cache: dict[tuple[int, int], dict[str, float]],
    rng: random.Random,
) -> int:
    prediction = _pair_prediction(team_home, team_away, pair_cache)
    goals_home, goals_away = _simulate_match_goals(prediction, rng)
    if goals_home > goals_away:
        return team_home.id
    if goals_away > goals_home:
        return team_away.id
    p_home = prediction["prob_home_win"]
    p_away = prediction["prob_away_win"]
    total = max(0.000001, p_home + p_away)
    return team_home.id if rng.random() < (p_home / total) else team_away.id


def _simulate_pairs(
    pairings: list[tuple[int, int]],
    team_by_id: dict[int, Team],
    pair_cache: dict[tuple[int, int], dict[str, float]],
    rng: random.Random,
) -> list[int]:
    winners: list[int] = []
    for home_id, away_id in pairings:
        winners.append(
            _simulate_knockout_winner(
                team_by_id[home_id],
                team_by_id[away_id],
                pair_cache=pair_cache,
                rng=rng,
            )
        )
    return winners


def _choose_opponent(
    pool: list[int],
    group_by_team: dict[int, str],
    team_id: int,
    prefer_weakest: bool = True,
) -> int | None:
    indices = range(len(pool) - 1, -1, -1) if prefer_weakest else range(len(pool))
    team_group = group_by_team.get(team_id)
    for idx in indices:
        opp_id = pool[idx]
        if group_by_team.get(opp_id) != team_group:
            return pool.pop(idx)
    if not pool:
        return None
    return pool.pop(len(pool) - 1 if prefer_weakest else 0)


def _to_pairings(sequence: list[int]) -> list[tuple[int, int]]:
    pairings: list[tuple[int, int]] = []
    for idx in range(0, len(sequence), 2):
        if idx + 1 >= len(sequence):
            break
        pairings.append((sequence[idx], sequence[idx + 1]))
    return pairings


def run_tournament_monte_carlo(db: Session, simulations: int = 5000, seed: int | None = None) -> dict[str, Any]:
    if simulations < 1:
        raise ValueError("simulations must be >= 1")

    teams = db.query(Team).all()
    team_by_id = {team.id: team for team in teams}
    grouped_teams: dict[str, list[int]] = defaultdict(list)
    group_by_team: dict[int, str] = {}
    for team in teams:
        group = _normalize_group(team.group)
        if group:
            grouped_teams[group].append(team.id)
            group_by_team[team.id] = group
    if not grouped_teams:
        raise RuntimeError("No grouped teams found. Load teams first.")

    group_matches: dict[str, list[Match]] = defaultdict(list)
    matches = db.query(Match).filter(Match.stage == "GROUP_STAGE").all()
    for match in matches:
        group = _normalize_group(match.group)
        if group:
            group_matches[group].append(match)
    if not group_matches:
        raise RuntimeError("No group-stage matches found. Load matches first.")

    model_predictions = db.query(ModelPrediction).all()
    pred_by_match = {pred.match_id: pred for pred in model_predictions}
    pair_cache: dict[tuple[int, int], dict[str, float]] = {}

    first_counts: dict[int, int] = defaultdict(int)
    qualify_counts: dict[int, int] = defaultdict(int)
    position_counts: dict[int, dict[int, int]] = defaultdict(lambda: defaultdict(int))
    champion_counts: dict[int, int] = defaultdict(int)
    reach_r32: dict[int, int] = defaultdict(int)
    reach_r16: dict[int, int] = defaultdict(int)
    reach_qf: dict[int, int] = defaultdict(int)
    reach_sf: dict[int, int] = defaultdict(int)
    reach_final: dict[int, int] = defaultdict(int)

    for run in range(simulations):
        rng = random.Random((seed or 0) + run)
        group_tables: dict[str, dict[int, _TableStats]] = {
            group: {team_id: _TableStats() for team_id in team_ids}
            for group, team_ids in grouped_teams.items()
        }
        group_h2h: dict[str, dict[int, dict[int, _TableStats]]] = {
            group: {team_id: {} for team_id in team_ids}
            for group, team_ids in grouped_teams.items()
        }
        group_rankings: dict[str, list[int]] = {}

        for group, team_ids in grouped_teams.items():
            table = group_tables[group]
            h2h_table = group_h2h[group]
            for match in group_matches.get(group, []):
                if match.home_team_id not in table or match.away_team_id not in table:
                    continue
                if (
                    match.status == "finished"
                    and match.result_home_goals is not None
                    and match.result_away_goals is not None
                ):
                    goals_home = int(match.result_home_goals)
                    goals_away = int(match.result_away_goals)
                else:
                    prediction = pred_by_match.get(match.id)
                    if prediction:
                        pred_data = {
                            "lambda_home": float(prediction.lambda_home),
                            "lambda_away": float(prediction.lambda_away),
                            "prob_home_win": float(prediction.prob_home_win),
                            "prob_draw": float(prediction.prob_draw),
                            "prob_away_win": float(prediction.prob_away_win),
                        }
                    else:
                        pred_data = _pair_prediction(
                            team_by_id[match.home_team_id],
                            team_by_id[match.away_team_id],
                            pair_cache=pair_cache,
                        )
                    goals_home, goals_away = _simulate_match_goals(pred_data, rng)

                _apply_result(table[match.home_team_id], table[match.away_team_id], goals_home, goals_away)
                if match.away_team_id not in h2h_table[match.home_team_id]:
                    h2h_table[match.home_team_id][match.away_team_id] = _TableStats()
                if match.home_team_id not in h2h_table[match.away_team_id]:
                    h2h_table[match.away_team_id][match.home_team_id] = _TableStats()
                _apply_result(
                    h2h_table[match.home_team_id][match.away_team_id],
                    h2h_table[match.away_team_id][match.home_team_id],
                    goals_home,
                    goals_away,
                )

            ranking = _rank_group(team_ids, table, h2h_table, team_by_id)
            group_rankings[group] = ranking
            if ranking:
                first_counts[ranking[0]] += 1
            for idx, team_id in enumerate(ranking):
                position_counts[team_id][idx + 1] += 1
                if idx < 2:
                    qualify_counts[team_id] += 1

        winner_rows: list[tuple[int, int, int, int, str]] = []
        runner_rows: list[tuple[int, int, int, int, str]] = []
        third_rows: list[tuple[int, int, int, int, str]] = []
        for group, ranking in group_rankings.items():
            table = group_tables[group]
            if len(ranking) > 0:
                first = ranking[0]
                s = table[first]
                winner_rows.append((first, s.points, s.goal_diff, s.goals_for, group))
            if len(ranking) > 1:
                second = ranking[1]
                s = table[second]
                runner_rows.append((second, s.points, s.goal_diff, s.goals_for, group))
            if len(ranking) > 2:
                third = ranking[2]
                s = table[third]
                third_rows.append((third, s.points, s.goal_diff, s.goals_for, group))

        winner_rows.sort(key=lambda row: (-row[1], -row[2], -row[3], team_by_id[row[0]].fifa_code or team_by_id[row[0]].name))
        runner_rows.sort(key=lambda row: (-row[1], -row[2], -row[3], team_by_id[row[0]].fifa_code or team_by_id[row[0]].name))
        third_rows.sort(key=lambda row: (-row[1], -row[2], -row[3], team_by_id[row[0]].fifa_code or team_by_id[row[0]].name))

        winners = [row[0] for row in winner_rows]
        runners = [row[0] for row in runner_rows]
        best_thirds = [row[0] for row in third_rows[:8]]
        if len(winners) < 12 or len(runners) < 12 or len(best_thirds) < 8:
            continue

        # Build R32 pairings using a seeded structure:
        # - 8 winners vs best third teams
        # - 4 winners vs runners-up
        # - 4 runners-up vs runners-up
        r32_pairs: list[tuple[int, int]] = []

        third_pool = list(reversed(best_thirds))  # weakest third first for strongest winner
        for winner_id in winners[:8]:
            opponent = _choose_opponent(third_pool, group_by_team, winner_id, prefer_weakest=True)
            if opponent is None:
                break
            r32_pairs.append((winner_id, opponent))

        remaining_winners = winners[8:]
        runner_pool = list(runners)
        for winner_id in remaining_winners:
            opponent = _choose_opponent(runner_pool, group_by_team, winner_id, prefer_weakest=False)
            if opponent is None:
                break
            r32_pairs.append((winner_id, opponent))

        while len(runner_pool) >= 2:
            a_id = runner_pool.pop(0)
            b_id = _choose_opponent(runner_pool, group_by_team, a_id, prefer_weakest=True)
            if b_id is None:
                break
            r32_pairs.append((a_id, b_id))

        if len(r32_pairs) != 16:
            continue

        for home_id, away_id in r32_pairs:
            reach_r32[home_id] += 1
            reach_r32[away_id] += 1

        r32_winners = _simulate_pairs(r32_pairs, team_by_id, pair_cache=pair_cache, rng=rng)
        for team_id in r32_winners:
            reach_r16[team_id] += 1

        r16_pairs = _to_pairings(r32_winners)
        r16_winners = _simulate_pairs(r16_pairs, team_by_id, pair_cache=pair_cache, rng=rng)
        for team_id in r16_winners:
            reach_qf[team_id] += 1

        qf_pairs = _to_pairings(r16_winners)
        qf_winners = _simulate_pairs(qf_pairs, team_by_id, pair_cache=pair_cache, rng=rng)
        for team_id in qf_winners:
            reach_sf[team_id] += 1

        sf_pairs = _to_pairings(qf_winners)
        sf_winners = _simulate_pairs(sf_pairs, team_by_id, pair_cache=pair_cache, rng=rng)
        for team_id in sf_winners:
            reach_final[team_id] += 1

        final_pairs = _to_pairings(sf_winners)
        final_winners = _simulate_pairs(final_pairs, team_by_id, pair_cache=pair_cache, rng=rng)
        if final_winners:
            champion_counts[final_winners[0]] += 1

    group_output: dict[str, list[dict[str, Any]]] = {}
    for group, team_ids in grouped_teams.items():
        rows: list[dict[str, Any]] = []
        group_size = len(team_ids)
        for team_id in team_ids:
            team = team_by_id[team_id]
            pos_probs = {
                str(position): position_counts[team_id][position] / simulations
                for position in range(1, group_size + 1)
            }
            rows.append(
                {
                    "group": group,
                    "team": team.name,
                    "fifa_code": team.fifa_code or "",
                    "qualify_probability": qualify_counts[team_id] / simulations,
                    "first_place_probability": first_counts[team_id] / simulations,
                    "position_probabilities": pos_probs,
                }
            )
        rows.sort(key=lambda row: (-row["qualify_probability"], -row["first_place_probability"], row["team"]))
        group_output[group] = rows

    tournament_rows: list[dict[str, Any]] = []
    for team in teams:
        tournament_rows.append(
            {
                "team": team.name,
                "fifa_code": team.fifa_code or "",
                "round_of_32_probability": reach_r32[team.id] / simulations,
                "round_of_16_probability": reach_r16[team.id] / simulations,
                "quarterfinal_probability": reach_qf[team.id] / simulations,
                "semifinal_probability": reach_sf[team.id] / simulations,
                "final_probability": reach_final[team.id] / simulations,
                "champion_probability": champion_counts[team.id] / simulations,
            }
        )
    tournament_rows.sort(key=lambda row: (-row["champion_probability"], -row["final_probability"], row["team"]))

    return {
        "simulations": simulations,
        "group_qualification_probabilities": group_output,
        "tournament_probabilities": tournament_rows,
    }
