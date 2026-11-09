import copy
import unittest

from tournament.fixtures import generate_fixtures
from tournament.results import record_result, validate_score


def make_fixtures():
    """Six pending fixtures for four teams (M001..M006)."""
    teams = [{"id": f"TM{n:03d}", "name": f"Team {n}"} for n in range(1, 5)]
    return generate_fixtures(teams)
BAD_SCORES = {
    "negative": -1,
    "float": 2.0,
    "bool": True,
    "text": "2",
    "none": None,
}
class TestValidateScore(unittest.TestCase):

    def test_valid_scores_returned(self):
        for good in (0, 1, 2, 10):
            with self.subTest(score=good):
                self.assertEqual(validate_score(good), good)

    def test_bad_scores_rejected(self):
        for name, bad in BAD_SCORES.items():
            with self.subTest(kind=name):
                with self.assertRaises(ValueError):
                    validate_score(bad)


class TestRecordResult(unittest.TestCase):

    def test_result_is_recorded(self):
        fixtures = make_fixtures()
        record_result(fixtures, "M001", 2, 1)
        first = fixtures[0]
        self.assertEqual(first["status"], "played")
        self.assertEqual(first["home_score"], 2)
        self.assertEqual(first["away_score"], 1)

    def test_goalless_draw_is_valid(self):
        fixtures = make_fixtures()
        record_result(fixtures, "M001", 0, 0)
        self.assertEqual(fixtures[0]["status"], "played")
        self.assertEqual((fixtures[0]["home_score"], fixtures[0]["away_score"]), (0, 0))

    def test_only_the_chosen_fixture_changes(self):
        fixtures = make_fixtures()
        before = copy.deepcopy(fixtures)
        record_result(fixtures, "M003", 1, 0)
        for index, (now, old) in enumerate(zip(fixtures, before)):
            with self.subTest(fixture=now["id"]):
                if index == 2:
                    self.assertNotEqual(now, old)
                else:
                    self.assertEqual(now, old)

    def test_second_submission_rejected_and_first_kept(self):
        fixtures = make_fixtures()
        record_result(fixtures, "M001", 2, 1)
        with self.assertRaises(ValueError):
            record_result(fixtures, "M001", 5, 5)
        self.assertEqual((fixtures[0]["home_score"], fixtures[0]["away_score"]), (2, 1))

    def test_unknown_fixture_rejected_and_nothing_changes(self):
        fixtures = make_fixtures()
        before = copy.deepcopy(fixtures)
        with self.assertRaises(ValueError):
            record_result(fixtures, "M999", 1, 0)
        self.assertEqual(fixtures, before)

    def test_bad_score_rejected_and_nothing_changes(self):
        for name, bad in BAD_SCORES.items():
            with self.subTest(bad_home=name):
                fixtures = make_fixtures()
                before = copy.deepcopy(fixtures)
                with self.assertRaises(ValueError):
                    record_result(fixtures, "M002", bad, 1)
                self.assertEqual(fixtures, before)
            with self.subTest(bad_away=name):
                fixtures = make_fixtures()
                before = copy.deepcopy(fixtures)
                with self.assertRaises(ValueError):
                    record_result(fixtures, "M002", 3, bad)
                # A valid home score must NOT be left behind (all or nothing).
                self.assertEqual(fixtures, before)


if __name__ == "__main__":
    unittest.main()