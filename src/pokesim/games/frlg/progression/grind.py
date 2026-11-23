"""Compare ways to level the Mail Glitch grinders (mg-04) with a sweeper, by Monte Carlo.

    PYTHONPATH=src python3 -m pokesim.games.frlg.progression.grind --runs 200 --seed 1

Battle rules follow pret/pokefirered: CalculateBaseDamage order, badge boosts,
Cmd_getexp sharing (switch-in participants split EXP, traded x1.5, trainer x1.5),
wild move choice at random from GiveMonInitialMoveset's last four moves, and
the FRLG step encounter test (cooldown, rate buff). Durations in TIMING are
estimates for Fast text with battle scenes off; they are not cartridge data.
"""

import argparse
from bisect import bisect_right
import json
import random

from pokesim._test_paths import REPO
from pokesim.games.frlg.progression.experience import defeat_exp
from pokesim.games.frlg.progression.stats import summary_stats

DATA = REPO + "/data/games/frlg/progression/mail-glitch-grind-pret.json"
PARTY = REPO + "/data/games/frlg/progression/mail-glitch-mg03-party.json"
PHYSICAL = {"NORMAL", "FIGHTING", "FLYING", "POISON", "GROUND", "ROCK", "BUG", "GHOST", "STEEL"}
FRAMES_PER_SECOND = 59.7275
TIMING = {  # seconds of game time; estimates, see module docstring
    "battle_start": 5.0, "battle_end": 2.0, "choose_action": 1.0, "move": 2.5, "switch": 4.0,
    "shift_prompt": 2.0, "faint": 2.0, "exp_text": 1.5, "level_up": 3.0, "learn_auto": 2.5,
    "learn_decline": 6.0, "learn_replace": 8.0, "trainer_intro": 10.0, "trainer_defeat": 6.0,
    "vs_seeker_use": 5.0, "trainer_walk": 3.0,
}
STEP_FRAMES = {"walk": 16, "run": 8}
HEAL_TRIP_SECONDS = {  # round trip from the grinding tiles back to them
    "pokemon-tower-5f": 2 * 2 * STEP_FRAMES["walk"] / FRAMES_PER_SECOND + 4.0,  # PurifiedZone heal pad, 2 tiles
    "victory-road": 90.0,   # estimate: exit, Indigo Plateau Center, walk back
    "route-8-rematches": 40.0,  # estimate: Lavender Town Center is next to Route 8
}
HEAL_FLOOR = {"pokemon-tower-5f": 1.0, "victory-road": 0.5, "route-8-rematches": 0.5}  # heal below this HP share
TURN_CAP = 20


def load(path=DATA):
    with open(path) as source:
        return json.load(source)


def load_party(path=PARTY):
    with open(path) as source:
        return {mon["species"]: mon for mon in json.load(source)["party"]}


def level_at(exp, curve):
    return max(1, min(100, bisect_right(curve, exp) - 1))


def initial_moves(learnset, level):
    """GiveMonInitialMoveset: learn in order, skip duplicates, drop the oldest past four."""
    moves = []
    for learn_level, move in learnset:
        if learn_level > level:
            break
        if move not in moves:
            moves = (moves + [move])[-4:]
    return moves


class Battler:
    """One side's active Pokémon with the state a wild or rematch fight needs."""

    def __init__(self, data, species, level, ivs, nature, evs=None, moves=None, badges=False, traded=False,
                 pp=None, exp=None):
        info = data["species"][species]
        self.data, self.species, self.level, self.ivs, self.nature = data, species, level, ivs, nature
        self.evs = evs or dict.fromkeys(ivs, 0)
        self.types, self.abilities, self.badges, self.traded = info["types"], info["abilities"], badges, traded
        self.curve = data["growth_curves"][info["growth_rate"]]
        self.exp = self.curve[level] if exp is None else exp
        self.moves = moves or initial_moves(info["learnset"], level)
        self.max_pp = {m: data["moves"][m]["pp"] for m in self.moves}
        self.pp = dict(pp or self.max_pp)
        self.recalculate()
        self.hp = self.stats["hp"]
        self.clear_battle_state()
        self.status, self.sleep_turns, self.toxic = None, 0, 0

    def recalculate(self):
        self.stats = summary_stats(self.data["species"][self.species]["base_stats"], self.level,
                                   self.ivs, self.evs, self.nature)

    def clear_battle_state(self):
        self.confused, self.cursed, self.trapped = 0, False, False

    def battle_stat(self, stat):
        value = self.stats[stat]
        if self.badges and stat != "hp":
            value = value * 110 // 100  # FRLG badge boosts (all eight badges assumed)
        if stat == "spe" and self.status == "par":
            value //= 4
        return value


