"""Dump every planned-policy decision of N League chains, as the program's battle state can be built from it.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_parity --chains 200 --out /tmp/parity.json

One JSON document: {"format": "frlg-league-parity/1", "decisions": [...]}. A decision is a battle turn
("kind": "turn") or a between-fight top-up ("kind": "between"). Names are the program's slugs
("full-restore", "ice-beam"). A turn holds only what the program can read or track:
  own      our lead: species, level, raw summary stats (the program applies the badges), HP, status,
           stat stages, Mist turns left, moves with PP
  foe      the foe out: species, party slot, HP bar fill (pret's 48-pixel bar), status, stages,
           the fewest sleep turns the program can count (3 after Rest, else 2, one less per
           "is fast asleep"), Hyper Beam recharge, the two-turn move it charges
  field    weather and turns left, the foe side's Reflect / Light Screen turns left
  trainer  its party slots still standing and the Full Restores it has used
  bag, streak (the medicine turns in a row against this foe at this HP), attacks (our attacks on this foe's
  party slot so far: a foe's `sequence` picks by it), choice (row, item, move slot)
and, apart, "hidden": what the sim's policy reads but the program can't (the foe's exact HP, its
exact sleep counter, its moves' PP). The C++ parity test builds the program-visible state, then the
same state with "hidden" put back, so a gap is either a port bug or one of these visibility limits.
"""

import argparse
import json
from pathlib import Path

from pokesim.cli.frlg_league_chain import league_cases, BAG_NOW, LEVELS_NOW
from pokesim.games.frlg.battle.engine import Engine
from pokesim.games.frlg.battle.npc_ai import NPCTrainerAI
from pokesim.games.frlg.battle_data_export import MOVE_SLUGS, slug
from pokesim.games.frlg.league import planned
from pokesim.games.frlg.league.chain import run_chain, FIGHTS, MOVE_PP

FORMAT = 'frlg-league-parity/1'
TRAINERS = {'lorelei': 'TRAINER_ELITE_FOUR_LORELEI', 'bruno': 'TRAINER_ELITE_FOUR_BRUNO',
            'agatha': 'TRAINER_ELITE_FOUR_AGATHA', 'lance': 'TRAINER_ELITE_FOUR_LANCE',
            'champion': 'TRAINER_CHAMPION_FIRST_BULBASAUR'}
ITEMS = {'fullrestore': 'full-restore', 'maxpotion': 'max-potion', 'hyperpotion': 'hyper-potion',
         'superpotion': 'super-potion', 'fullheal': 'full-heal', 'parlyzheal': 'parlyz-heal', 'antidote': 'antidote',
         'awakening': 'awakening', 'burnheal': 'burn-heal', 'iceheal': 'ice-heal', 'elixir': 'elixir',
         'maxelixir': 'max-elixir', 'xspecial': 'x-special', 'xspeed': 'x-speed', 'xaccuracy': 'x-accuracy',
         'xattack': 'x-attack', 'xdefend': 'x-defend', 'guardspec': 'guard-spec'}
STATUS = {'': 'none', 'psn': 'poison', 'tox': 'poison', 'par': 'paralysis', 'slp': 'sleep', 'brn': 'burn',
          'frz': 'freeze'}
WEATHER = {'AI_WEATHER_SUN': 'sun', 'AI_WEATHER_RAIN': 'rain', 'AI_WEATHER_HAIL': 'hail',
           'AI_WEATHER_SANDSTORM': 'sand'}
STAGES = ('atk', 'def', 'spa', 'spd', 'spe', 'accuracy', 'evasion')
#   pret: a sleep lasts 2 to 5 turns, Rest's 3; the program counts the fewest left.
MIN_SLEEP, REST_SLEEP = 2, 3
#   pret GetScaledHPFraction: the HP bar's 48 pixels.
BAR_PIXELS = 48


def move_slugs(pret):
    """Showdown move id ("icebeam") -> program slug ("ice-beam")."""
    return {name.lower().replace('_', ''): slug(name, MOVE_SLUGS) for name in pret['moves']}


def item_slug(name):
    return ITEMS.get(name, name)


def bar_fill(hp, max_hp):
    pixels = hp * BAR_PIXELS // max_hp
    if pixels == 0 and hp > 0:
        pixels = 1
    return pixels / BAR_PIXELS


class SleepCount:
    """The foe's sleep as the program counts it from the battle text."""

    def __init__(self):
        self.left = 0

    def read(self, log):
        for line in log:
            if line.startswith('|-status|p2a') and line.split('|')[3] == 'slp':
                self.left = REST_SLEEP if 'move: Rest' in line else MIN_SLEEP
            elif line.startswith('|cant|p2a') and line.endswith('|slp'):
                self.left = max(1, self.left - 1)
            elif line.startswith('|-curestatus|p2a') or line.startswith('|switch|p2a'):
                self.left = 0


def stages(mon):
    """Its stat stages other than 0."""
    return {k: mon['boosts'][k] for k in STAGES if mon['boosts'].get(k, 0)}


def own_line(state, level, stats, moves):
    own = state['own']
    return {'species': own['species'], 'level': level, 'stats': dict(stats), 'hp': own['hp'],
            'status': STATUS.get(own['status'], own['status']),
            'stages': stages(own),
            'mist_turns': own.get('side_turns', {}).get('mist', 0),
            'moves': [{'id': moves.get(m['id'], m['id']), 'pp': m['pp']} for m in own['moves']]}


