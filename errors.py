#!/usr/bin/python

from __future__ import division, print_function, unicode_literals

"""Exceptions for my Twitter search package.
"""


class TwitterError(Exception):
    pass


class APILimitError(TwitterError):
    pass


class NetworkError(TwitterError):
    pass


class WierdError(TwitterError):
    pass
