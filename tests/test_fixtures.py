import unittest

from tournament.fixtures import (
    expected_fixture_count,
    find_fixture,
    generate_fixtures,
    list_fixtures,
    make_fixture_id,
)


def make_teams(count):
    """Helper: build `count` teams like TM001 'Team 1', TM002 'Team 2', ..."""
    return [{"id": f"TM{n:03d}", "name": f"Team {n}"} for n in range(1, count + 1)]


class TestGenerateFixtures(unittest.TestCase):

    def test_four_teams_make_six_fixtures(self):
        fixtures = generate_fixtures(make_teams(4))
        self.assertEqual(len(fixtures), 6)

    def test_six_teams_make_fifteen_fixtures(self):
        fixtures = generate_fixtures(make_teams(6))
        self.assertEqual(len(fixtures), 15)

    def test_no_team_plays_itself(self):
        for n in range(4, 9):
            with self.subTest(teams=n):
                for fixture in generate_fixtures(make_teams(n)):
                    self.assertNotEqual(fixture["home_id"], fixture["away_id"])

    def test_no_duplicate_unordered_pair(self):
        for n in range(4, 9):
            with self.subTest(teams=n):
                fixtures = generate_fixtures(make_teams(n))
                pairs = {frozenset((f["home_id"], f["away_id"])) for f in fixtures}
                # A reversed duplicate collapses into the same frozenset,
                # so the set would be smaller than the fixture list.
                self.assertEqual(len(pairs), len(fixtures))

    def test_fewer_than_four_teams_rejected(self):
        with self.assertRaises(ValueError):
            generate_fixtures(make_teams(3))

    def test_more_than_eight_teams_rejected(self):
        with self.assertRaises(ValueError):
            generate_fixtures(make_teams(9))

    def test_ids_are_deterministic_and_in_order(self):
        teams = make_teams(4)
        first = generate_fixtures(teams)
        second = generate_fixtures(teams)
        self.assertEqual(
            [f["id"] for f in first],
            ["M001", "M002", "M003", "M004", "M005", "M006"],
        )
        self.assertEqual(first, second)

    def test_new_fixtures_are_pending_with_no_scores(self):
        for fixture in generate_fixtures(make_teams(4)):
            self.assertEqual(fixture["status"], "pending")
            self.assertIsNone(fixture["home_score"])
            self.assertIsNone(fixture["away_score"])

    def test_generate_does_not_change_teams(self):
        teams = make_teams(4)
        before = list(teams)
        generate_fixtures(teams)
        self.assertEqual(teams, before)

    def test_count_matches_formula(self):
        for n in range(4, 9):
            with self.subTest(teams=n):
                self.assertEqual(
                    len(generate_fixtures(make_teams(n))),
                    expected_fixture_count(n),
                )


class TestHelpers(unittest.TestCase):

    def test_make_fixture_id_pads_with_zeros(self):
        self.assertEqual(make_fixture_id(7), "M007")

    def test_find_fixture_returns_match(self):
        fixtures = generate_fixtures(make_teams(4))
        self.assertEqual(find_fixture(fixtures, "M003")["id"], "M003")

    def test_find_fixture_unknown_id_raises(self):
        fixtures = generate_fixtures(make_teams(4))
        with self.assertRaises(ValueError):
            find_fixture(fixtures, "M999")

    def test_list_fixtures_uses_team_names(self):
        teams = make_teams(4)
        rows = list_fixtures(teams, generate_fixtures(teams))
        self.assertEqual(
            rows[0],
            {"id": "M001", "home": "Team 1", "away": "Team 2", "status": "pending"},
        )


if __name__ == "__main__":
    unittest.main()