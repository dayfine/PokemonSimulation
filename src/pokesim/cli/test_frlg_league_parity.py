"""What the parity dump records as the program can see it: the HP bar and the counted sleep."""

import unittest

from pokesim.cli.frlg_league_parity import SleepCount, bar_fill


class BarFillTest(unittest.TestCase):

    def test_bar(self):
        cases = [
            ('full', (171, 171), 1.0),
            ('a sliver still shows one pixel', (1, 171), 1 / 48),
            ('pixels round down', (85, 171), 23 / 48),
            ('fainted', (0, 171), 0.0),
        ]
        for name, (hp, max_hp), fill in cases:
            with self.subTest(name):
                self.assertEqual(bar_fill(hp, max_hp), fill)


class SleepCountTest(unittest.TestCase):

    def test_sleep(self):
        cases = [
            ('Hypnosis: 2 at least', [['|-status|p2a: Gengar|slp|[from] move: Hypnosis']], 2),
            ('Rest: 3', [['|-status|p2a: Snorlax|slp|[from] move: Rest']], 3),
            ('one less per turn slept through, never below 1',
             [['|-status|p2a: Gengar|slp'], ['|cant|p2a: Gengar|slp'], ['|cant|p2a: Gengar|slp']], 1),
            ('woke up', [['|-status|p2a: Gengar|slp'], ['|-curestatus|p2a: Gengar|slp|[msg]']], 0),
            ('our sleep is not the foe\'s', [['|-status|p1a: Blastoise|slp']], 0),
        ]
        for name, turns, left in cases:
            with self.subTest(name):
                sleep = SleepCount()
                for log in turns:
                    sleep.read(log)
                self.assertEqual(sleep.left, left)


if __name__ == '__main__':
    unittest.main()
