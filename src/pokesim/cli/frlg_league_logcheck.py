"""Compare an AutoStory FRLG League log against the PokeGuy-replica policy table.

Reads SerialPrograms.log lines ("Battle: turn N, HP ... (P% of the bar)", "policy:",
"move N" / "using the ITEM", "trainer's X is out", "Summary of party slot 1", and
out-of-battle "Bag: using the ITEM"). For each logged turn it rebuilds the state the
log shows (own HP, foe out, stages we set, PP, bag) and reports actions the replica
table would not take. Foe HP and battle-text events (evasion, confusion) are not in
the log yet, so rules that need them are reported as unchecked.

PYTHONPATH=src python3 -m pokesim.cli.frlg_league_logcheck LOG --from 05:08 --to 06:15
"""

import argparse
import re

# Foe's best normal-roll hit on our Lv54-56 Blastoise (frlg_league_chain damage previews).
D = {'dewgong': 18, 'cloyster': 12, 'slowbro': 24, 'jynx': 24, 'lapras': 31,
     'onix': 34, 'hitmonchan': 54, 'hitmonlee': 57, 'machamp': 75,
     'gengar': 40, 'golbat': 28, 'haunter': 40, 'arbok': 52,
     'gyarados': 78, 'dragonair': 52, 'aerodactyl': 66, 'dragonite': 96}
GOALS = {'lorelei': {'xspecial': 4, 'setup_foe': 'dewgong'}, 'bruno': {'xspecial': 2, 'setup_foe': 'onix'},
         'agatha': {'xspecial': 3, 'setup_foe': 'gengar'}, 'lance': {'xspecial': 3, 'xaccuracy': 2, 'setup_foe': 'gyarados'},
         'champion': {'xspecial': 2, 'xaccuracy': 2, 'setup_foe': 'pidgeot'}}
MEDICINE = {'full-restore', 'super-potion', 'hyper-potion', 'max-potion', 'potion'}
SLOTS = ['bite', 'strength', 'surf', 'blizzard']
PP = {'bite': 25, 'strength': 15, 'surf': 15, 'blizzard': 5}


def check(lines):
    out, fight, foe, max_hp, turn = [], None, None, None, None
    pp, used, bag_sp = dict(PP), {}, None
    for line in lines:
        t = line[11:19]
        m = re.search(r"Summary of party slot 1: \w+ Lv(\d+), (\d+) HP", line)
        if m:
            max_hp = int(m.group(2))
        m = re.search(r"Story: (\w+) is TRAINER_(ELITE_FOUR|CHAMPION)", line)
        if m:
            fight, used = m.group(1), {}
        m = re.search(r"trainer's (\w+) is out", line)
        if m:
            foe = m.group(1)
        m = re.search(r"Battle: turn (\d+), HP \w+ \((\d+)% of the bar\).*?(\d+) Super Potions", line)
        if m and fight:
            turn = {'t': t, 'n': int(m.group(1)), 'hp': int(m.group(2)) * (max_hp or 171) / 100, 'foe': foe}
            bag_sp = int(m.group(3))
            continue
        m = re.search(r"Bag: using the ([\w-]+)", line)
        if m and m.group(1) == 'full-restore' and bag_sp:
            out.append((t, fight, '-', 'between fights: Full Restore out of battle with {} Super Potions in the bag'.format(bag_sp)))
        m = re.search(r"Battle: (?:move (\d)|using the ([\w-]+) in row)", line)
        if not (m and turn and fight):
            continue
        hp, d = turn['hp'], D.get(turn['foe'], 0)
        tag = (turn['t'], fight, '{} t{}'.format(turn['foe'], turn['n']))
        if m.group(1):
            move = SLOTS[int(m.group(1)) - 1]
            if hp <= d:
                out.append(tag + ('attack at HP {:.0f} <= D {} (KO risk): replica heals unless the hit is a safe finish'.format(hp, d),))
            if pp[move] == 0:
                out.append(tag + ('{} has 0 PP by the log count'.format(move),))
            pp[move] = max(0, pp[move] - 1)
            if move != 'surf' and pp['surf'] == 0:
                out.append(tag + ('Surf empty: replica uses Elixir/Max Elixir before falling back to {}'.format(move),))
        else:
            item = m.group(2)
            used[item] = used.get(item, 0) + 1
            if item in MEDICINE and hp > d:
                out.append(tag + ('{} at HP {:.0f} > D {}: no KO risk, replica attacks/sets up'.format(item, hp, d),))
            goal = GOALS.get(fight, {})
            if item.startswith('x-') and goal and turn['foe'] != goal['setup_foe'] and used[item] == 1:
                out.append(tag + ('setup started on {} not on {}'.format(turn['foe'], goal['setup_foe']),))
        turn = None
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log')
    parser.add_argument('--date', default='2026-11-16')
    parser.add_argument('--from', dest='start', default='00:00')
    parser.add_argument('--to', default='23:59')
    args = parser.parse_args(argv)
    lines = [l for l in open(args.log, errors='replace')
             if l.startswith(args.date) and args.start <= l[11:16] <= args.to]
    rows = check(lines)
    for row in rows:
        print(' | '.join(row))
    print('{} mismatches. Unchecked (not in the log): foe HP, foe evasion/stat changes, confusion, misses.'.format(len(rows)))


if __name__ == '__main__':
    main()
