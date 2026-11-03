MIN_TEAMS = 4
MAX_TEAMS = 8

def expected_fixture_count(team_count):
    return team_count * (team_count - 1) // 2

def make_fixture_id(number):
    return f"M{number:03d}"

def generate_fixtures(teams):
    if len(teams) < 4 or len(teams) > 8:
        raise ValueError("A league needs 4 to 8 teams.")

    fixtures = []
    for i in range(len(teams)):
        for j in range(i + 1, len(teams)):
            fixture = {
                "id": make_fixture_id(len(fixtures) + 1),
                "home_id": teams[i]["id"],
                "away_id": teams[j]["id"],
                "status": "pending",
                "home_score": None,
                "away_score": None,
            }
            fixtures.append(fixture)
    return fixtures

def find_fixture(fixtures, fixture_id):
    for fixture in fixtures:
        if fixture["id"] == fixture_id:
            return fixture
    raise ValueError("Unknown fixture ID.")

def list_fixtures(teams, fixtures):
    names = {}
    for team in teams:
        names[team["id"]] = team["name"]
    rows = []
    for fixture in fixtures:
        rows.append({
            "id": fixture["id"],
            "home": names[fixture["home_id"]],
            "away": names[fixture["away_id"]],
            "status": fixture["status"],
        })
    return rows