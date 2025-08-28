"""
This module defines some assert functions useful for unit tests.
"""

from typing import List


# pylint tries to enforce snake_case function names by default, but unittest uses camelCase
# for asserts. As we're using unittest we would like to use their conventions and disable
# pylint's check here.
# pylint: disable-next=invalid-name
def assertCodesEqual(string1 : str, string2 : str) -> None:
    """
    Asserts that two multiline strings are equal, ignoring leading and trailing whitespaces in each
    line.

    Parameters
    ----------
    string1 : str
        first string
    string2 : str
        second string

    Raises
    ------
    AssertionError
        In case the strings are not equal.
    """
    lines1 = string1.strip().split('\n')
    lines2 = string2.strip().split('\n')

    if len(lines1) != len(lines2):
        raise AssertionError("Strings have different number of lines", string1, string2)

    for line1, line2 in zip(lines1, lines2):
        if line1.strip() != line2.strip():
            raise AssertionError("String lines are not equal", line1, line2)


# pylint: disable-next=invalid-name
def assertListofCodesEqual(list1: List[str], list2: List[str]) -> None:
    """
    Asserts that two lists of code (aka multuline strings, ignoring leading and trailing
    whitespaces in each line) are equal.

    Parameters
    ----------
    list1 : List[str]
        first list
    list2 : List[str]
        second list

    Raises
    ------
    AssertionError
        In case the strings are not equal.
    """
    if len(list1) != len(list2):
        raise AssertionError("Lists have different lengths", list1, list2)

    for string1, string2 in zip(list1, list2):
        assertCodesEqual(string1.strip(), string2.strip())
