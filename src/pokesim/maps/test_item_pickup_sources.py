"""Fixed-reward decoders fail closed instead of interpreting labels as item names."""

import struct
import unittest

from .item_pickup_sources import diamond_events, diamond_pickups, frlg_pickups, frlg_starter, platinum_pickups


class SourcePickupTest(unittest.TestCase):
    def test_frlg_reads_operands_aliases_and_declared_default_not_the_label(self):
        scripts = ('Misleading_ItemPotion::\nAlias::\n finditem ITEM_ESCAPE_ROPE\n end\n'
                   'Two::\n finditem ITEM_POTION, 2\n end\n'
                   'Conditional::\n goto_if_eq VAR_X, 1, Other\n finditem ITEM_POTION\n end\n'
                   'Variable::\n finditem VAR_ITEM\n end\n')
        result = frlg_pickups(scripts, '.macro finditem item:req, amount=1')
        self.assertEqual(result, {'Misleading_ItemPotion': dict(item='escape_rope', quantity=1),
                                 'Alias': dict(item='escape_rope', quantity=1),
                                 'Two': dict(item='potion', quantity=2)})
        self.assertEqual(frlg_pickups('A::\nfinditem ITEM_POTION\nend', '.macro finditem item:req, amount=3')['A']['quantity'], 3)
        with self.assertRaises(ValueError):
            frlg_pickups(scripts, '.macro unknown')

    def test_starter_choice_is_an_interaction_not_a_granted_item_or_pokemon(self):
        scripts = ('Ball::\nsetvar PLAYER_STARTER_SPECIES, SPECIES_SQUIRTLE\n'
                   'goto_if_eq VAR_SCENE, 2, ConfirmStarterChoice\nend\n')
        self.assertEqual(frlg_starter('Ball', scripts),
                         dict(interaction=dict(kind='starter_choice', species='squirtle')))
        self.assertNotIn('item', frlg_starter('Ball', scripts))
        self.assertEqual(frlg_starter('Missing', scripts)['pickup']['status'], 'unresolved')

    def test_platinum_uses_its_entry_order_and_actual_operands(self):
        scripts = (' ScriptEntry Misleading_Potion\n ScriptEntry Unknown\n ScriptEntryEnd\n'
                   'Misleading_Potion:\nSetVar VAR_0x8008, ITEM_LUCK_INCENSE\n'
                   'SetVar VAR_0x8009, 1\nGoTo VisibleItems_TryGiveItem\nEnd\nUnknown:\nEnd\n')
        self.assertEqual(platinum_pickups(scripts), {7000: dict(item='luck_incense', quantity=1)})

    @staticmethod
    def diamond_archive():
        # Two 20-byte fixed entries and one 20-byte conditional/unsupported entry.
        start, tail = 18, 78
        pointers = b''.join(struct.pack('<I', start + 20 * i - 4 * i - 4) for i in range(3))
        pointers += struct.pack('<I', tail - 16)
        entries = b''
        for i, item in enumerate((17, 78, 17)):
            entries += struct.pack('<7HiH', 0x28 if i != 2 else 0x19, 0x8008, item,
                                   0x28, 0x8009, 2 if i == 0 else 1, 0x16,
                                   tail - (start + i * 20 + 18), 2)
        return pointers + b'\x13\xfd' + entries + b'\0' * 24

    def test_diamond_constants_counts_and_unsupported_script_form(self):
        raw = self.diamond_archive()
        constants = '#define ITEM_POTION 17\n#define ITEM_ESCAPE_ROPE 78\n'
        self.assertEqual(diamond_pickups(raw, constants),
                         {7000: dict(item='potion', quantity=2), 7001: dict(item='escape_rope', quantity=1)})
        for broken in (raw[:5], b'\xff' * len(raw), raw[:18]):
            with self.subTest(raw=broken[:8]), self.assertRaises(ValueError):
                diamond_pickups(broken, constants)
        drift = bytearray(raw)
        struct.pack_into('<H', drift, 18 + 10, 0)
        self.assertNotIn(7000, diamond_pickups(drift, constants))

    def test_diamond_retains_event_id_script_and_collection_flag(self):
        raw = struct.pack('<II', 0, 1) + struct.pack('<14HI', 3, 87, 0, 0, 993, 7012, 0, 0, 0, 0, 0, 0, 4, 28, 0)
        self.assertEqual(diamond_events(raw), [dict(index=0, id=3, script=7012, x=4, y=28, hide_flag='flag 993')])
        with self.assertRaisesRegex(ValueError, 'truncated'):
            diamond_events(raw[:-1])


if __name__ == '__main__':
    unittest.main()
