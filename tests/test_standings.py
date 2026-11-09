import copy
import unittest
 
from tournament.fixtures import generate_fixtures
from tournament.results import record_result
from tournament.standings import (
    compute_standings,
    get_champion,
    is_league_complete,
    rank_standings,
)
 
 
def make_teams(count=4):
    return [{"id": f"TM{n:03d}", "name": f"Team {n}"} for n in range(1, count + 1)]
 
 
def fx(fid, home, away, home_score=None, away_score=None):
    played = home_score is not None
    return {"id": fid, "home_id": home, "away_id": away,
            "status": "played" if played else "pending",
            "home_score": home_score, "away_score": away_score}
 
 
def by_name(rows):
    return {row["name"]: row for row in rows}
 
 
def sort_row(name, points, goal_diff, goals_for):
    """A minimal row, just the fields the ranking uses."""
    return {"team_id": name, "name": name, "points": points,
            "goal_diff": goal_diff, "goals_for": goals_for}
 
 
class TestPoints(unittest.TestCase):
 
    def test_win_gives_three_loss_gives_zero(self):
        rows = by_name(compute_standings(make_teams(2), [fx("M001", "TM001", "TM002", 3, 1)]))
        self.assertEqual((rows["Team 1"]["wins"], rows["Team 1"]["points"]), (1, 3))
        self.assertEqual((rows["Team 2"]["losses"], rows["Team 2"]["points"]), (1, 0))
 
    def test_draw_gives_one_each_even_goalless(self):
        rows = by_name(compute_standings(make_teams(2), [fx("M001", "TM001", "TM002", 0, 0)]))
        for name in ("Team 1", "Team 2"):
            self.assertEqual((rows[name]["draws"], rows[name]["points"]), (1, 1))
 
    def test_losing_team_still_keeps_its_goals(self):
        rows = by_name(compute_standings(make_teams(2), [fx("M001", "TM001", "TM002", 3, 2)]))
        loser = rows["Team 2"]
        self.assertEqual((loser["goals_for"], loser["goals_against"], loser["goal_diff"]),
                         (2, 3, -1))
 
 
class TestComputeStandings(unittest.TestCase):
 
    def test_phase_zero_paper_table(self):
        teams = [{"id": "TM001", "name": "Red"},
                 {"id": "TM002", "name": "Blue"},
                 {"id": "TM003", "name": "Green"}]
        fixtures = [fx("M001", "TM001", "TM002", 2, 0),
                    fx("M002", "TM001", "TM003", 0, 1),
                    fx("M003", "TM002", "TM003", 1, 1)]
        table = rank_standings(compute_standings(teams, fixtures))
        summary = [(r["name"], r["played"], r["wins"], r["draws"], r["losses"],
                    r["goals_for"], r["goals_against"], r["goal_diff"], r["points"])
                   for r in table]
        self.assertEqual(summary, [
            ("Green", 2, 1, 1, 0, 2, 1, 1, 4),
            ("Red", 2, 1, 0, 1, 2, 1, 1, 3),
            ("Blue", 2, 0, 1, 1, 1, 3, -2, 1),
        ])
 
    def test_pending_fixtures_are_ignored(self):
        rows = compute_standings(make_teams(4), generate_fixtures(make_teams(4)))
        for row in rows:
            self.assertEqual(row["played"], 0)
            self.assertEqual(row["points"], 0)
 
    def test_every_team_appears_even_with_no_games(self):
        rows = compute_standings(make_teams(4), [])
        self.assertEqual([r["name"] for r in rows], ["Team 1", "Team 2", "Team 3", "Team 4"])
 
    def test_league_invariants_hold(self):
        teams = make_teams(4)
        fixtures = generate_fixtures(teams)
        scores = [(2, 1), (0, 0), (1, 3), (2, 2), (0, 1), (4, 0)]
        for fixture, (home, away) in zip(fixtures, scores):
            record_result(fixtures, fixture["id"], home, away)
        rows = compute_standings(teams, fixtures)
 
        draws = sum(1 for h, a in scores if h == a)
        non_draws = len(scores) - draws
        self.assertEqual(sum(r["points"] for r in rows), 3 * non_draws + 2 * draws)
        self.assertEqual(sum(r["goals_for"] for r in rows),
                         sum(r["goals_against"] for r in rows))
        for row in rows:
            self.assertEqual(row["wins"] + row["draws"] + row["losses"], row["played"])
            self.assertEqual(row["goal_diff"], row["goals_for"] - row["goals_against"])
 
    def test_table_is_recomputed_from_the_matches(self):
        teams = make_teams(4)
        fixtures = generate_fixtures(teams)
        before = by_name(compute_standings(teams, fixtures))
        self.assertEqual(before["Team 1"]["points"], 0)
        record_result(fixtures, "M001", 1, 0)
        after = by_name(compute_standings(teams, fixtures))
        self.assertEqual(after["Team 1"]["points"], 3)
        self.assertEqual(compute_standings(teams, fixtures),
                         compute_standings(teams, fixtures))
 
    def test_inputs_are_not_changed(self):
        teams = make_teams(4)
        fixtures = generate_fixtures(teams)
        record_result(fixtures, "M001", 2, 0)
        teams_before = copy.deepcopy(teams)
        fixtures_before = copy.deepcopy(fixtures)
        compute_standings(teams, fixtures)
        self.assertEqual(teams, teams_before)
        self.assertEqual(fixtures, fixtures_before)
 
 
