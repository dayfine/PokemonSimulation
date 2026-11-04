"""Validate FireRed/LeafGreen (Gen 3) solo-battle experiment inputs."""

from pokesim.games.frlg.battle.npc_ai import move_id
from pokesim.games.frlg.progression.experience import level_at

STATS = {"hp", "atk", "def", "spa", "spd", "spe"}
STAGES = {"atk", "def", "spa", "spd", "spe", "accuracy", "evasion"}
ITEMS = {"potion", "superpotion", "hyperpotion", "maxpotion", "fullrestore",
         "awakening", "antidote", "parlyzheal", "burnheal", "iceheal", "fullheal"}
ITEMS |= {"xattack", "xdefend", "xspecial", "xspeed", "xaccuracy", "direhit", "guardspec",
          "ether", "maxether", "elixir", "maxelixir", "oranberry"}
BADGES = {"boulder", "cascade", "thunder", "rainbow", "soul", "marsh", "volcano", "earth"}


def integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("{} must be an integer from {} to {}".format(name, low, high))


def validate_cases(cases, pret):
    """Reject unsupported inputs instead of reporting a misleading estimate."""
    if pret.get("format") != "pokesim-frlg-pret/1":
        raise ValueError("Unsupported pret snapshot format")
    if not cases:
        raise ValueError("At least one case is required")
    ids = [c.get("id") for c in cases]
    if any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
        raise ValueError("Cases must have unique nonempty IDs")
    move_data = {move_id(k): v for k, v in pret["moves"].items()}
    for case in cases:
        if type(case.get('enable_complex_planning', False)) is not bool:
            raise ValueError('enable_complex_planning must be a boolean')
        goals = case.get('planning_goals', {})
        if not isinstance(goals, dict) or set(goals) - {'spa', 'accuracy', 'outspeed', 'guard_accuracy', 'target_torrent', 'torrent_power'}:
            raise ValueError('Unknown planning goal')
        if goals and not case.get('enable_complex_planning', False):
            raise ValueError('Planning goals require explicit complex-planning opt-in')
        for key in ('spa', 'accuracy'):
            if key in goals:
                integer(goals[key], 0, 6, key + ' setup goal')
        for key in ('outspeed', 'guard_accuracy', 'target_torrent', 'torrent_power'):
            if key in goals and type(goals[key]) is not bool:
                raise ValueError(key + ' must be a boolean')
        if case.get("trainer") not in pret["trainers"]:
            raise ValueError("Trainer outside imported snapshot: " + str(case.get("trainer")))
        player = case["player"]
        if move_id(player["species"]) not in ("squirtle", "wartortle", "blastoise"):
            raise ValueError("First milestone supports the Squirtle line as the solo lead")
        integer(player["level"], 1, 100, "level")
        if set(player["stats"]) != STATS:
            raise ValueError("Player must specify all six summary stats")
        for stat, value in player["stats"].items():
            integer(value, 1, 999, stat)
        integer(player.get("hp", player["stats"]["hp"]), 1, player["stats"]["hp"], "current HP")
        if player.get("status", "") not in ("", "slp", "psn", "tox", "par", "brn", "frz"):
            raise ValueError("Unsupported initial status")
        if "sleep_turns" in player:
            integer(player["sleep_turns"], 1, 5, "sleep counter")
        boosts = player.get("boosts", {})
        if not isinstance(boosts, dict) or set(boosts) - STAGES:
            raise ValueError("Initial boosts must use the seven supported stat stages")
        for stat, stage in boosts.items():
            integer(stage, -6, 6, stat + " stage")
        moves = player["moves"]
        if not 1 <= len(moves) <= 4:
            raise ValueError("Player must have one to four moves")
        names = [move_id(m if isinstance(m, str) else m["name"]) for m in moves]
        if len(set(names)) != len(names):
            raise ValueError("Player moves must be unique")
        for move, name in zip(moves, names):
            if name not in move_data:
                raise ValueError("Move outside milestone snapshot: " + name)
            if isinstance(move, dict):
                integer(move["pp"], 0, move_data[name]["pp"], "PP")
        for item, count in case.get("bag", {}).items():
            if move_id(item) not in ITEMS:
                raise ValueError("Unsupported bag item " + item)
            integer(count, 0, 999, "item count")
        badges = case.get("badges", [])
        if len(set(badges)) != len(badges) or set(badges) - BADGES:
            raise ValueError("Badges must be unique FRLG badge names")
        if 'progression' in case:
            data = case['progression']
            integer(data['exp'], 0, 2 ** 32 - 1, 'total EXP')
            thresholds = data['thresholds']
            if len(thresholds) != 101 or any(type(n) is not int for n in thresholds) or any(
                    a >= b for a, b in zip(thresholds, thresholds[1:])):
                raise ValueError('Progression requires 101 increasing EXP thresholds')
            if level_at(data['exp'], thresholds) != player['level']:
                raise ValueError('Starting level disagrees with total EXP')
            if set(data['evs']) != STATS or set(data['ivs']) != STATS:
                raise ValueError('Live progression requires all six EVs and IVs')
            for stat in STATS:
                integer(data['evs'][stat], 0, 255, 'EV')
                integer(data['ivs'][stat], 0, 31, 'IV')
            if sum(data['evs'].values()) > 510 or data['ivs'] != player.get('ivs'):
                raise ValueError('Invalid EV total or inconsistent IV profile')
            if data['badges'] != badges:
                raise ValueError('Live progression must use the starting badge set')
            needed = [player['species']] + [m['species'] for m in pret['trainers'][case['trainer']]['party']]
            if any(move_id(name) not in data['species'] for name in needed):
                raise ValueError('Missing species progression data')
