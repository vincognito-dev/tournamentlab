import copy
import random
 
from tournament.fixtures import generate_fixtures, list_fixtures
from tournament.results import record_result
from tournament.standings import (
    compute_standings,
    get_champion,
    is_league_complete,
    rank_standings,
)
from tournament.storage import SCHEMA_VERSION, load_league, save_league
from tournament.teams import list_teams, register_team
 
DEFAULT_FILE = "season.json"
 
MENU = """
=== TournamentLab ===
 1. Register a team
 2. List teams
 3. Generate schedule
 4. List fixtures
 5. Record a result
 6. Show standings
 7. Save league
 8. Load league
 9. Show champion
10. Simulate demo results (does not change your records)
 0. Quit"""
 
def new_league():
    return {"schema_version": SCHEMA_VERSION, "teams": [], "fixtures": []}
 
def ask(prompt):
    return input(prompt).strip()

def print_table(rows, title):
    print(f"\n{title}")
    print(f"{'Pos':<4}{'Team':<22}{'P':>3}{'W':>3}{'D':>3}{'L':>3}"
          f"{'GF':>4}{'GA':>4}{'GD':>5}{'Pts':>5}")
    for position, row in enumerate(rows, start=1):
        print(f"{position:<4}{row['name']:<22}{row['played']:>3}{row['wins']:>3}"
              f"{row['draws']:>3}{row['losses']:>3}{row['goals_for']:>4}"
              f"{row['goals_against']:>4}{row['goal_diff']:>+5}{row['points']:>5}")
 
def print_champion(league):
    champion = get_champion(league["teams"], league["fixtures"])
    if champion is not None:
        print(f"Champion: {champion['name']} with {champion['points']} points!")
        return
    if not league["fixtures"]:
        print("No schedule yet, so there is no champion.")
        return
    pending = sum(1 for f in league["fixtures"] if f["status"] != "played")
    print(f"No champion yet: {pending} fixture(s) still to play.")

def menu_register_team(league):
    if league["fixtures"]:
        print("The schedule already exists, so no more teams can join this season.")
        return
    name = ask("Team name: ")
    try:
        team = register_team(league["teams"], name)
    except ValueError as err:
        print(f"Error: {err}")
        return
    print(f"Registered {team['name']} as {team['id']}.")
 
def menu_list_teams(league):
    teams = list_teams(league["teams"])
    if not teams:
        print("No teams yet.")
        return
    for team in teams:
        print(f"  {team['id']}  {team['name']}")
 
def menu_generate_schedule(league):
    if league["fixtures"]:
        print("The schedule has already been generated for this season.")
        return
    try:
        fixtures = generate_fixtures(league["teams"])
    except ValueError as err:
        print(f"Error: {err}")
        return
    league["fixtures"] = fixtures          # change state only after success
    print(f"Created {len(fixtures)} fixtures.")

def menu_list_fixtures(league):
    if not league["fixtures"]:
        print("No schedule yet. Generate it first.")
        return
    rows = list_fixtures(league["teams"], league["fixtures"])
    for row, fixture in zip(rows, league["fixtures"]):
        if fixture["status"] == "played":
            result = f"{fixture['home_score']}-{fixture['away_score']}"
        else:
            result = "pending"
        print(f"  {row['id']}  {row['home']} vs {row['away']}  [{result}]")

def menu_record_result(league):
    if not league["fixtures"]:
        print("No schedule yet. Generate it first.")
        return
    fixture_id = ask("Fixture ID (for example M001): ").upper()
    home_text = ask("Home score: ")
    away_text = ask("Away score: ")
    try:
        home_score = int(home_text)
        away_score = int(away_text)
    except ValueError:
        print("Error: scores must be whole numbers.")
        return
    try:
        record_result(league["fixtures"], fixture_id, home_score, away_score)
    except ValueError as err:
        print(f"Error: {err}")
        return
    print(f"Recorded {fixture_id}: {home_score}-{away_score}.")
 
def menu_show_standings(league):
    rows = rank_standings(compute_standings(league["teams"], league["fixtures"]))
    if not rows:
        print("No teams yet.")
        return
    label = "FINAL" if is_league_complete(league["fixtures"]) else "in progress"
    print_table(rows, f"Standings ({label})")

def menu_save(league):
    path = ask(f"File name [{DEFAULT_FILE}]: ") or DEFAULT_FILE
    try:
        save_league(league, path)
    except OSError as err:
        print(f"Could not save: {err}")
        return
    print(f"Saved to {path}.")

def menu_load(league):
    path = ask(f"File name [{DEFAULT_FILE}]: ") or DEFAULT_FILE
    try:
        loaded = load_league(path)
    except ValueError as err:
        print(f"Could not load: {err}")
        print("Your current league is unchanged.")
        return league
    print(f"Loaded {len(loaded['teams'])} teams and {len(loaded['fixtures'])} fixtures.")
    return loaded
 
def menu_champion(league):
    print_champion(league)
 
def menu_simulate(league):
    if not league["fixtures"]:
        print("No schedule yet. Generate it first.")
        return
    print("This plays the pending fixtures with random scores on a COPY.")
    print("Your real records will not be changed.")
    if ask("Continue? (y/n): ").lower() != "y":
        print("Cancelled.")
        return
    seed_text = ask("Seed [42]: ") or "42"
    try:
        seed = int(seed_text)
    except ValueError:
        print("Error: the seed must be a whole number.")
        return
 
    rng = random.Random(seed)
    demo = copy.deepcopy(league)
    for fixture in demo["fixtures"]:
        if fixture["status"] == "pending":
            record_result(demo["fixtures"], fixture["id"],
                          rng.randint(0, 4), rng.randint(0, 4))
 
    rows = rank_standings(compute_standings(demo["teams"], demo["fixtures"]))
    print_table(rows, f"SIMULATED standings (seed {seed}) - not your real records")
    print_champion(demo)
 
ACTIONS = {
    "1": menu_register_team,
    "2": menu_list_teams,
    "3": menu_generate_schedule,
    "4": menu_list_fixtures,
    "5": menu_record_result,
    "6": menu_show_standings,
    "7": menu_save,
    "9": menu_champion,
    "10": menu_simulate,
}

def main():
    league = new_league()
    print("Welcome to TournamentLab!")
    while True:
        print(MENU)
        try:
            choice = ask("Choose an option: ")
            if choice == "0":
                print("Goodbye!")
                break
            if choice == "8":
                league = menu_load(league)
            elif choice in ACTIONS:
                ACTIONS[choice](league)
            else:
                print("Please type a number from the menu.")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
