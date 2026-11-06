 """standings.py - compute the league table from match results (Mission D).

Fill in each function, top to bottom. After each one, run from the project root:
    python -m tournament.standings

THE BIG RULE: standings are DERIVED. We never store a scoreboard. Every call
rebuilds the table from the teams and the PLAYED fixtures, so the table can
never disagree with the matches (the matches are the source of truth).

Row = {"team_id", "name", "played", "wins", "draws", "losses",
       "goals_for", "goals_against", "goal_diff", "points"}
Points: win 3, draw 1, loss 0.
Ranking: points (high first), goal difference (high first), goals for
(high first), then normalized team name A to Z. No head-to-head rule.
Only cli.py uses print()/input().
"""

from tournament.teams import normalize_name

POINTS_WIN = 3
POINTS_DRAW = 1
POINTS_LOSS = 0


# ---------------------------------------------------------------
# 1. new_row   (about 12 lines)
# ---------------------------------------------------------------
def new_row(team):
    return {
        "team_id": team["id"],
        "name": team["name"],
        "played": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "goal_diff": 0,
        "points": 0,
    }

def add_result(row, goals_for, goals_against):
    row["played"] += 1
    row["goals_for"] += goals_for
    row["goals_against"] += goals_against
    if goals_for > goals_against:
        row["wins"] += 1
        row["points"] += POINTS_WIN
    elif goals_for == goals_against:
        row["draws"] += 1
        row["points"] += POINTS_DRAW
    else:
        row["losses"] += 1
        row["points"] += POINTS_LOSS

def compute_standings(teams, fixtures):
        rows = {team["id"]: new_row(team) for team in teams}
 
    for fixture in fixtures:
        if fixture["status"] != "played":
            continue                                  # pending games earn nothing
        home = rows[fixture["home_id"]]
        away = rows[fixture["away_id"]]
        home_goals = fixture["home_score"]
        away_goals = fixture["away_score"]
        add_result(home, home_goals, away_goals)      # one match, two rows,
        add_result(away, away_goals, home_goals)      # numbers swapped
 
    for row in rows.values():
        row["goal_diff"] = row["goals_for"] - row["goals_against"]
 
    return list(rows.values())                        # keeps registration order


# ---------------------------------------------------------------
# 4. rank_standings   (about 6 lines)
# ---------------------------------------------------------------
def rank_standings(rows):
    """Return a NEW list sorted by the four ranking rules."""
    # One call to sorted(rows, key=...) is enough.
    # The problem to solve: three keys go HIGHEST first, but the name goes
    # A to Z. (Lesson 4: how do you flip the direction of a number?)
    # The name part must use normalize_name(row["name"]), so "Red" and "green"
    # compare fairly regardless of capitals.
    pass


# ---------------------------------------------------------------
# 5. is_league_complete   (about 3 lines)
# ---------------------------------------------------------------
def is_league_complete(fixtures):
    """True only if there is at least one fixture and every one is played."""
    # Careful: all([]) is True in Python. An empty schedule is NOT complete.
    pass


# ---------------------------------------------------------------
# 6. get_champion   (about 5 lines)
# ---------------------------------------------------------------
def get_champion(teams, fixtures):
    """Return the top row if the league is complete, else None."""
    # Not complete -> None. Otherwise rank the standings and return the first.
    pass


# ---------------------------------------------------------------
# Quick self-check. Run: python -m tournament.standings
# Delete this block when you move to tests/test_standings.py.
# ---------------------------------------------------------------
def _fx(fid, home, away, hs=None, aws=None):
    played = hs is not None
    return {"id": fid, "home_id": home, "away_id": away,
            "status": "played" if played else "pending",
            "home_score": hs, "away_score": aws}


def _summary(row):
    return (row["name"], row["played"], row["wins"], row["draws"], row["losses"],
            row["goals_for"], row["goals_against"], row["goal_diff"], row["points"])


if __name__ == "__main__":
    # Your Phase 0 paper example.
    teams = [{"id": "TM001", "name": "Red"},
             {"id": "TM002", "name": "Blue"},
             {"id": "TM003", "name": "Green"}]
    fixtures = [_fx("M001", "TM001", "TM002", 2, 0),    # Red 2-0 Blue
                _fx("M002", "TM001", "TM003", 0, 1),    # Red 0-1 Green
                _fx("M003", "TM002", "TM003", 1, 1)]    # Blue 1-1 Green

    table = rank_standings(compute_standings(teams, fixtures))
    print("name, P, W, D, L, GF, GA, GD, Pts")
    for row in table:
        print(_summary(row))
    print("-> want Green 2,1,1,0,2,1,1,4 / Red 2,1,0,1,2,1,1,3 / Blue 2,0,1,1,1,3,-2,1")

    print("2. points total:", sum(r["points"] for r in table), "-> want 8")
    print("3. GF == GA:", sum(r["goals_for"] for r in table)
          == sum(r["goals_against"] for r in table), "-> want True")

    more = fixtures + [_fx("M004", "TM001", "TM003")]            # a pending one
    same = rank_standings(compute_standings(teams, more))
    print("4. pending ignored:", [_summary(r) for r in same] == [_summary(r) for r in table],
          "-> want True")

    print("5. complete?", is_league_complete(fixtures), is_league_complete(more),
          is_league_complete([]), "-> want True False False")
    print("6. champion:", (get_champion(teams, fixtures) or {}).get("name"),
          get_champion(teams, more), "-> want Green None")

    # Tie-break order, with crafted rows.
    def row(name, pts, gd, gf):
        return {"team_id": name, "name": name, "points": pts,
                "goal_diff": gd, "goals_for": gf}
    crafted = [row("zed", 7, 2, 5), row("Alpha", 7, 2, 5),   # all equal -> name
               row("Low", 6, 9, 9),                           # fewer points
               row("MoreGD", 7, 3, 4),                        # same pts, better GD
               row("MoreGF", 7, 2, 6)]                        # same pts+GD, more GF
    order = [r["name"] for r in rank_standings(crafted)]
    print("7. order:", order)
    print("   -> want ['MoreGD', 'MoreGF', 'Alpha', 'zed', 'Low']")

    before = [dict(t) for t in teams]
    compute_standings(teams, fixtures)
    print("8. inputs unchanged:", teams == before, "-> want True")