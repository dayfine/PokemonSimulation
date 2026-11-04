"""Checks that the package imports, so CI fails early on a broken layout."""

import unittest

import pokesim


class PackageTest(unittest.TestCase):
    def test_imports_with_a_version(self):
        self.assertRegex(pokesim.__version__, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
