from tournament.teams import normalize_name

POINTS_WIN = 3
POINTS_DRAW = 1
POINTS_LOSS = 0

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
            continue                                  
        home = rows[fixture["home_id"]]
        away = rows[fixture["away_id"]]
        home_goals = fixture["home_score"]
        away_goals = fixture["away_score"]
        add_result(home, home_goals, away_goals)      
        add_result(away, away_goals, home_goals)

    for row in rows.values():
        row["goal_diff"] = row["goals_for"] - row["goals_against"]

    return list(rows.values())                       

def rank_standings(rows):
    return sorted(
        rows,
        key=lambda row: (
            -row["points"],
            -row["goal_diff"],
            -row["goals_for"],
            normalize_name(row["name"]),
        ),
    )

def is_league_complete(fixtures):
    return len(fixtures) > 0 and all(f["status"] == "played" for f in fixtures)

def get_champion(teams, fixtures):
    """Return the top row if the league is complete, else None."""
    if not is_league_complete(fixtures):
        return None
    return rank_standings(compute_standings(teams, fixtures))[0]