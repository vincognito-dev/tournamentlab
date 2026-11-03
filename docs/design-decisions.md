# TournamentLab Design Decisions

Author: Okefu Enyitobi (solo)
Status: draft v1. Items marked **[DECIDE]** are mine to settle before coding.

## 1. Goals and non-goals
- Goal: a fair league manager (register teams, round-robin schedule, record results, derived standings, JSON save/load, champion report).
- Non-goals: no web, no external packages, no AI API, no score editing after a result is recorded.

## 2. Data shapes

Team
    {"id": "TM001", "name": "Red Comets"}

Fixture
    {"id": "M001", "home_id": "TM001", "away_id": "TM002",
     "status": "pending", "home_score": None, "away_score": None}

Played fixture: status = "played", both scores are ints >= 0.

League (the whole state passed between modules)
    {"schema_version": 1, "teams": [...], "fixtures": [...]}

Standings row (computed, never stored)
    {"team_id", "name", "played", "wins", "draws", "losses",
     "goals_for", "goals_against", "goal_diff", "points"}

Decision: names are display labels, IDs are stable identifiers. Fixtures reference IDs only, so renaming a team never breaks a fixture.

## 3. Rules
- Team name: 2-30 chars after trim; unique when casefolded.
- 4-8 teams before fixtures are generated.
- Fixtures are generated once per season, one per unordered pair; N*(N-1)/2 total.
- IDs: teams TM001..., fixtures M001..., assigned in generation order.
- Only a pending fixture accepts a score; scores are non-negative ints, bool rejected.
- Standings use played fixtures only.
- League is complete only when every fixture is played.
- Points: win 3, draw 1 each, loss 0.

## 4. Invariants (these become tests)
1. Every fixture references two distinct, existing teams.
2. Fixture IDs are unique; no duplicate unordered team pair.
3. Pending => both scores None. Played => both scores int >= 0, not bool.
4. Total points = 3 * (non-draw matches) + 2 * (draw matches).
5. Total goals for = total goals against.
6. For every standings row: wins + draws + losses = played.
7. A rejected operation changes nothing.

## 5. Functions (name, takes, returns, raises)

### tournament/teams.py
- normalize_name(name) -> str. Trim and casefold; used for comparisons only.
- validate_team_name(name, existing_teams) -> str. Returns the trimmed display name. Raises ValueError for wrong length or duplicate.
- register_team(teams, name) -> dict. Validates, builds the team with the next ID, appends it, returns it. Raises ValueError (including when already 8 teams or fixtures exist) **[DECIDE: block registering after fixtures exist? my default: yes]**.
- list_teams(teams) -> list of teams in registration order.

### tournament/fixtures.py
- generate_fixtures(teams) -> list of fixtures. Raises ValueError if fewer than 4 or more than 8 teams. Pure: does not touch the league.
- list_fixtures(fixtures) -> list of display-ready dicts or tuples with ID, team names, status. **[DECIDE: return data, let cli format it]**
- find_fixture(fixtures, fixture_id) -> fixture. Raises ValueError for unknown ID.

Generation guard (fixtures already exist) lives where the league is updated, not inside generate_fixtures. **[DECIDE: which function owns it]**

### tournament/results.py
- validate_score(value) -> int. Accepts only int that is not bool and >= 0. Raises ValueError. **[DECIDE: are numeric strings like "2" converted in cli before this, or rejected here? my default: cli converts, this function stays strict]**
- record_result(fixtures, fixture_id, home_score, away_score) -> None. Order: find fixture, check pending, validate both scores, then update both scores and status together. Raises ValueError for unknown, already played, or invalid score; changes nothing on any failure.

### tournament/standings.py
- compute_standings(teams, fixtures) -> list of standings rows (unsorted or sorted? **[DECIDE]**). Built fresh from played fixtures every call. No stored scoreboard.
- rank_standings(rows) -> rows sorted. Order documented in section 7.
- is_league_complete(fixtures) -> bool. True only if there is at least one fixture and all are played.
- get_champion(teams, fixtures) -> row or None. None unless the league is complete.

### tournament/storage.py
- save_league(league, path) -> None. Writes schema_version, teams, fixtures.
- load_league(path) -> league. Parses into a temporary structure, validates, and only then returns it. Raises ValueError for any problem.
- validate_league(data) -> None. Checks: required keys, schema_version == 1, team shapes and names, unique team IDs and names, fixture shapes, unique fixture IDs, referenced team IDs exist and differ, no duplicate unordered pair, status and score consistency.

### tournament/cli.py
- Menu loop only. The only module that calls input() and print().
- Converts text to ints, catches ValueError, prints messages, re-prompts on bad input.

## 6. Error handling
- Modules raise ValueError with a short message that says what was wrong and which value.
- cli catches ValueError and prints it; no traceback ever reaches the user.
- Messages needed: duplicate name, name length, too few teams, unknown fixture, fixture already played, invalid score, bad file data.
- load_league never leaves a half-loaded state: the caller's league is replaced only after a full successful load. **[DECIDE: what the CLI does with the old league on a failed load; my default: keep it unchanged]**

## 7. Tie-break order (documented, tested, no head-to-head)
1. Points, higher first
2. Goal difference, higher first
3. Goals for, higher first
4. Normalized team name, A to Z

How the single sort expresses "three descending, one ascending" is **[DECIDE]**: work it out in Lesson 4's mini-lab first.

## 8. Pure vs side effects
- Pure (return data, no printing, no files): normalize_name, validate_team_name, generate_fixtures, validate_score, compute_standings, rank_standings, is_league_complete, get_champion, validate_league.
- Mutates passed-in state, only after validation: register_team, record_result.
- File I/O: save_league, load_league.
- Screen and keyboard: cli.py only.

## 9. Demo simulation
- Only runs on an explicit menu choice.
- Uses a seeded random generator so results are reproducible.
- Works on a copy of the league; real records are never changed. **[DECIDE: does the user see simulated standings only, or can they save the copy as a separate file?]**

## 10. Test plan (maps to the brief's 16 scenarios)
- test_teams.py: duplicate casefolded name, blank/too-long name, limit of 8 teams.
- test_fixtures.py: fewer than 4 teams, 4 gives 6, 6 gives 15, no self-match, no duplicate pair.
- test_results.py: negative/float/bool score, unknown fixture, duplicate result, rejected score changes nothing.
- test_standings.py: 3/1/0 points, tie-break crafted records, recompute from matches, champion only when complete.
- test_storage.py: bad team reference rejected with no state change, reload preserves IDs and standings. Use tempfile.TemporaryDirectory.

## 11. Git plan
- feat/1-team-scheduling: teams, fixtures, storage and tests.
- feat/2-results-and-rankings: results, standings, cli and tests.
- Each branch: at least 2 commits, one PR, reviewed by mentor before merge.