class TestRanking(unittest.TestCase):
 
    def test_each_tie_break_level(self):
        cases = {
            "points decide": ([sort_row("A", 3, 9, 9), sort_row("B", 4, 0, 0)], ["B", "A"]),
            "goal difference decides": ([sort_row("A", 4, 1, 9), sort_row("B", 4, 2, 0)], ["B", "A"]),
            "goals for decide": ([sort_row("A", 4, 2, 3), sort_row("B", 4, 2, 5)], ["B", "A"]),
            "name decides": ([sort_row("B", 4, 2, 5), sort_row("A", 4, 2, 5)], ["A", "B"]),
        }
        for label, (rows, expected) in cases.items():
            with self.subTest(rule=label):
                self.assertEqual([r["name"] for r in rank_standings(rows)], expected)
 
    def test_name_tie_break_ignores_case_and_spaces(self):
        rows = [sort_row("Red", 4, 2, 5), sort_row(" green", 4, 2, 5)]
        self.assertEqual([r["name"] for r in rank_standings(rows)], [" green", "Red"])
 
    def test_full_crafted_order(self):
        rows = [sort_row("zed", 7, 2, 5), sort_row("Alpha", 7, 2, 5),
                sort_row("Low", 6, 9, 9), sort_row("MoreGD", 7, 3, 4),
                sort_row("MoreGF", 7, 2, 6)]
        self.assertEqual([r["name"] for r in rank_standings(rows)],
                         ["MoreGD", "MoreGF", "Alpha", "zed", "Low"])
 
    def test_ranking_returns_a_new_list(self):
        rows = [sort_row("B", 1, 0, 0), sort_row("A", 3, 0, 0)]
        original = list(rows)
        ranked = rank_standings(rows)
        self.assertEqual(rows, original)
        self.assertIsNot(ranked, rows)
 
 
class TestChampion(unittest.TestCase):
 
    def test_empty_schedule_is_not_complete(self):
        self.assertFalse(is_league_complete([]))
 
    def test_partly_played_is_not_complete_and_has_no_champion(self):
        teams = make_teams(4)
        fixtures = generate_fixtures(teams)
        record_result(fixtures, "M001", 1, 0)
        self.assertFalse(is_league_complete(fixtures))
        self.assertIsNone(get_champion(teams, fixtures))
 
    def test_champion_appears_only_when_everything_is_played(self):
        teams = make_teams(4)
        fixtures = generate_fixtures(teams)
        # Team 1 wins its three games; every other game is a goalless draw.
        for fixture in fixtures:
            home_wins = fixture["home_id"] == "TM001"
            record_result(fixtures, fixture["id"], 1 if home_wins else 0, 0)
        self.assertTrue(is_league_complete(fixtures))
        self.assertEqual(get_champion(teams, fixtures)["name"], "Team 1")
 
 
if __name__ == "__main__":
    unittest.main()
