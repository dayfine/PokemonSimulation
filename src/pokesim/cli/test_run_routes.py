"""Pictures per checkpoint attempt from the 01.11 console runs (2026-11-08)."""

from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from xml.etree import ElementTree

from pokesim.cli import run_routes
from pokesim.maps.test_run_trace import FLOAROMA_START, TESTDATA, bdsp_maps, read_log
from pokesim.maps.run_trace import parse
from pokesim.png import Image

SVG = '{http://www.w3.org/2000/svg}'


class RunRoutesTest(unittest.TestCase):
    def draw(self, log, marks=()):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        runs = parse(read_log(log), bdsp_maps(), FLOAROMA_START)
        written = run_routes.write_pictures(runs, bdsp_maps(), directory.name, marks)
        return Path(directory.name), written

    def test_failing_run_pictures(self):
        out, written = self.draw('bdsp-0110-0111-fail.log', [('FloaromaTown', (3, 25), 'old man on the map')])
        self.assertEqual([str(path.relative_to(out)) for path in written], [
            'bdsp-20261108-183821/01.10-attempt1-Route204North.svg',
            'bdsp-20261108-183821/01.11-attempt1-FloaromaTown.svg'])
        root = ElementTree.fromstring(written[1].read_text())
        text = ' '.join(root.itertext())
        self.assertIn('01.11 attempt 1: FloaromaTown', text)
        self.assertIn('failed at old_man: old man: nobody answered.', text)
        self.assertIn('2. up_to_the_old_woman (legs, done): walk north 2 (assumed: to the first blocked tile on the map)', text)
        self.assertIn('[1] (3, 25): old man on the map', text)
        # The walks, dashed and numbered in order; the crop starts at x 0, y 22 (16 px tiles).
        walked = [(line.attrib['points']) for line in root.iter(SVG + 'polyline')
                  if line.attrib['stroke'] == '#1f6fd1']
        self.assertEqual(walked, ['184.0,104.0 56.0,104.0', '56.0,104.0 56.0,72.0', '56.0,72.0 40.0,72.0'])
        failed = [g for g in root.iter(SVG + 'g') if g.findtext(SVG + 'title') == 'old man: nobody answered.']
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0].find(SVG + 'circle').attrib['fill'], '#d62839')
        png = Image.read(str(written[1].with_suffix('.png')))
        self.assertEqual((png.width, png.height), (15 * 16, 10 * 16))
        self.assertEqual(png.get(40, 72)[:3], (0xd6, 0x28, 0x39))     # the failure, on (2, 26)

    def test_replan_and_stops_on_route_204(self):
        out, written = self.draw('bdsp-0110-0111-fail.log')
        root = ElementTree.fromstring(written[0].read_text())
        strokes = [line.attrib['stroke'] for line in root.iter(SVG + 'polyline')]
        self.assertEqual(strokes.count('#6d7470'), 1)      # line 2's re-plan
        self.assertEqual(strokes.count('#e0661b'), 6)      # each line's plan
        titles = [g.findtext(SVG + 'title') for g in root.iter(SVG + 'g')]
        self.assertIn('something the map lacks; marked it', titles)
        self.assertIn('blocked after 4 of 9 tiles', titles)

    def test_passing_run_and_index(self):
        out, written = self.draw('bdsp-0111-pass.log')
        self.assertEqual(len(written), 1)
        text = ' '.join(ElementTree.fromstring(written[0].read_text()).itertext())
        self.assertIn('passed', text)
        self.assertNotIn('failed here', text)
        index = (out / 'index.html').read_text()
        self.assertIn('bdsp-20261108-190923/01.11-attempt1-FloaromaTown.svg', index)
        self.assertIn('<span class="passed">passed</span>', index)
        self.assertEqual(json.loads((out / 'trace.json').read_text())[0]['run_id'], 'bdsp-20261108-190923')

    def test_walks_without_a_tile_are_listed(self):
        runs = parse(read_log('bdsp-0111-pass.log'), bdsp_maps())
        with tempfile.TemporaryDirectory() as directory:
            written = run_routes.write_pictures(runs, bdsp_maps(), directory)
            index = (Path(directory) / 'index.html').read_text()
        self.assertEqual(written, [])
        self.assertIn('west_to_the_field_edge (legs, done): walk west 0 (unknown: blocked, from an unknown tile)'
                      ' - not drawn: no known tile', index)

    def test_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            args = [str(TESTDATA / 'bdsp-0111-pass.log'), '-o', directory, '--revision', 'f' * 40,
                    '--start', '01.11=FloaromaTown:11,28', '--mark', 'FloaromaTown:3,25=old man']
            with mock.patch('pokesim.cli.run_routes.PinnedMaps', return_value=bdsp_maps()), \
                    redirect_stdout(io.StringIO()) as output:
                self.assertEqual(run_routes.main(args), 0)
            self.assertIn('1 run(s), 1 picture(s)', output.getvalue())
            self.assertTrue((Path(directory) / 'bdsp-20261108-190923' / '01.11-attempt1-FloaromaTown.png').exists())

    def test_arguments(self):
        self.assertEqual(run_routes.parse_start('01.11=FloaromaTown:11,27/11,28'),
                         ('01.11', [('FloaromaTown', 11, 27), ('FloaromaTown', 11, 28)]))
        self.assertEqual(run_routes.parse_mark('Route 204:-1,5=edge'), ('Route 204', (-1, 5), 'edge'))
        with self.assertRaises(ValueError):
            run_routes.parse_start('01.11=11,28')


if __name__ == '__main__':
    unittest.main()
