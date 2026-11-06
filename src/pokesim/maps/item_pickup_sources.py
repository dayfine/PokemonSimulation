"""Resolve fixed item pickups from source instructions, never sprite/script names.

Readers deliberately cover only fixed finditem / visible-item scripts. An
unknown, conditional or variable reward stays unresolved instead of becoming
an inventory grant. Source revisions and file hashes are recorded by item_identity.
"""

import re
import struct


def unresolved(reason):
    return {'pickup': {'status': 'unresolved', 'reason': reason}}


def _bodies(text, double_colon=False):
    pattern = r'^(\w+)::\s*$' if double_colon else r'^(\w+):\s*$'
    labels = list(re.finditer(pattern, text, re.M))
    result, aliases = {}, []
    for index, label in enumerate(labels):
        end = labels[index + 1].start() if index + 1 < len(labels) else len(text)
        body = text[label.end():end]
        aliases.append(label.group(1))
        if body.strip():
            for name in aliases:
                result[name] = body
            aliases = []
    return result


def frlg_pickups(scripts, macros):
    """Read only straight-line finditem/end bodies and its declared default count."""
    default = re.search(r'\.macro\s+finditem\s+item:req,\s*amount=(\d+)', macros)
    if not default:
        raise ValueError('unrecognized FRLG finditem macro default')
    result = {}
    for label, body in _bodies(scripts, double_colon=True).items():
        instructions = '\n'.join(line.split('@', 1)[0].strip() for line in body.splitlines()
                                 if line.split('@', 1)[0].strip())
        match = re.fullmatch(r'finditem\s+(ITEM_\w+)(?:,\s*(\d+))?\s*\nend', instructions)
        if match:
            quantity = int(match.group(2) or default.group(1))
            if quantity > 0:
                result[label] = dict(item=match.group(1)[5:].lower(), quantity=quantity)
    return result


def frlg_starter(script, map_scripts):
    """Identify starter-selection semantics without asserting a Pokémon was granted."""
    body = _bodies(map_scripts, double_colon=True).get(script, '')
    choices = re.findall(r'^\s*setvar\s+PLAYER_STARTER_SPECIES,\s*SPECIES_(\w+)\s*$', body, re.M)
    if len(choices) == 1 and 'ConfirmStarterChoice' in body:
        return {'interaction': {'kind': 'starter_choice', 'species': choices[0].lower()}}
    return unresolved('script is not a supported fixed item pickup')


def platinum_pickups(scripts):
    """Index Platinum's own ScriptEntry list; its numeric IDs differ from Diamond."""
    labels = re.findall(r'^\s*ScriptEntry\s+(\w+)\s*$', scripts, re.M)
    bodies = _bodies(scripts)
    result = {}
    for index, label in enumerate(labels):
        lines = [line.strip() for line in bodies.get(label, '').splitlines() if line.strip()]
        match = re.fullmatch(r'SetVar VAR_0x8008, (ITEM_\w+)\nSetVar VAR_0x8009, (\d+)\n'
                             r'GoTo VisibleItems_TryGiveItem\nEnd', '\n'.join(lines))
        if match and int(match.group(2)) > 0:
            result[7000 + index] = dict(item=match.group(1)[5:].lower(), quantity=int(match.group(2)))
    return result


def diamond_pickups(archive, constants):
    """Decode Diamond archive 370: 7000-based entries, SetVar item/count, shared jump.

    Source: unk_02038C78.s selects archive 0x172 and subtracts 0x1b58;
    scrcmd.c defines opcode 0x28. Accept only the fixed immediate form and
    a forward in-bounds shared tail. Do not execute arbitrary script bytecode.
    """
    if len(archive) < 6:
        raise ValueError('truncated Diamond visible-item archive')
    first = struct.unpack_from('<I', archive)[0] + 4
    table_end = first - 2
    if table_end < 4 or table_end % 4 or first > len(archive) or archive[table_end:first] != b'\x13\xfd':
        raise ValueError('invalid Diamond script-entry table')
    names = {}
    for name, value in re.findall(r'^#define\s+(ITEM_\w+)\s+(0x[\da-fA-F]+|\d+)\s*$', constants, re.M):
        names.setdefault(int(value, 0), name[5:].lower())
    result = {}
    shared_offset = table_end - 4
    shared_tail = shared_offset + 4 + struct.unpack_from('<I', archive, shared_offset)[0]
    for index in range(table_end // 4):
        offset = index * 4
        target = offset + 4 + struct.unpack_from('<I', archive, offset)[0]
        if target < first or target + 20 > len(archive):
            raise ValueError('Diamond script pointer outside archive')
        op1, var1, item, op2, var2, quantity, jump = struct.unpack_from('<7H', archive, target)
        delta = struct.unpack_from('<i', archive, target + 14)[0]
        end = struct.unpack_from('<H', archive, target + 18)[0]
        tail = target + 18 + delta
        if ((op1, var1, op2, var2, jump, end) == (0x28, 0x8008, 0x28, 0x8009, 0x16, 2)
                and quantity > 0 and item in names and tail == shared_tail and target + 20 <= tail < len(archive)):
            result[7000 + index] = dict(item=names[item], quantity=quantity)
    return result


def diamond_events(raw):
    """Retain source event IDs, scripts, hidden flags and (world x,z) coordinates."""
    if len(raw) < 4:
        raise ValueError('truncated Diamond event header')
    offset = 4 + 20 * struct.unpack_from('<I', raw)[0]
    if offset + 4 > len(raw):
        raise ValueError('truncated Diamond background events')
    count = struct.unpack_from('<I', raw, offset)[0]
    offset += 4
    if offset + 32 * count > len(raw):
        raise ValueError('truncated Diamond object events')
    result = []
    for index in range(count):
        fields = struct.unpack_from('<14HI', raw, offset + index * 32)
        result.append(dict(index=index, id=fields[0], script=fields[5], x=fields[12], y=fields[13],
                           hide_flag=('flag ' + str(fields[4])) if fields[4] else None))
    return result
