import json
from pathlib import Path

from tournament.fixtures import expected_fixture_count, MAX_TEAMS, MIN_TEAMS
from tournament.teams import validate_team_name

SCHEMA_VERSION = 1
FIXTURE_KEYS = ("id", "home_id", "away_id", "status", "home_score", "away_score")

def save_league(league, path):
    data = {"schema_version": SCHEMA_VERSION, "teams": league["teams"], "fixtures": league["fixtures"]}
    with (Path(path).open("w", encoding="utf-8")) as file:
        json.dump(data, file, indent=2)

def _is_valid_score(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0
    
def validate_league(data):
    if not isinstance(data, dict):
        raise ValueError("League file must contain an object.")
    for key in ("schema_version", "teams", "fixtures"):
        if key not in data:
            raise ValueError(f"League file is missing '{key}'.")
    if data["schema_version"] != SCHEMA_VERSION:
        raise ValueError("Unsupported schema version.")

    teams = data["teams"]
    if not isinstance(teams, list):
        raise ValueError("'teams' must be a list.")

    accepted = []
    seen_ids = set()
    for team in teams:
        if not isinstance(team, dict):
            raise ValueError("Each team must be an object.")
        if "id" not in team or "name" not in team:
            raise ValueError("Each team needs an 'id' and a 'name'.")
        if not isinstance(team["id"], str):
            raise ValueError("Team id must be text.")
        if team["id"] in seen_ids:
            raise ValueError(f"Duplicate team id: {team['id']}")

        validate_team_name(team["name"], accepted)

        seen_ids.add(team["id"])
        accepted.append(team)
    team_ids = seen_ids
    fixtures = data["fixtures"]
    if not isinstance(fixtures, list):
        raise ValueError("'fixture' must be a list.")

    seen_fixture_ids = set()
    seen_pairs = set()
    for fixture in fixtures:
        if not isinstance(fixture, dict):
            raise ValueError("Each fixture must be an object.")
        for key in FIXTURE_KEYS:
            if key not in fixture:
                raise ValueError(f"fixture is missing '{key}'.")
        if not isinstance(fixture["id"], str):
            raise ValueError("fixture id must be a text.")
        if fixture["id"] in seen_fixture_ids:
            raise ValueError(f"Duplicate fixture id: {fixture['id']}")
        seen_fixture_ids.add(fixture["id"])
        home = fixture["home_id"]
        away = fixture["away_id"]
        if not isinstance(home, str) or not isinstance(away, str):
            raise ValueError(f"Fixture {fixture['id']} team ids must be text.")
        if home not in team_ids or away not in team_ids:
            raise ValueError(f"Fixture {fixture['id']} refers to an unknown team.")
        if home == away:
            raise ValueError(f"Fixture {fixture['id']} has a team playing itself.")

        pair = frozenset((home, away))
        if pair in seen_pairs:
            raise ValueError(f"Fixture {fixture['id']} repeats an existing pairing.")
        seen_pairs.add(pair)
        
        status = fixture["status"]
        home_score = fixture["home_score"]
        away_score = fixture["away_score"]
        if status == "pending":
            if home_score is not None or away_score is not None:
                raise ValueError(f"Pending fixture {fixture['id']} must have no scores.")
        elif status == "played":
            if not (_is_valid_score(home_score) and _is_valid_score(away_score)):
                raise ValueError(f"Played fixture {fixture['id']} needs two valid scores.")
        else:
            raise ValueError(f"Fixture {fixture['id']} has an unknown status.")
    if len(teams) > MAX_TEAMS:
        raise ValueError("A league can have at most 8 teams.")
    if fixtures:
        if len(teams) < MIN_TEAMS:
            raise ValueError("A schedule needs at least 4 teams.")
        if len(fixtures) != expected_fixture_count(len(teams)):
            raise ValueError("Fixture count does not match the number of teams.")
def load_league(path):
    try:
        with Path(path).open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as err:
        raise ValueError(f"League file not found: {path}") from err
    except json.JSONDecodeError as err:
        raise ValueError("League file is not valid JSON.") from err
    except OSError as err:
        raise ValueError(f"League file could not be read: {path}") from err

    validate_league(data)

    return {
        "schema_version": data["schema_version"],
        "teams": data["teams"],
        "fixtures": data["fixtures"],
    }