def foe_line(state, moves, sleep):
    foe = state['foe']
    locked = foe['locked_move']
    charging = moves.get(locked, locked) if locked and locked != 'recharge' else None
    side = foe.get('side_turns', {})
    return {'species': foe['species'], 'slot': foe['party_index'], 'fill': bar_fill(foe['hp'], foe['max_hp']),
            'status': STATUS.get(foe['status'], foe['status']),
            'sleep_min_left': sleep.left if foe['status'] == 'slp' else 0,
            'stages': stages(foe),
            'recharging': locked == 'recharge', 'charging': charging,
            'reflect_turns': side.get('reflect', 0), 'light_screen_turns': side.get('lightscreen', 0)}


def turn_line(state, goals, streak, attacks, choice, context):
    moves, sleep = context['moves'], context['sleep']
    sleep.read(state.get('log', ()))
    foe = state['foe']
    weather = WEATHER.get(foe.get('weather'), 'none')
    action = {'row': goals.get('_why', '')}
    if choice.get('kind') == 'item':
        action['item'] = item_slug(choice['item'])
    elif choice.get('kind') == 'move':
        action['move_slot'] = choice['slot']
    return {'kind': 'turn', 'chain': context['chain'], 'fight': context['fight'],
            'trainer': TRAINERS[context['fight']], 'turn': state['turn'],
            'own': own_line(state, context['level'], context['stats'], moves),
            'foe': foe_line(state, moves, sleep),
            'field': {'weather': weather, 'weather_turns': foe.get('weather_turns', 0) if weather != 'none' else 0},
            'trainer_state': {'foes_left': sum(p['hp'] > 0 for p in state['party']),
                              'full_restores_used': state.get('trainer_items_used', {}).get('fullrestore', 0)},
            'bag': {item_slug(k): v for k, v in sorted(state['bag'].items()) if v > 0},
            'streak': streak, 'attacks': attacks, 'choice': action,
            'hidden': {'foe_hp': foe['hp'], 'foe_sleep_turns': foe['sleep_turns'] if foe['status'] == 'slp' else 0,
                       'foe_pp': {moves.get(m['id'], m['id']): m['pp'] for m in foe['moves']}}}


def recorder(lines, context):
    """planned.action, recording each decision with the streak it saw."""
    def policy(state, ai, flags, items, goals):
        memo = goals.get('_memo', {})
        streak = memo.get('streak', 0) if memo.get('foe') == (state['foe']['species'], state['foe']['hp']) else 0
        attacks = memo.get(('attacks', state['foe']['party_index']), 0)
        choice = planned.action(state, ai, flags, items, goals)
        if context.get('fight') != goals.get('_fight'):
            context['fight'], context['sleep'] = goals['_fight'], SleepCount()
            context['level'] = context['levels'][context['fight']]
            context['stats'] = context['stats_by_fight'][context['fight']]
        lines.append(turn_line(state, goals, streak, attacks, choice, context))
        return choice
    return policy


def between_line(chain, fight, carry, max_hp, used):
    order = [item_slug(k) for k, n in used.items() for _ in range(n)]
    return {'kind': 'between', 'chain': chain, 'fight': fight,
            'carry': {'hp': carry['hp'], 'max_hp': max_hp, 'status': STATUS.get(carry['status'], carry['status']),
                      'pp': {k.lower(): v for k, v in carry['pp'].items()},
                      'full_pp': {k.lower(): v for k, v in MOVE_PP.items()},
                      'bag': {item_slug(k): v for k, v in sorted(carry['bag'].items()) if v > 0}},
            'used': order}


def dump(chains, seed, levels=LEVELS_NOW, bag=BAG_NOW):
    from pokesim.games.frlg.league.chain import ours_at
    cases, pret = league_cases()
    ai = NPCTrainerAI(pret)
    moves = move_slugs(pret)
    lines = []
    stats_by_fight = {f: {k: v for k, v in ours_at(levels[f]).items()} for f in FIGHTS}
    with Engine() as engine:
        for chain in range(chains):
            context = {'chain': chain, 'moves': moves, 'levels': levels, 'stats_by_fight': stats_by_fight}

            def on_between(fight, carry, max_hp, used, chain=chain):
                lines.append(between_line(chain, fight, carry, max_hp, used))
            run_chain(engine, cases, pret, ai, 'planned', dict(bag), levels, '{}:{}'.format(seed, chain),
                      policy_fn=recorder(lines, context), on_between=on_between, held_item='')
    return {'format': FORMAT, 'chains': chains, 'seed': seed, 'decisions': lines}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--chains', type=int, default=200)
    parser.add_argument('--seed', default='parity')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(argv)
    doc = dump(args.chains, args.seed)
    text = '{{"format": "{}", "chains": {}, "seed": "{}", "decisions": [\n'.format(doc['format'], doc['chains'], doc['seed'])
    text += ',\n'.join(json.dumps(line, separators=(',', ':')) for line in doc['decisions'])
    args.out.write_text(text + '\n]}\n')
    rows = {}
    for line in doc['decisions']:
        key = line['choice']['row'] if line['kind'] == 'turn' else 'between'
        rows[key] = rows.get(key, 0) + 1
    print(json.dumps({'decisions': len(doc['decisions']), 'by_row': rows}))


if __name__ == '__main__':
    main()
