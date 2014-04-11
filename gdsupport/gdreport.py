#!/usr/bin/env python

import re
import collections

TEMPLATE = {
    'minsk_target': {'type': 'cell', 'range': 'B1'},
    'ua_target': {'type': 'cell', 'range': 'B2'},
    'update_date': {'type': 'cell', 'range': 'H1'},
    'update_time': {'type': 'cell', 'range': 'H2'},
    'hour_report': {'type': 'range', 'range': 'A4:H4', 'dynamic': 'rows'}
}

__ALFA__ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


class GDReportError(Exception):
    pass


def abc2col(abc_col):
    """
      Converts AA columns style addressing to column number
    """
    idx = __ALFA__
    col = 0
    mul = 0
    for s in abc_col:
        col = idx.index(s) + col * mul + 1
        mul += len(idx)
    return col


def col2abc(num_col):
    """
      reverts the one done by abc2col
    """
    if not type(num_col) == int:
        raise GDReportError('Column number must be int')
    if num_col < 1:
        raise GDReportError('Column number should start from 1 ')
    if num_col < len(__ALFA__):
        return __ALFA__[num_col - 1]
    else:
        return __ALFA__[num_col / len(__ALFA__) - 1] + __ALFA__[num_col % len(__ALFA__) - 1]


#TODO: Rewrite in abcmeta
class ReportTemplate(collections.MutableMapping):
    _REG_ = re.compile('^([a-zA-Z]+)([1-9]+)', re.IGNORECASE)

    class Cell(object):
        def __init__(self, key, cell_range):
            self._name = key
            self._range = cell_range

        @property
        def name(self):
            return self._name

        @property
        def range(self):
            return self._range

    class Range(Cell):
        def __init__(self, name, init_range, **kwargs):
            super(ReportTemplate.Range, self).__init__(name, init_range)
            self._dynamic = kwargs.get('dynamic')
            if self._dynamic and not self._dynamic in ['rows', 'cols']:
                raise GDReportError('Dynamic attribute should be in %' % str(['rows', 'cols']))

        @property
        def dynamic(self):
            return self._dynamic

        @staticmethod
        def _next_col(crange):
            sr = crange.split(":")
            if len(sr) == 1:
                m = ReportTemplate._REG_.match(sr)
                result = col2abc(abc2col(m.groups()[0]) + 1) + m.groups()[1]
            else:
                hm = ReportTemplate._REG_.match(sr[0])
                tm = ReportTemplate._REG_.match(sr[1])
                head = col2abc(abc2col(tm.groups()[0]) + 1) + hm.groups()[1]
                tail = col2abc(2 * abc2col(tm.groups()[0]) - abc2col(hm.groups()[0]) + 1) + tm.groups()[1]
                result = ":".join([head, tail])
            return result

        @staticmethod
        def _next_row(rrange):
            sr = rrange.split(":")
            if len(sr) == 1:
                m = ReportTemplate._REG_.match(sr)
                result = m.groups()[0] + str(int(m.groups()[1]) + 1)
            else:
                hm = ReportTemplate._REG_.match(sr[0])
                tm = ReportTemplate._REG_.match(sr[1])
                head = hm.groups()[0] + str(int(tm.groups()[1]) + 1)
                tail = tm.groups()[0] + str(2 * int(tm.groups()[1]) - int(hm.groups()[1]) + 1)
                result = ":".join([head, tail])
            return result

        def next(self):
            new_range = self
            if self.dynamic == 'rows':
                new_range = ReportTemplate.Range(self._name, self._next_row(self._range),
                                                 **{'dynamic': self._dynamic})
            elif self.dynamic == 'cols':
                new_range = ReportTemplate.Range(self._name, self._next_col(self._range),
                                                 **{'dynamic': self._dynamic})
            return new_range

    def __init__(self, template=None):
        self._template = template or {}
        self._report = {}
        self._generators = {'cell': self._generate_cell, 'range': self._generate_range}

    @staticmethod
    def __validate_type(item_type):
        if not item_type in ['cell', 'range']:
            raise GDReportError('Expecting cell or range type items')
        return item_type

    @classmethod
    def __validate_range(cls, item_range):
        if not type(item_range) == str:
            raise GDReportError('Expecting range as string type')

        refs = item_range.split(':')
        if len(refs) > 2:
            raise GDReportError('Wrong reference %s (seems more than one semicolon) ' % item_range)

        for ref in refs:
            if not cls._REG_.match(ref):
                raise GDReportError('Reference %s (%s) is not valid' % (item_range, ref))
        return item_range

    def _generate_cell(self, name, **kwargs):
        return self.Cell(name, self.__validate_range(kwargs.get('range')))

    def _generate_range(self, name, **kwargs):
        return self.Range(name, kwargs.get('range'), **kwargs)

    def _parse_template(self):
        for name, value in self._template.iteritems():
            self._report[name] = self._generators[self.__validate_type(value.get('type'))](name, **value)


    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, template):
        self._template = template
        self._parse_template()

    def __getitem__(self, item):
        return self._report[item]

    def __iter__(self):
        for key in self._report.keys():
            yield key

    def __len__(self):
        return len(self._report)

    def __setitem__(self, key, value):
        raise GDReportError('Not supported')

    def __delitem__(self, key):
        raise GDReportError('Not supported')


class SpreadsheetProvider(object):
    def set_cell(self, cell_range, value):
        pass

    def set_range(self, xlrange, value):
        pass


class DataProvider(object):
    def get_value(self, key):
        """
         Simple value for cell
        :rtype : string
        """
        pass

    def get_range_value(self, key):
        """
         list of lists for ROWS in a range
         :rtype : iterable
        """
        pass


class ReportBuilder(object):
    def __init__(self, dataprovider=None, spreadsheet=None, template=None):
        self._dp = dataprovider
        self._ss = spreadsheet
        self._tt = template

    def execute(self):
        for name, value in self._tt.iteritems():
            if isinstance(value, ReportTemplate.Cell):
                self._process_cell(value)
            else:
                self._process_range(value)

    def _process_cell(self, cell):
        self._ss.set_cell(cell.range, self._dp.get_value(cell.name))

    def _process_range(self, range):
        if range.dynamic:
            r = range
            for v in self._dp.get_range_value(range.name):
                self._ss.set_range(r.range, v)
                r = r.next()
        else:
            self._ss.set_range(range.range, self._dp.get_range_value(range.name))

    @property
    def spreadsheet(self):
        return self._ss

    @spreadsheet.setter
    def spreadsheet(self, spreadsheet):
        self._ss = spreadsheet

    @property
    def datasource(self):
        return self._dp

    @datasource.setter
    def datasource(self, datasource):
        self._dp = datasource

    @property
    def template(self):
        return self._tt

    @template.setter
    def template(self, template):
        self._tt = template


if __name__ == '__main__':
    report = ReportTemplate()
    builder = ReportBuilder()
    data = DataProvider()
    sheet = SpreadsheetProvider()
    report.template = TEMPLATE
    builder.template = report
    builder.datasource = data
    builder.spreadsheet = sheet
    builder.execute()