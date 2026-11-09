"""CLI report and drawing output for an actual computed local path."""

from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree

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
            svg = Path(directory) / 'route.svg'
            args = ['--game', 'bdsp', '--map', 'room', '--start', 'start', '--goal', 'goal',
                    '--revision', 'f' * 40, '--json', str(report), '--png', str(image), '--svg', str(svg)]
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
            root = ElementTree.fromstring(svg.read_text())
            self.assertEqual(root[1].attrib.get('fill'), '#f6f7f4')
            text = ' '.join(root.itertext())
            self.assertIn('room', text)
            self.assertIn('local tile coordinates', text)
            self.assertIn('planned route', text)
            self.assertNotIn('walked', text)

    def test_actual_path_and_suspect_marks_are_drawn(self):
        with tempfile.TemporaryDirectory() as directory:
            svg = Path(directory) / 'route.svg'
            image = Path(directory) / 'route.png'
            args = ['--game', 'bdsp', '--map', 'room', '--start', 'start', '--goal', 'goal', '--revision', 'f' * 40,
                    '--actual', '0,1 0,2 2,2', '--mark', '1,1=wall on the map', '--mark', '2,0',
                    '--svg', str(svg), '--png', str(image)]
            with mock.patch('pokesim.cli.route.load_pinned_map', return_value=self.view()), redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            root = ElementTree.fromstring(svg.read_text())
            ns = '{http://www.w3.org/2000/svg}'
            lines = {line.attrib['stroke']: line.attrib['points'] for line in root.iter(ns + 'polyline')}
            # Tile centres at 16 px: the walked line keeps its corners, dashed beside the solid plan.
            self.assertEqual(lines['#1f6fd1'], '8.0,24.0 8.0,40.0 40.0,40.0')
            self.assertIn('#e0661b', lines)
            dashed = [line for line in root.iter(ns + 'polyline') if line.attrib.get('stroke-dasharray')]
            self.assertEqual([line.attrib['stroke'] for line in dashed], ['#1f6fd1'])
            text = ' '.join(root.itertext())
            self.assertIn('[1] (1, 1): wall on the map', text)
            self.assertIn('suspect tile', text)
            self.assertIn('walked', text)
            png = Image.read(str(image))
            self.assertEqual(png.get(24, 17)[:3], (0xd6, 0x28, 0x39))   # suspect box edge on (1, 1)
            self.assertEqual(png.get(8, 40)[:3], (0x1f, 0x6f, 0xd1))    # walked corner (0, 2)

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
