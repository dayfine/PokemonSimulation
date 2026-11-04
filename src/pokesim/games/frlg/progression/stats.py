"""FRLG solo-lead EV awards and raw summary stats, without battle/badge boosts."""

ORDER = ("hp", "atk", "def", "spe", "spa", "spd")  # MonGainEVs cap allocation order.


def gain_evs(evs, yields, limits):
    """Full species yield for a surviving participant; no Pokérus/Macho Brace."""
    result = dict(evs)
    for stat in ORDER:
        gain = min(yields[stat], limits["per_stat"] - result[stat], limits["total"] - sum(result.values()))
        result[stat] += max(0, gain)
    return result


def summary_stats(base, level, ivs, evs, nature):
    """CalculateMonStats integer order for the Squirtle family; HP has no nature."""
    result = {}
    for stat in ORDER:
        value = (2 * base[stat] + ivs[stat] + evs[stat] // 4) * level // 100
        result[stat] = value + level + 10 if stat == "hp" else (value + 5) * nature[stat] // 100
    return result
