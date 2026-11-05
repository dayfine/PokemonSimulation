"""CLI report and drawing output for an actual computed local path."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pokesim.cli.route import main
from pokesim.maps.local_routing import LocalMap
from pokesim.png import Image


class RouteCliTest(unittest.TestCase):
    def view(self):
        return LocalMap(dict(name='room', source=dict(decomp_file='fixture', revision='fixed', date='test'),
            tiles=['...', '.#.', '...'], points=dict(start=[0, 1], goal=[2, 1])), 'bdsp',
            provenance=dict(revision='f' * 40, manifest_sha256='a' * 64))

    def test_outputs_computed_path_provenance_and_image(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'route.json'
            image = Path(directory) / 'route.png'
            args = ['--game', 'bdsp', '--map', 'room', '--start', 'start', '--goal', 'goal',
                    '--revision', 'f' * 40, '--json', str(report), '--png', str(image)]
            with mock.patch('pokesim.cli.route.load_pinned_map', return_value=self.view()), redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(args), 0)
            data = json.loads(report.read_text())
            self.assertEqual(data['source']['revision'], 'f' * 40)
            self.assertEqual(data['moves'][-1]['tile'], [2, 1])
            self.assertEqual(len(data['moves']), 4)
            self.assertNotIn([1, 1], [move['tile'] for move in data['moves']])
            self.assertIn('single-map static route; transitions excluded', data['limitations'])
            self.assertIn('@', output.getvalue())
            self.assertIn('X', output.getvalue())
            self.assertEqual(Image.read(str(image)).width, 48)

    def test_missing_route_and_invalid_cost_are_failures(self):
        view = self.view()
        view.occupied.update((point.tile for point in view.map_file.points))
        args = ['--game', 'bdsp', '--map', 'room', '--start', 'start', '--goal', 'goal', '--revision', 'f' * 40]
        with mock.patch('pokesim.cli.route.load_pinned_map', return_value=view), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as result:
                main(args)
            self.assertEqual(result.exception.code, 1)
        for cost in ('-1', 'nan', 'inf'):
            with self.subTest(cost=cost), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(args + ['--grass-cost', cost])

    def test_unreachable_goal_does_not_write_a_report(self):
        view = LocalMap(dict(name='room', source=dict(decomp_file='fixture', revision='fixed', date='test'),
            tiles=['.#.']), 'bdsp')
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / 'route.json'
            args = ['--game', 'bdsp', '--map', 'room', '--start', '0,0', '--goal', '2,0',
                    '--revision', 'f' * 40, '--json', str(report)]
            with mock.patch('pokesim.cli.route.load_pinned_map', return_value=view), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as result:
                    main(args)
                self.assertEqual(result.exception.code, 2)
                self.assertFalse(report.exists())


if __name__ == '__main__':
    unittest.main()
