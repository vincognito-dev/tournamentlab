from tournament.fixtures import find_fixture, generate_fixtures



def validate_score(value):
    if not (isinstance(value, int) and not isinstance(value, bool) and value >= 0):
        raise ValueError("Score must be a whole number, 0 or more.")
    return value

def record_result(fixtures, fixture_id, home_score, away_score):
    fixture = find_fixture(fixtures, fixture_id)
    if fixture["status"] != "pending":
        raise ValueError("That fixture has already been played.")
    home = validate_score(home_score)
    away = validate_score(away_score)

    fixture["home_score"] = home
    fixture["away_score"] = away
    fixture["status"] = "played"