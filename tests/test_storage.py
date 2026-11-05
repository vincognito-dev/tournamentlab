import copy
import json
import tempfile
import unittest
from pathlib import Path

from tournament.fixtures import generate_fixtures
from tournament.storage import SCHEMA_VERSION, load_league, save_league, validate_league
from tournament.teams import register_team


def build_league(count=4):
    teams = []
    for n in range(1, count + 1):
        register_team(teams, f"Team {n}")
    return {"schema_version": SCHEMA_VERSION, "teams": teams,
            "fixtures": generate_fixtures(teams)}

BAD_CASES = {
    "wrong schema version": lambda lg: lg.update(schema_version=2),
    "missing teams key": lambda lg: lg.pop("teams"),
    "teams not a list": lambda lg: lg.update(teams="Red"),
    "duplicate team id": lambda lg: lg["teams"][1].update(id="TM001"),
    "duplicate team name": lambda lg: lg["teams"][1].update(name=" team 1 "),
    "phantom team": lambda lg: lg["fixtures"][0].update(away_id="TM009"),
    "team plays itself": lambda lg: lg["fixtures"][0].update(
        away_id=lg["fixtures"][0]["home_id"]),
    "reversed pair": lambda lg: lg["fixtures"][1].update(
        home_id=lg["fixtures"][0]["away_id"], away_id=lg["fixtures"][0]["home_id"]),
    "unknown status": lambda lg: lg["fixtures"][0].update(status="done"),
    "pending with a score": lambda lg: lg["fixtures"][0].update(home_score=1),
    "played with a missing score": lambda lg: lg["fixtures"][0].update(
        status="played", home_score=2),
    "played with a bool score": lambda lg: lg["fixtures"][0].update(
        status="played", home_score=True, away_score=1),
    "played with a negative score": lambda lg: lg["fixtures"][0].update(
        status="played", home_score=-1, away_score=0),
    "too few fixtures": lambda lg: lg["fixtures"].pop(),
}


class TestValidate(unittest.TestCase):

    def test_good_league_passes(self):
        league = build_league(4)
        league["fixtures"][0].update(status="played", home_score=2, away_score=2)
        validate_league(league)

    def test_league_without_schedule_passes(self):
        league = build_league(4)
        league["teams"] = league["teams"][:2]
        league["fixtures"] = []
        validate_league(league)

    def test_file_that_is_not_an_object_rejected(self):
        with self.assertRaises(ValueError):
            validate_league([])

    def test_each_bad_case_rejected(self):
        for name, change in BAD_CASES.items():
            with self.subTest(case=name):
                league = build_league(4)
                change(league)
                with self.assertRaises(ValueError):
                    validate_league(league)


class TestSaveAndLoad(unittest.TestCase):

    def test_round_trip_keeps_ids_and_results(self):
        league = build_league(4)
        league["fixtures"][0].update(status="played", home_score=2, away_score=0)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "season.json"
            save_league(league, path)
            loaded = load_league(path)
        self.assertEqual(loaded["teams"], league["teams"])
        self.assertEqual(loaded["fixtures"], league["fixtures"])

    def test_missing_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                load_league(Path(folder) / "nope.json")

    def test_broken_json_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "broken.json"
            path.write_text('{"teams": [', encoding="utf-8")
            with self.assertRaises(ValueError):
                load_league(path)

    def test_failed_load_leaves_current_league_unchanged(self):
        current = build_league(4)
        before = copy.deepcopy(current)
        bad = build_league(4)
        bad["fixtures"][0]["away_id"] = "TM009"      # valid JSON, invalid league
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.json"
            path.write_text(json.dumps(bad), encoding="utf-8")
            league = current
            try:
                league = load_league(path)
            except ValueError:
                pass
        self.assertIs(league, current)
        self.assertEqual(current, before)


if __name__ == "__main__":
    unittest.main()