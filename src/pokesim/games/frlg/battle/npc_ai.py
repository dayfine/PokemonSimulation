"""Game NPC move-selection AI, interpreted from pret's FRLG scoring scripts.

The imported snapshot selects trainer and move coverage: either the original
four AutoStory experiments or all 69 trainers in Pokeguy's route. This module
selects the enemy trainer's moves; our solo player's strategy is player_action()
in policy.py. NPC item use and compulsory replacement are also in policy.py.

The instruction branches and score changes come from the pinned decomp.
Damage helpers use Smogon previews rather than pret's AI_CalcDmg. This is a
script-policy approximation, not a cartridge RNG or full AI emulation.
Voluntary switching is not modeled; switch moves such as Baton Pass run in Showdown.
"""

import operator
import re
from functools import lru_cache


def move_id(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


STAT = {"ATK": "atk", "DEF": "def", "SPEED": "spe", "SPATK": "spa",
        "SPDEF": "spd", "ACC": "accuracy", "EVASION": "evasion"}
COMPARE = {"equal": operator.eq, "not_equal": operator.ne, "less_than": operator.lt,
           "more_than": operator.gt}
STAT_OPS = {'if_stat_level_' + name for name in COMPARE}
HP_OPS = {'if_hp_' + name for name in COMPARE}
STATUS_OPS = {'if_status', 'if_status2', 'if_status3', 'if_not_status', 'if_not_status2', 'if_not_status3'}
DISCOURAGED = {"EFFECT_" + e for e in ("EXPLOSION", "DREAM_EATER", "RAZOR_WIND", "SKY_ATTACK",
    "RECHARGE", "SKULL_BASH", "SOLAR_BEAM", "SPIT_UP", "FOCUS_PUNCH", "SUPERPOWER", "ERUPTION", "OVERHEAT")}


@lru_cache(maxsize=None)
def script_value(token):
    """Decode immutable script operands once, preserving symbolic constants."""
    try:
        return int(token, 0)
    except ValueError:
        if token.startswith('ABILITY_'):
            return move_id(token[len('ABILITY_'):])
        return {'MOVE_POWER_DISCOURAGED': 0, 'MOVE_NOT_MOST_POWERFUL': 1,
                'MOVE_MOST_POWERFUL': 2}.get(token, token)


class NPCTrainerAI:
    """Choose enemy trainer moves using a revision-stamped pret script snapshot."""

    def __init__(self, snapshot):
        self.script = snapshot["ai"]
        self.metadata = {move_id(k): v for k, v in snapshot["moves"].items()}
        self.names = {move_id(k): "MOVE_" + k for k in snapshot["moves"]}

    def metadata_for(self, name):
        if name not in self.metadata:
            raise ValueError("Move outside imported AI snapshot: " + name)
        return self.metadata[name]

    def scores(self, state, flags, rng):
        """Score each move. Damage samples are shared across the scoring flags."""
        user, target = state["foe"], state["own"]
        rolls = [100 - rng.randrange(16) for _ in range(4)]
        damage = [max(1, max(m.get("damage", [0])) * rolls[i] // 100)
                  if self.metadata_for(m["id"])["power"] > 1 else 0
                  for i, m in enumerate(user["moves"])]
        scores = [100 if m["pp"] and not m["disabled"] else 0 for m in user["moves"]]
        # pret executes flags in bit order: bad move, viability, try to faint.
        for flag, root in self.script["roots"].items():
            if flag not in flags:
                continue
            for slot, move in enumerate(user["moves"]):
                if move["pp"] and not move["disabled"]:
                    scores[slot] = self.execute(root, scores[slot], user, target, slot, damage, rng)
        return scores

    def execute(self, root, score, user, target, slot, damage, rng):
        """Run one script to `end`, failing closed on unsupported instructions."""
        labels, code = self.script["labels"], self.script["instructions"]
        pc, result = labels[root], 0
        move = user["moves"][slot]
        meta = self.metadata_for(move["id"])

        def mon(which):
            return user if which == "AI_USER" else target

        value = script_value

        for _ in range(2000):
            op, *args = code[pc]
            pc += 1
            jump = False
            if op == "end":
                return score
            if op == "goto":
                pc = labels[args[0]]
                continue
            if op == "score":
                score = max(0, score + int(args[0]))
                continue
            if op == "get_how_powerful_move_is":
                eligible = [i for i, m in enumerate(user["moves"])
                            if self.metadata_for(m["id"])["effect"] not in DISCOURAGED
                            and self.metadata_for(m["id"])["power"] > 1]
                result = 0 if slot not in eligible else (2 if damage[slot] >= max(damage[i] for i in eligible) else 1)
            elif op == "get_ability":
                result = mon(args[0])["ability"]
            elif op in ("get_target_type1", "get_target_type2", "get_user_type1", "get_user_type2"):
                types = (target if "target" in op else user)["types"]
                result = "TYPE_" + types[min(int(op[-1]) - 1, len(types) - 1)].upper()
            elif op == "get_curr_move_type":
                result = meta["type"]
            elif op == "get_last_used_move":
                result = self.names.get(mon(args[0])["last_move"], "MOVE_NONE")
            elif op in ("get_move_effect_from_result", "get_move_power_from_result", "get_move_type_from_result"):
                previous = self.metadata.get(move_id(str(result)[len("MOVE_"):]))
                key = {"get_move_effect_from_result": "effect", "get_move_power_from_result": "power", "get_move_type_from_result": "type"}[op]
                result = previous[key] if previous else 0
            elif op == "get_weather":
                result = user.get("weather", 0)
            elif op == "get_gender":
                result = {"M": "MON_MALE", "F": "MON_FEMALE", "N": "MON_GENDERLESS"}[mon(args[0])["gender"]]
            elif op == "count_alive_pokemon":
                result = mon(args[0])["reserves_alive"]
            elif op == "is_first_turn_for":
                result = int(mon(args[0])["first_turn"])
            elif op == "get_protect_count":
                result = mon(args[0])["protect_count"]
            elif op == "if_level_cond":
                jump = (operator.gt, operator.lt, operator.eq)[int(args[0])](user["level"], target["level"])
            elif op == "if_not_double_battle":
                jump = True
            elif op == "if_target_not_taunted":
                jump = "taunt" not in target["volatiles"]
            elif op == "if_side_affecting":
                condition = args[1][len("SIDE_STATUS_"):].lower()
                jump = condition in mon(args[0])["side_conditions"]
            elif op == "if_more_than":
                jump = result > value(args[0])
            elif op in STAT_OPS:
                stat = STAT[args[1][len("STAT_"):]]
                jump = COMPARE[op[len("if_stat_level_"):]](mon(args[0])["boosts"][stat] + 6, int(args[2]))
            elif op in HP_OPS:
                p = mon(args[0])
                jump = COMPARE[op[len("if_hp_"):]](p["hp"] * 100 // p["max_hp"], int(args[1]))
            elif op in STATUS_OPS:
                jump = self.has_status(mon(args[0]), args[1])
                if "not_status" in op:
                    jump = not jump
            elif op in ("if_equal", "if_equal_", "if_not_equal"):
                jump = result == value(args[0])
                if op == "if_not_equal":
                    jump = not jump
            elif op in ("if_effect", "if_not_effect"):
                jump = (meta["effect"] == args[0]) == (op == "if_effect")
            elif op == "if_move":
                jump = self.names[move["id"]] == args[0]
            elif op == "if_random_less_than":
                jump = rng.randrange(256) < int(args[0])
            elif op == "if_can_faint":
                jump = meta["power"] > 1 and damage[slot] >= target["hp"]
            elif op == "if_type_effectiveness":
                expected = float(args[0].split("_x")[1].replace("_", "."))
                jump = move["effectiveness"] == expected
            elif op in ("if_in_bytes", "if_not_in_bytes"):
                values = []
                index = labels[args[0]]
                while code[index][0] == ".byte":
                    if code[index][1] == "-1":
                        break
                    values.extend(value(v) for v in code[index][1:])
                    index += 1
                jump = (result in values) == (op == "if_in_bytes")
            elif op in ("if_target_faster", "if_user_faster"):
                faster = target["speed"] > user["speed"] or (target["speed"] == user["speed"] and bool(rng.randrange(2)))
                jump = faster if op == "if_target_faster" else not faster
            elif op in ("if_has_move_with_effect", "if_doesnt_have_move_with_effect"):
                # Only moves already revealed to the trainer are known for AI_TARGET.
                known = mon(args[0])["moves"] if args[0] == "AI_USER" else target.get("revealed_moves", [])
                found = any(self.metadata_for(m["id"])["effect"] == args[1] for m in known)
                jump = found == (op == "if_has_move_with_effect")
            elif op == "if_any_move_disabled":
                jump = any(m["disabled"] for m in mon(args[0])["moves"])
            elif op == "if_user_has_no_attacking_moves":
                jump = not any(self.metadata_for(m["id"])["power"] for m in user["moves"])
            else:
                raise ValueError("Unsupported pret AI instruction: " + op)
            if jump:
                pc = labels[args[-1]]
        raise ValueError("AI script did not terminate")

    @staticmethod
    def has_status(mon, flag):
        """Translate supported symbolic pret status masks to Showdown state."""
        if " | " in flag:
            return any(NPCTrainerAI.has_status(mon, part) for part in flag.split(" | "))
        conditions = {"STATUS1_ANY": bool(mon["status"]), "STATUS1_TOXIC_POISON": mon["status"] == "tox",
            "STATUS3_LEECHSEED": "leechseed" in mon["volatiles"], "STATUS3_ROOTED": "ingrain" in mon["volatiles"],
            "STATUS2_CURSED": "curse" in mon["volatiles"]}
        conditions.update({"STATUS1_" + name: mon["status"] == status for name, status in
            (("SLEEP", "slp"), ("POISON", "psn"), ("BURN", "brn"), ("PARALYSIS", "par"), ("FREEZE", "frz"))})
        conditions.update({"STATUS" + group + "_" + name: volatile in mon["volatiles"] for group, name, volatile in
            (("2", "CONFUSION", "confusion"), ("2", "INFATUATION", "attract"),
             ("2", "FOCUS_ENERGY", "focusenergy"), ("2", "SUBSTITUTE", "substitute"),
             ("2", "ESCAPE_PREVENTION", "trapped"), ("2", "FORESIGHT", "foresight"),
             ("2", "NIGHTMARE", "nightmare"), ("2", "TORMENT", "torment"),
             ("3", "PERISH_SONG", "perishsong"), ("3", "YAWN", "yawn"),
             ("3", "IMPRISONED_OTHERS", "imprison"), ("3", "MUDSPORT", "mudsport"),
             ("3", "WATERSPORT", "watersport"))})
        if flag not in conditions:
            raise ValueError("Unsupported AI status mask " + flag)
        return conditions[flag]

    def choose_move(self, state, flags, rng):
        """Use pret's best-score selection, including its duplicate-new-best slot."""
        moves = state["foe"]["moves"]
        scores = self.scores(state, flags, rng)
        best, tied = scores[0], [0]
        for slot in range(1, len(scores)):
            if scores[slot] > best:
                best, tied = scores[slot], [slot]
            if scores[slot] == best:
                tied.append(slot)
        if not any(m["pp"] and not m["disabled"] for m in moves):
            return {"kind": "move", "slot": 0}  # Showdown substitutes Struggle.
        return {"kind": "move", "slot": rng.choice(tied)}
