#!/usr/bin/env python

import re

# TEMPLATE = {
#     'minsk_target':{'type': 'cell',  'range': 'B1'},
#     'ua_target':   {'type': 'cell',  'range': 'B2'},
#     'update_date': {'type': 'cell',  'range': 'H1'},
#     'update_time': {'type': 'cell',  'range': 'H2'},
#     'hour_report': {'type': 'range', 'range': 'A4:H4', 'dynamic': 'rows'}
# }


class GDReportError(Exception):
    pass


class ReportTemplateParser(object):

    def __init__(self):
        self._template = {}

    @staticmethod
    def __validate_type(item_type):
        if not item_type in ['cell', 'range']:
            raise GDReportError('Expecting cell or range type items')
        return item_type

    @staticmethod
    def __validate_range(item_range):
        if not type(item_range) == str:
            raise GDReportError('Expecting range as string type')

        refs = item_range.split(':')
        if len(refs) > 2:
            raise GDReportError('Wrong reference %s (seems more than one semicolon) ' % item_range)

        r = re.compile('^[a-zA-Z]+[1-9]+', re.IGNORECASE)
        for ref in refs:
            if not r.match(ref):
                raise GDReportError('Reference %s (%s) is not valid' % (item_range, ref))
        return item_range

    def add_item(self, key, **kwargs):
        args = kwargs
        item_type = self.__validate_type(args.pop('type'))
        item_range = self.__validate_range(args.pop('range'))

# class SpreadsheetReport(object):
#     def __init__(self, template, sheet_provider=None, data_source=None):
