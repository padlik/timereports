#!/bin/env python

import re

__ALFA__ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
__REG__ = re.compile('^([a-zA-Z]+)([1-9][0-9]*)', re.IGNORECASE)


def cell2tuple(cell):
    m = __REG__.match(cell)
    if m:
        return m.groups()[0], m.groups()[1]
    else:
        raise ValueError('Cell %s is invalid' % cell)


def abc2col(abc_col):
    """
      Converts AA columns style addressing to column number
    """
    idx = __ALFA__
    col = 0
    mul = 0
    for s in str.upper(abc_col):
        col = idx.index(s) + col * mul + 1
        mul += len(idx)
    return col


def col2abc(num_col):
    """
      reverts the one done by abc2col
    """
    if not type(num_col) == int:
        raise ValueError('Column number must be int')
    if num_col < 1:
        raise ValueError('Column number should start from 1 ')
    if num_col < len(__ALFA__):
        return __ALFA__[num_col - 1]
    else:
        return __ALFA__[num_col / len(__ALFA__) - 1] + __ALFA__[num_col % len(__ALFA__) - 1]


def range_dimension(xlrange):
    s_range = xlrange.split(':')
    nofcols = (1, 1)
    if len(s_range) != 1:
        hcell = cell2tuple(s_range[0])
        tcell = cell2tuple(s_range[1])
        head_col = abc2col(hcell[0])
        head_row = int(hcell[1])
        tail_col = abc2col(tcell[0])
        tail_row = int(tcell[1])
        nofcols = (tail_col - head_col + 1, tail_row - head_row + 1)
    return nofcols

