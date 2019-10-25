# -*- coding:utf-8 -*-

"""
Datadog logs logging handler
"""

__author__ = "Katsuya Iwayama <iwayamak@matsubabreak.com>"
__status__ = "beta"
__version__ = "0.1.0"
__date__ = "01 Sep 2019"

import logging


class DictFormatter(logging.Formatter):
    """
    Dict formatter for Datadog logs logging handler
    """

    def format(self, record):
        ret = {}
        for attr, value in record.__dict__.items():
            if attr == 'asctime':
                value = self.formatTime(record)
            if attr == 'exc_info' and value is not None:
                value = self.formatException(value)
            if attr == 'stack_info' and value is not None:
                value = self.formatStack(value)
            ret[attr] = value
        return ret
