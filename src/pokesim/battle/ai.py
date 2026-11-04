"""Execute the imported pret scoring scripts for the four milestone trainers.

The instruction branches and score changes come from the pinned decomp.
Damage helpers use Smogon previews rather than pret's AI_CalcDmg. This is a
script-policy approximation, not a cartridge RNG or full AI emulation.
Voluntary switching is outside the first milestone.
"""

import operator
import re


def move_id(name):
    return re.sub(r"[^a-z0-9]", "", name.lower())


STAT = {"ATK": "atk", "DEF": "def", "SPEED": "spe", "SPATK": "spa",
        "SPDEF": "spd", "ACC": "accuracy", "EVASION": "evasion"}
COMPARE = {"equal": operator.eq, "not_equal": operator.ne, "less_than": operator.lt,
           "more_than": operator.gt}
DISCOURAGED = {"EFFECT_" + e for e in ("EXPLOSION", "DREAM_EATER", "RAZOR_WIND", "SKY_ATTACK",
    "RECHARGE", "SKULL_BASH", "SOLAR_BEAM", "SPIT_UP", "FOCUS_PUNCH", "SUPERPOWER", "ERUPTION", "OVERHEAT")}


class TrainerAI:
    """An interpreter over one revision-stamped snapshot, with explicit helpers."""

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

        def value(token):
            try:
                return int(token, 0)
            except ValueError:
                if token.startswith("ABILITY_"):
                    return move_id(token[len("ABILITY_"):])
                return {"MOVE_POWER_DISCOURAGED": 0, "MOVE_NOT_MOST_POWERFUL": 1,
                        "MOVE_MOST_POWERFUL": 2}.get(token, token)

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
                result = 0  # These four encounters have no weather-setting moves.
            elif op.startswith("if_stat_level_"):
                stat = STAT[args[1][len("STAT_"):]]
                jump = COMPARE[op[len("if_stat_level_"):]](mon(args[0])["boosts"][stat] + 6, int(args[2]))
            elif op.startswith("if_hp_"):
                p = mon(args[0])
                jump = COMPARE[op[len("if_hp_"):]](p["hp"] * 100 // p["max_hp"], int(args[1]))
            elif op.startswith(("if_status", "if_not_status")):
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
            elif op == "if_target_faster":
                jump = target["speed"] > user["speed"] or (target["speed"] == user["speed"] and bool(rng.randrange(2)))
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
        conditions = {"STATUS1_ANY": bool(mon["status"]), "STATUS1_TOXIC_POISON": mon["status"] == "tox",
            "STATUS3_LEECHSEED": "leechseed" in mon["volatiles"], "STATUS3_ROOTED": "ingrain" in mon["volatiles"],
            "STATUS2_CURSED": "curse" in mon["volatiles"]}
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