def type_multiplier(chart, move_type, defender):
    result = 10
    for attack, defend, multiplier in chart:
        if attack == move_type and defend in defender.types:
            result = result * multiplier // 10
    if move_type == "GROUND" and "LEVITATE" in defender.abilities:
        return 0
    return result


def damage(data, attacker, defender, name, rng, crit=None):
    """Gen 3 damage: base formula, crit x2, +2, STAB, type chart, 85-100% roll."""
    move = data["moves"][name]
    effect = move["effect"]
    if effect == "LEVEL_DAMAGE":
        return attacker.level if type_multiplier(data["type_chart"], move["type"], defender) else 0
    if effect == "SONICBOOM":
        return 20
    if effect == "SUPER_FANG":
        return max(1, defender.hp // 2)
    multiplier = type_multiplier(data["type_chart"], move["type"], defender)
    if not move["power"] or not multiplier:
        return 0
    physical = move["type"] in PHYSICAL
    attack = attacker.battle_stat("atk" if physical else "spa")
    defense = defender.battle_stat("def" if physical else "spd")
    if effect == "EXPLOSION":
        defense = max(1, defense // 2)
    base = attack * move["power"] * (2 * attacker.level // 5 + 2) // defense // 50 + 2
    if crit if crit is not None else rng.randrange(16) == 0:
        base *= 2
    if move["type"] in attacker.types:
        base = base * 15 // 10
    base = base * multiplier // 10
    return max(1, base * (100 - rng.randrange(16)) // 100)


def expected_damage(data, attacker, defender, name):
    """Mean of the 16 rolls without crits, times accuracy; ranks the sweeper's moves."""
    move = data["moves"][name]
    rolls = [damage(data, attacker, defender, name, random.Random(r), crit=False) for r in range(16)]
    return sum(rolls) / 16 * (move["accuracy"] or 100) / 100


class Outcome:
    def __init__(self):
        self.seconds, self.attacker_fainted, self.defender_fainted, self.stuck = 0.0, False, False, False
        self.awakenings = 0


def use_move(data, attacker, defender, name, rng, outcome):
    """Resolve one move with the effects that change who faints or when; others do nothing."""
    outcome.seconds += TIMING["move"]
    attacker.pp[name] -= 1
    if attacker.status == "slp":
        attacker.sleep_turns -= 1
        if attacker.sleep_turns > 0:
            return
        attacker.status = None
    if attacker.status == "par" and rng.randrange(4) == 0:
        return
    if attacker.confused:
        attacker.confused -= 1
        if attacker.confused and rng.randrange(2) == 0:
            hurt = attacker.stats["atk"] * 40 * (2 * attacker.level // 5 + 2) // attacker.stats["def"] // 50 + 2
            attacker.hp = max(0, attacker.hp - hurt)
            return
    move = data["moves"][name]
    effect = move["effect"]
    if move["accuracy"] and rng.randrange(100) >= move["accuracy"]:
        return
    if effect == "CURSE" and "GHOST" in attacker.types:
        if defender.cursed:
            return
        attacker.hp = max(0, attacker.hp - attacker.stats["hp"] // 2)
        defender.cursed = True
        return
    if effect == "MEAN_LOOK":
        defender.trapped = True
    if effect == "OHKO":
        if attacker.level >= defender.level and rng.randrange(100) < 30 + attacker.level - defender.level:
            defender.hp = 0
        return
    hits = 1
    if effect == "MULTI_HIT":
        hits = rng.choice((2, 2, 2, 3, 3, 3, 4, 5))
    elif effect == "DOUBLE_HIT":
        hits = 2
    dealt = 0
    for _ in range(hits):
        dealt += damage(data, attacker, defender, name, rng)
    defender.hp = max(0, defender.hp - dealt)
    if effect == "EXPLOSION":
        attacker.hp = 0
    if effect in ("RECOIL", "DOUBLE_EDGE"):
        attacker.hp = max(0, attacker.hp - dealt // (3 if effect == "DOUBLE_EDGE" else 4))
    if not defender.hp or (move["power"] and not dealt):
        return
    chance = move["chance"] if move["power"] else 100
    if rng.randrange(100) >= chance:
        return
    if effect in ("SLEEP",) and defender.status is None:
        defender.status, defender.sleep_turns = "slp", rng.randint(2, 5)
    elif effect in ("PARALYZE", "PARALYZE_HIT") and defender.status is None:
        defender.status = "par"
    elif effect in ("POISON", "POISON_HIT", "POISON_FANG") and defender.status is None \
            and not {"POISON", "STEEL"} & set(defender.types):
        defender.status, defender.toxic = "psn", 2 if effect == "POISON_FANG" else 0
    elif effect in ("CONFUSE", "CONFUSE_HIT") and not defender.confused:
        defender.confused = rng.randint(2, 5)


def end_of_turn(mon):
    if mon.hp and mon.status == "psn":
        mon.toxic += 1 if mon.toxic else 0
        mon.hp = max(0, mon.hp - max(1, mon.stats["hp"] * (mon.toxic or 2) // 16))
    if mon.hp and mon.cursed:
        mon.hp = max(0, mon.hp - max(1, mon.stats["hp"] // 4))


def usable(mon):
    return [m for m in mon.moves if mon.pp[m] > 0] or ["STRUGGLE"]


def sweeper_move(data, sweeper, foe):
    return max(usable(sweeper), key=lambda m: expected_damage(data, sweeper, foe, m))


def play_turn(data, player, foe, player_move, rng, outcome):
    """player_move None means the player switched or used the turn on something else."""
    outcome.seconds += TIMING["choose_action"]
    foe_move = rng.choice(usable(foe))
    order = [(player, foe, player_move), (foe, player, foe_move)]
    if player_move is not None:
        player_speed, foe_speed = player.battle_stat("spe"), foe.battle_stat("spe")
        if foe_speed > player_speed or (foe_speed == player_speed and rng.randrange(2)):
            order.reverse()
    for attacker, defender, move in order:
        if move is None or not attacker.hp or not defender.hp:
            continue
        use_move(data, attacker, defender, move, rng, outcome)
    for mon in (player, foe):
        end_of_turn(mon)


def fight(data, grinder, sweeper, foe, rng, solo_threshold=None):
    """One encounter; returns (Outcome, grinder participated).

    Switch trick: the grinder leads and switches out on turn 1 (switches go
    first, so the foe's move hits the sweeper). With solo_threshold set, the
    grinder instead attacks when it outspeeds and its best move's minimum roll
    is at least that fraction of the foe's HP, and finishes alone.
    """
    outcome = Outcome()
    grinder.clear_battle_state()
    sweeper.clear_battle_state()
    grinder_in = grinder.hp > 0
    active = sweeper
    if grinder_in and solo_threshold is not None:
        best = max(usable(grinder), key=lambda m: expected_damage(data, grinder, foe, m))
        low = min(damage(data, grinder, foe, best, random.Random(r), crit=False) for r in range(16))
        if grinder.battle_stat("spe") > foe.battle_stat("spe") and low >= solo_threshold * foe.hp:
            active = grinder
            play_turn(data, grinder, foe, best, rng, outcome)
            if foe.hp and grinder.hp and not grinder.trapped:
                outcome.seconds += TIMING["switch"]
                active = sweeper
                play_turn(data, sweeper, foe, None, rng, outcome)
            elif foe.hp and grinder.hp:
                while foe.hp and grinder.hp and outcome.seconds < 200:
                    play_turn(data, grinder, foe, best if grinder.pp[best] else usable(grinder)[0], rng, outcome)
            if not grinder.hp:
                outcome.seconds += TIMING["faint"] + TIMING["switch"]
                active = sweeper
    elif grinder_in:
        outcome.seconds += TIMING["switch"]
        play_turn(data, sweeper, foe, None, rng, outcome)
    else:
        outcome.seconds += TIMING["switch"]  # lead is fainted; the sweeper is sent out directly
    turns = 0
    while foe.hp and active.hp:
        turns += 1
        if turns > TURN_CAP:
            outcome.stuck = True
            break
        if active is sweeper and sweeper.status == "slp" and sweeper.cursed:
            sweeper.status, sweeper.sleep_turns = None, 0  # Awakening from the bag uses the turn
            outcome.awakenings += 1
            play_turn(data, active, foe, None, rng, outcome)
            continue
        play_turn(data, active, foe, sweeper_move(data, active, foe), rng, outcome)
    outcome.attacker_fainted = not sweeper.hp
    outcome.defender_fainted = not foe.hp
    return outcome, grinder.hp > 0 and (active is grinder or grinder_in)


def gain_level_ups(grinder, gained, target_move, outcome):
    """Apply EXP; count level-up and move-offer text; returns True when target_move is learned."""
    before = grinder.level
    grinder.exp += gained
    grinder.level = level_at(grinder.exp, grinder.curve)
    learned = False
    for level in range(before + 1, grinder.level + 1):
        outcome.seconds += TIMING["level_up"]
        for learn_level, move in grinder.data["species"][grinder.species]["learnset"]:
            if learn_level != level or move in grinder.moves:
                continue
            if move == target_move:
                outcome.seconds += TIMING["learn_replace"]
                learned = True
            elif len(grinder.moves) < 4:
                grinder.moves.append(move)
                grinder.max_pp[move] = grinder.pp[move] = grinder.data["moves"][move]["pp"]
                outcome.seconds += TIMING["learn_auto"]
            else:
                outcome.seconds += TIMING["learn_decline"]
    if grinder.level != before:
        hp_lost = grinder.stats["hp"] - grinder.hp
        grinder.recalculate()
        grinder.hp = grinder.stats["hp"] - hp_lost if grinder.hp else 0
    return learned


def award(grinder, sweeper, foe_species, foe_level, data, trainer, grinder_shared, outcome, target_move):
    exp_yield = data["species"][foe_species]["exp_yield"]
    participants = 2 if grinder_shared and grinder.hp else 1
    outcome.seconds += TIMING["faint"]
    learned = False
    if grinder_shared and grinder.hp:
        outcome.seconds += TIMING["exp_text"]
        learned = gain_level_ups(grinder, defeat_exp(exp_yield, foe_level, trainer, participants,
                                                     traded=grinder.traded), target_move, outcome)
    if sweeper.hp:
        outcome.seconds += TIMING["exp_text"]
        sweeper.exp += defeat_exp(exp_yield, foe_level, trainer, participants, traded=sweeper.traded)
        new_level = level_at(sweeper.exp, sweeper.curve)
        if new_level != sweeper.level:
            outcome.seconds += TIMING["level_up"] * (new_level - sweeper.level)
            hp_lost = sweeper.stats["hp"] - sweeper.hp
            sweeper.level = new_level
            sweeper.recalculate()
            sweeper.hp = sweeper.stats["hp"] - hp_lost
    return learned


def steps_to_encounter(rate, rng, cooldown=None):
    """FRLG TryStandardWildEncounter on one metatile behavior (no 60% global roll), no repel."""
    if cooldown is None:
        cooldown = 0 if rate >= 80 else 8 if rate < 10 else 8 - rate // 10
    since, buff, steps = 0, 0, 0
    while True:
        steps += 1
        passed = since >= cooldown
        if not passed:
            since += 1
            passed = rng.randrange(100) < 5
        if not passed:
            continue
        if rng.randrange(1600) < min(1600, rate * 16 + buff * 16 // 200):
            return steps
        buff += rate


def wild_foe(data, table, rng):
    roll, total = rng.randrange(100), 0
    for slot, weight in zip(table["slots"], data["land_slot_rates"]):
        total += weight
        if roll < total:
            level = rng.randint(slot["min_level"], slot["max_level"])
            ivs = {s: rng.randrange(32) for s in ("hp", "atk", "def", "spe", "spa", "spd")}
            return Battler(data, slot["species"], level, ivs, rng.choice(data["natures"]))


def party_battler(data, mon, badges=True):
    """Saved summary stats stay until the next level-up, as in the game (EVs apply then)."""
    battler = Battler(data, mon["species"], mon["level"], mon["ivs"], data["natures"][mon["nature_index"]],
                      evs=mon["evs"], moves=[m["name"] for m in mon["moves"]], badges=badges,
                      traded=mon["traded"], pp={m["name"]: m["pp"] for m in mon["moves"]}, exp=mon["exp"])
    battler.stats = dict(mon["stats"])
    battler.hp = battler.stats["hp"]
    return battler


class GrindResult:
    def __init__(self):
        self.seconds = self.battles = self.heal_trips = self.sweeper_faints = self.grinder_faints = 0
        self.stuck = self.awakenings = 0
        self.exp = 0
        self.done = False


def needs_heal(mon, floor):
    return mon.hp < floor * mon.stats["hp"] or mon.status is not None or all(
        mon.pp[m] == 0 for m in mon.moves if mon.data["moves"][m]["power"])


def heal(mon):
    mon.hp, mon.status, mon.toxic = mon.stats["hp"], None, 0
    mon.pp = dict(mon.max_pp)


def grind_wild(data, party, grinder_species, target_level, target_move, spot, table_index, rng,
               solo_threshold=None, max_battles=2000):
    """Grind one grinder to target_level on one wild land table; one Monte Carlo run."""
    grinder, sweeper = party_battler(data, party[grinder_species]), party_battler(data, party["BLASTOISE"])
    table = data["spots"][spot][table_index]
    step_seconds = STEP_FRAMES["run" if table["allow_running"] else "walk"] / FRAMES_PER_SECOND
    result, start_exp = GrindResult(), grinder.exp
    heal(grinder)
    heal(sweeper)
    while grinder.level < target_level and result.battles < max_battles:
        if needs_heal(sweeper, HEAL_FLOOR[spot]) or needs_heal(grinder, 1.0):
            result.heal_trips += 1
            result.seconds += HEAL_TRIP_SECONDS[spot]
            heal(sweeper)
            heal(grinder)
        result.seconds += steps_to_encounter(table["encounter_rate"], rng) * step_seconds
        foe = wild_foe(data, table, rng)
        outcome, shared = fight(data, grinder, sweeper, foe, rng, solo_threshold)
        result.battles += 1
        outcome.seconds += TIMING["battle_start"] + TIMING["battle_end"]
        if outcome.defender_fainted:
            award(grinder, sweeper, foe.species, foe.level, data, False, shared, outcome, target_move)
        result.seconds += outcome.seconds
        result.sweeper_faints += outcome.attacker_fainted
        result.stuck += outcome.stuck
        result.awakenings += outcome.awakenings
        if not grinder.hp:
            result.grinder_faints += 1
            heal(grinder)  # Revive plus heal trip, charged on the next loop
            grinder.hp = grinder.stats["hp"] - 1
        if outcome.attacker_fainted:
            heal(sweeper)
            sweeper.hp = sweeper.stats["hp"] - 1  # forces a heal trip next encounter
    result.exp, result.done = grinder.exp - start_exp, grinder.level >= target_level
    return result


def rematch_party(data, trainer):
    members = []
    for mon in trainer["party"]:
        iv = mon["iv"] * 31 // 255  # CreateNPCTrainerParty fixedIV
        members.append(Battler(data, mon["species"], mon["level"], dict.fromkeys(
            ("hp", "atk", "def", "spe", "spa", "spd"), iv), data["natures"][0], moves=mon.get("moves")))
    return members


def grind_rematches(data, party, grinder_species, target_level, target_move, rng, trainers_per_use=3,
                    max_battles=2000):
    """VS Seeker on one route: 100 steps to recharge, each in-range trainer agrees 70% of the time.

    Every foe Pokémon gets the switch trick: on a trainer's next Pokémon the
    Shift prompt sends the grinder back in for free, then it switches out.
    """
    grinder, sweeper = party_battler(data, party[grinder_species]), party_battler(data, party["BLASTOISE"])
    singles = [t for t in data["rematches"].values() if not t["double"]]
    result, start_exp = GrindResult(), grinder.exp
    step_seconds = STEP_FRAMES["run"] / FRAMES_PER_SECOND
    while grinder.level < target_level and result.battles < max_battles:
        result.seconds += 100 * step_seconds + TIMING["vs_seeker_use"]
        for trainer in rng.sample(singles, min(trainers_per_use, len(singles))):
            if rng.randrange(100) < 30 or grinder.level >= target_level:
                continue
            if needs_heal(sweeper, HEAL_FLOOR["route-8-rematches"]) or needs_heal(grinder, 1.0):
                result.heal_trips += 1
                result.seconds += HEAL_TRIP_SECONDS["route-8-rematches"]
                heal(sweeper)
                heal(grinder)
            result.battles += 1
            result.seconds += TIMING["trainer_walk"] + TIMING["trainer_intro"] + TIMING["trainer_defeat"]
            for index, foe in enumerate(rematch_party(data, trainer)):
                outcome, shared = fight(data, grinder, sweeper, foe, rng)
                if index:
                    outcome.seconds += TIMING["shift_prompt"] + TIMING["switch"]
                if outcome.defender_fainted:
                    award(grinder, sweeper, foe.species, foe.level, data, True, shared, outcome, target_move)
                result.seconds += outcome.seconds
                result.sweeper_faints += outcome.attacker_fainted
                result.stuck += outcome.stuck
                result.awakenings += outcome.awakenings
                if outcome.attacker_fainted or outcome.stuck:
                    heal(sweeper)
                    sweeper.hp = sweeper.stats["hp"] - 1
                    break
    result.exp, result.done = grinder.exp - start_exp, grinder.level >= target_level
    return result


STRATEGIES = {
    "tower-switch": lambda d, p, g, lv, mv, rng: grind_wild(d, p, g, lv, mv, "pokemon-tower-5f", 0, rng),
    "tower-mimien-solo": lambda d, p, g, lv, mv, rng: grind_wild(d, p, g, lv, mv, "pokemon-tower-5f", 0, rng,
                                                                 solo_threshold=1.0),
    "victory-road-1f-switch": lambda d, p, g, lv, mv, rng: grind_wild(d, p, g, lv, mv, "victory-road", 0, rng),
    "victory-road-2f-switch": lambda d, p, g, lv, mv, rng: grind_wild(d, p, g, lv, mv, "victory-road", 1, rng),
    "route-8-vs-seeker": lambda d, p, g, lv, mv, rng: grind_rematches(d, p, g, lv, mv, rng),
}
GRINDERS = (("FARFETCHD", 21, "KNOCK_OFF"), ("MR_MIME", 33, "RECYCLE"))


def summarize(data, party, strategy, runs, seed):
    """Mean totals over runs for both grinders in sequence (each run starts from the save)."""
    rng = random.Random(seed)
    rows = {}
    for species, level, move in GRINDERS:
        if party[species]["level"] >= level and move in [m["name"] for m in party[species]["moves"]]:
            rows[species] = {"already_done": True}
            continue
        results = [STRATEGIES[strategy](data, party, species, level, move, rng) for _ in range(runs)]
        battles = sum(r.battles for r in results)
        hours = sum(r.seconds for r in results) / 3600
        rows[species] = {"already_done": False, "completed_runs": sum(r.done for r in results),
            "exp_per_hour": round(sum(r.exp for r in results) / hours),
            "battles": round(battles / runs, 1), "heal_trips": round(sum(r.heal_trips for r in results) / runs, 1),
            "minutes": round(hours * 60 / runs, 1),
            "sweeper_faints_per_1000_battles": round(1000 * sum(r.sweeper_faints for r in results) / battles, 2),
            "grinder_faints_per_1000_battles": round(1000 * sum(r.grinder_faints for r in results) / battles, 2),
            "stuck_per_1000_battles": round(1000 * sum(r.stuck for r in results) / battles, 2),
            "awakenings": round(sum(r.awakenings for r in results) / runs, 1)}
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    data, party = load(), load_party()
    print(json.dumps({name: summarize(data, party, name, args.runs, args.seed) for name in STRATEGIES}, indent=1))


if __name__ == "__main__":
    main()
