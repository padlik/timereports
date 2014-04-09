#!/usr/bin/env python

# TEMPLATE = {
#     'minsk_target':{'type': 'cell',  'range': 'B1', 'check': 'False'},
#     'ua_target':   {'type': 'cell',  'range': 'B2', 'check': 'False'},
#     'update_date': {'type': 'cell',  'range': 'H1', 'check': 'False'},
#     'update_time': {'type': 'cell',  'range': 'H2', 'check': 'False'},
#     'hour_report': {'type': 'range', 'range': 'A4:H4', 'dynamic': 'rows', 'crop': 'False'}
# }


class GDReportError(Exception):
    pass


def abc2col(abc_col):
    """ Converts AA columns style addressing to column number as per Google Sheet """
    idx = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    col = 0
    mul = 0
    for s in abc_col:
        col = idx.index(s) + mul + 1
        mul += len(idx)
    return col


class ReportTemplate(object):
    def __init__(self):
        self._template = {}

    @staticmethod
    def __check_type(item_type):
        if not item_type in ['cell', 'range']:
            raise GDReportError('Expecting cell or range type items')
        return item_type

    @staticmethod
    def __check_range(item_range):
        if not type(item_range) == str:
            raise GDReportError('Expecting range as string type')
        # r = re.compile('^[a-zA-Z]+\d+', re.IGNORECASE)

    def add_item(self, key, **kwargs):
        item_type = self.__check_type(kwargs.get('type'))
        item_range = kwargs.get('range')

# class SpreadsheetReport(object):
#     def __init__(self, template, sheet_provider=None, data_source=None):
