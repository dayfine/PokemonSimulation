"""FRLG EXP awards, thresholds, and Rare Candies with cartridge integer order.

Source: pret/pokefirered Cmd_getexp, experience_tables.h, and pokemon.c.
Battle outcomes are inputs; this module does not simulate winning a fight.
"""

from bisect import bisect_right


def defeat_exp(base_yield, opponent_level, trainer=False, participants=1,
               lucky_egg=False, traded=False):
    """EXP for one surviving participant without Exp. Share.

    The source truncates after yield * level / 7, participant division,
    then each 150/100 multiplier: Lucky Egg, trainer, traded, in that order.
    """
    for value, low, high, label in ((base_yield, 1, 255, "base EXP yield"),
            (opponent_level, 1, 100, "opponent level"), (participants, 1, 6, "participants")):
        if type(value) is not int or not low <= value <= high:
            raise ValueError("Invalid " + label)
    award = max(1, (base_yield * opponent_level // 7) // participants)
    for multiplier in (lucky_egg, trainer, traded):
        if multiplier:
            award = award * 150 // 100
    return award


def medium_slow_thresholds():
    """The Squirtle family's growth curve; source table overrides levels 0/1."""
    return [0, 1] + [6 * level ** 3 // 5 - 15 * level ** 2 + 100 * level - 140
                     for level in range(2, 101)]


def level_at(exp, thresholds):
    """Level at cumulative EXP, including equality with the next threshold."""
    if type(exp) is not int or exp < 0:
        raise ValueError("EXP must be a nonnegative integer")
    return max(1, min(100, bisect_right(thresholds, exp) - 1))


def rare_candy(exp, thresholds):
    """Set EXP to the next threshold, discarding current progress within a level."""
    level = level_at(exp, thresholds)
    return thresholds[level + 1] if level < 100 else exp
