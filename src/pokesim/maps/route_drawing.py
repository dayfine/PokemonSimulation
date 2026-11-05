"""Draw a computed local route with runtime glyphs and closed-side boundaries."""

from pokesim.grid.geometry import Direction
from pokesim.grid.maps import render
from pokesim.grid.maps.render import Overlay
from pokesim.grid.maps.schema import MapImage
from .runtime_symbols import CLOSED_SIDES


def ascii_route(view, path):
    rows = [list(row) for row in view.data['tiles']]
    for tile in view.occupied:
        rows[tile.y][tile.x] = 'O'
    for tile in view.scene_tiles:
        rows[tile.y][tile.x] = '?'
    places = path.places()
    for place in places:
        rows[place.tile.y][place.tile.x] = '*'
    first, last = places[0].tile, places[-1].tile
    rows[first.y][first.x] = '@'
    rows[last.y][last.x] = 'X'
    return '\n'.join(''.join(row) for row in rows) + '\n'


def route_image(view, path, tile_px=16):
    if tile_px < 4:
        raise ValueError('tile size must be at least 4 pixels')
    image = render.plain_image(view.map_file.grid, tile_px)
    overlay = Overlay(legs=[[place.tile for place in path.places()]],
                      regions=[view.occupied, view.scene_tiles])
    render.draw(image, MapImage('', 0, 0, tile_px), overlay)
    for y, row in enumerate(view.data['tiles']):
        for x, glyph in enumerate(row):
            side = CLOSED_SIDES.get(glyph)
            if side is None:
                continue
            x0, y0 = x * tile_px, y * tile_px
            x1, y1 = x0 + tile_px, y0 + tile_px
            if side is Direction.NORTH: y1 = y0 + 2
            if side is Direction.SOUTH: y0 = y1 - 2
            if side is Direction.WEST: x1 = x0 + 2
            if side is Direction.EAST: x0 = x1 - 2
            image.fill_rect(x0, y0, x1, y1, (0, 0, 0, 255))
    return image
