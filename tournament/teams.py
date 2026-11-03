MIN_NAME_LENGTH = 2
MAX_NAME_LENGTH = 30
MAX_TEAMS = 8

def normalize_name(name):
    return name.strip().casefold()

def validate_team_name(name, existing_teams):
    if not isinstance(name, str):
        raise ValueError("Team name must be text.")
    clean = name.strip()
    if len(clean) < 2 or len(clean) > 30:
        raise ValueError("Team name must be 2-30 characters.")
    for team in existing_teams:
        if normalize_name(clean) == normalize_name(team["name"]):
            raise ValueError("A team with that name already exists.")
    return clean

def next_team_id(teams):
    number = len(teams) + 1
    return f"TM{number:03d}"

def register_team(teams, name):
    if len(teams) >= MAX_TEAMS:
        raise ValueError("A league can have at most 8 teams.")
    clean = validate_team_name(name, teams)
    team = {"id": next_team_id(teams), "name": clean}
    teams.append(team)
    return team

def list_teams(teams):
    return list(teams)
