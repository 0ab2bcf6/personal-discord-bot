#!/usr/bin/env python3
"""
This file contains the unit-tests for __init__.py. The files containing unit
tests are usually named after the the file containing the tested functions and
classes plus the prefix 'test_'.

All unit-test functions must begin with the prefix 'test_' and must contain an
assert statement. The 'tests' directory should not include a '__init__.py'
file.
"""
from dwarfbot import add


def test_add() -> None:
    """
    Test for the add function.
    """
    result = add(1, 2)
    assert result == 3
