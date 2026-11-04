import unittest

from tournament.teams import(
    list_teams,
    next_team_id,
    normalize_name,
    register_team,
    validate_team_name,
)


def make_league(count):
    """Helper: register `count` teams named Team 1, Team 2, ... and return the list."""
    teams = []
    for n in range(1, count + 1):
        register_team(teams, f"Team {n}")
    return teams


class TestNormalizeName(unittest.TestCase):

    def test_trims_and_casefolds(self):
        cases = [
            ("Red Comets", "red comets"),
            (" red comets ", "red comets"),
            ("RED COMETS", "red comets"),
            ("  GREEN hawks", "green hawks"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(normalize_name(raw), expected)


class TestValidateTeamName(unittest.TestCase):

    def test_not_text_rejected(self):
        for bad in (123, None, ["Red"]):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    validate_team_name(bad, [])

    def test_duplicate_casefolded_name_rejected(self):
        existing = [{"id": "TM001", "name": "Red Comets"}]
        for duplicate in (" red comets ", "RED COMETS", "Red Comets"):
            with self.subTest(name=duplicate):
                with self.assertRaises(ValueError):
                    validate_team_name(duplicate, existing)

    def test_blank_name_rejected(self):
        for blank in ("", "   "):
            with self.subTest(name=blank):
                with self.assertRaises(ValueError):
                    validate_team_name(blank, [])

    def test_too_short_name_rejected(self):
        # Length is checked AFTER trimming, so "  A  " is still too short.
        for short in ("A", "  A  "):
            with self.subTest(name=short):
                with self.assertRaises(ValueError):
                    validate_team_name(short, [])

    def test_length_limits_are_exact(self):
        # Both sides of each limit, to catch off-by-one bugs.
        self.assertEqual(validate_team_name("ab", []), "ab")
        self.assertEqual(validate_team_name("x" * 30, []), "x" * 30)
        with self.assertRaises(ValueError):
            validate_team_name("x" * 31, [])

    def test_returns_trimmed_display_name(self):
        # Spaces are removed but capitals are kept.
        self.assertEqual(validate_team_name("  Red Comets  ", []), "Red Comets")

    def test_different_name_accepted(self):
        existing = [{"id": "TM001", "name": "Red Comets"}]
        self.assertEqual(validate_team_name("Blue Wolves", existing), "Blue Wolves")

    def test_validation_does_not_change_existing_teams(self):
        existing = [{"id": "TM001", "name": "Red Comets"}]
        before = [dict(team) for team in existing]
        validate_team_name("Blue Wolves", existing)
        self.assertEqual(existing, before)


class TestRegisterTeam(unittest.TestCase):

    def test_first_team_gets_tm001(self):
        teams = []
        team = register_team(teams, "Red Comets")
        self.assertEqual(team, {"id": "TM001", "name": "Red Comets"})
        self.assertEqual(teams, [team])

    def test_name_is_stored_trimmed(self):
        teams = []
        team = register_team(teams, "  Red Comets  ")
        self.assertEqual(team["name"], "Red Comets")

    def test_ids_run_in_order(self):
        teams = make_league(4)
        self.assertEqual(
            [team["id"] for team in teams],
            ["TM001", "TM002", "TM003", "TM004"],
        )

    def test_eighth_team_accepted_ninth_rejected(self):
        teams = make_league(8)
        self.assertEqual(len(teams), 8)
        with self.assertRaises(ValueError):
            register_team(teams, "Ninth")
        self.assertEqual(len(teams), 8)

    def test_rejected_registration_changes_nothing(self):
        teams = make_league(4)
        before = [dict(team) for team in teams]
        for bad in ("team 1", "A", 123):
            with self.subTest(name=bad):
                with self.assertRaises(ValueError):
                    register_team(teams, bad)
                self.assertEqual(teams, before)

    def test_rejected_duplicate_does_not_use_up_an_id(self):
        teams = []
        register_team(teams, "Red")
        with self.assertRaises(ValueError):
            register_team(teams, " red ")
        blue = register_team(teams, "Blue")
        self.assertEqual(blue["id"], "TM002")


class TestNextTeamId(unittest.TestCase):

    def test_id_format(self):
        self.assertEqual(next_team_id([]), "TM001")
        self.assertEqual(next_team_id(make_league(7)), "TM008")


class TestListTeams(unittest.TestCase):

    def test_registration_order_kept(self):
        teams = make_league(3)
        names = [team["name"] for team in list_teams(teams)]
        self.assertEqual(names, ["Team 1", "Team 2", "Team 3"])

    def test_empty_league_gives_empty_list(self):
        self.assertEqual(list_teams([]), [])


if __name__ == "__main__":
    unittest.main()