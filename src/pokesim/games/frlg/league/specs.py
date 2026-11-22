"""Plan specs for the FRLG League (compact form; planned.build() expands them to the JSON plan).

Moves by matchup at Lv54 (see docs/battles/frlg-league-plan.md): Bite (Dark, special in Gen 3,
25 PP) wherever it is within a few points of Surf, so Surf's 15 PP last; Strength on Jynx and Lapras
(Water Absorb); Blizzard only on Dragonair, Dragonite and Venusaur (and the Champion's Gyarados
when PP allows). Setup goals serve a named move and stop at +2 Sp. Atk against Roar/Whirlwind users:
pret's AI_CV_Roar only favours phazing once a stat is above +2.
"""

import copy


def g(item, stage=1, serves=None):
    out = {'item': item, 'stage': stage}
    if serves:
        out['serves'] = serves
    return out


BASE = {
    'lorelei': {
        'foes': {
            0: {'moves': ['bite', 'surf'], 'setup': [g('xspecial', 3, 'bite')]},
            1: {'moves': ['bite', 'surf']},
            2: {'moves': ['bite', 'surf']},
            3: {'moves': ['bite', 'surf', 'strength']},
            4: {'moves': ['bite', 'strength']},
        },
        'pp_reserve': {'blizzard': 5}, 'fr_spend': 2, 'hard_items': {'maxelixir': 1},
    },
    'bruno': {
        'foes': {
            0: {'moves': ['surf'], 'setup': [g('xspecial', 2, 'surf'), g('xspeed', 1, 'surf')]},
            1: {'moves': ['surf', 'blizzard']},
            2: {'moves': ['surf', 'strength']},
            3: {'moves': ['surf']},
            4: {'moves': ['surf', 'strength']},
        },
        'between': {'hp': 0.8, 'pp': {'surf': 8}},
        'pp_reserve': {'blizzard': 5}, 'fr_spend': 1, 'hard_items': {'maxelixir': 1},
    },
    'agatha': {
        'foes': {
            0: {'moves': ['bite', 'surf'], 'setup': [g('xspecial', 2, 'bite'), g('xspeed', 1, 'bite')]},
            1: {'moves': ['surf', 'bite']},
            2: {'moves': ['bite', 'surf']},
            3: {'moves': ['surf', 'bite']},
            4: {'moves': ['bite', 'surf']},
        },
        'between': {'hp': 0.6, 'pp': {'surf': 6}},
        'pp_reserve': {'blizzard': 5}, 'fr_spend': 1, 'hard_items': {'maxelixir': 1},
    },
    'lance': {
        'foes': {
            0: {'moves': ['bite', 'surf'], 'setup': [g('xspecial', 2, 'blizzard'), g('xaccuracy', 1, 'blizzard')]},
            1: {'moves': ['blizzard', 'strength']},
            2: {'moves': ['blizzard', 'strength']},
            3: {'moves': ['surf']},
            4: {'moves': ['blizzard', 'bite']},
        },
        'between': {'hp': 1.0, 'pp': {'surf': 4, 'blizzard': 4}},
        'fr_spend': 2, 'hard_items': {'maxelixir': 1},
    },
    'champion': {
        'foes': {
            0: {'moves': ['surf'], 'setup': [g('guardspec'), g('xspecial', 2, 'blizzard'), g('xaccuracy', 2, 'blizzard'),
                                             g('xspeed', 1, 'blizzard')]},
            1: {'moves': ['bite', 'surf']},
            2: {'moves': ['surf']},
            3: {'moves': ['bite', 'surf']},
            4: {'moves': ['surf']},
            5: {'moves': ['blizzard']},
        },
        'between': {'hp': 1.0, 'pp': {'surf': 8, 'blizzard': 4}},
        'fr_spend': 2,
    },
}


def variant(spec, path, value):
    """A copy of spec with spec[fight][...][key] = value (path: tuple of keys)."""
    out = copy.deepcopy(spec)
    node = out
    for key in path[:-1]:
        node = node.setdefault(key, {})
    node[path[-1]] = value
    return out
