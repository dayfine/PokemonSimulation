"""A person's walk path: legs from their start tile.

A path is a list of legs `[direction, tiles]`, direction north, east, south or
west, walked in order from the person's own coord. It returns to that coord
and starts over, unless its last leg has a third element, "stuck": the person
stops on the tile it ends on and stays there.
"""

STEPS = {'north': (0, -1), 'east': (1, 0), 'south': (0, 1), 'west': (-1, 0)}
STUCK = 'stuck'


def path_tiles(start, legs):
    """Every tile on the path, in walking order: `start`, then one tile per
    step of each leg."""
    x, y = start
    tiles = [(x, y)]
    for leg in legs:
        dx, dy = STEPS[leg[0]]
        for _ in range(leg[1]):
            x, y = x + dx, y + dy
            tiles.append((x, y))
    return tiles


def stuck(legs):
    """Whether the person stops for good at the end of the path."""
    return bool(legs) and len(legs[-1]) == 3


def path_error(start, legs, width, height):
    """Why `legs` is no valid path from `start` on a `width` x `height` map, or None."""
    if not isinstance(legs, list) or not legs:
        return 'a path is a nonempty list of legs'
    for index, leg in enumerate(legs):
        if not isinstance(leg, list) or len(leg) not in (2, 3) or leg[0] not in STEPS:
            return 'a leg is [direction, tiles] or [direction, tiles, "stuck"]'
        if type(leg[1]) is not int or leg[1] < 1:
            return 'a leg walks at least one tile'
        if len(leg) == 3 and (leg[2] != STUCK or index != len(legs) - 1):
            return 'only the last leg may be "stuck"'
        if index and leg[0] == legs[index - 1][0]:
            return 'consecutive legs go different ways'
    tiles = path_tiles(start, legs)
    if not all(0 <= x < width and 0 <= y < height for x, y in tiles):
        return 'a path leaves the map'
    if not stuck(legs) and tiles[-1] != tuple(start):
        return 'a path returns to its start unless stuck'
    return None
