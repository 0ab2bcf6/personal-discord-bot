#!/usr/bin/env python3
"""
Basic __init__.py file.
This file contains a basic description of your whole project. General
parameters for the any python-project can be set here.
Every python-module must contain a '__init__.py' file.
"""


def add(number1: float, number2: float) -> float:
    """
    This is a basic function for demonstration. Any functions defined inside
    __init__.py can be imported directly from this module by:
    from your_project import add

    Parameters
    ---------
    number1 :
        first number to be added
    number 2 :
        second number to be added

    Returns
    -------
    Sum of number1 and number2
    """
    return number1 + number2
