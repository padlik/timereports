#!/usr/bin/env python

import collections

import xlutils
from xlutils import abc2col
from xlutils import cell2tuple
from xlutils import col2abc

TEMPLATE = {'update_date': {'type': 'cell', 'range': 'H1'}, 'update_time': {'type': 'cell', 'range': 'H2'},
            'hour_report': {'type': 'range', 'range': 'A4:I70'}}


class GDReportError(Exception):
    pass


class ReportTemplate(collections.MutableMapping):
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
            if self._dynamic and self._dynamic not in ['rows', 'cols']:
                raise GDReportError('Dynamic attribute should be in %s' % str(['rows', 'cols']))

        @property
        def dynamic(self):
            return self._dynamic

        @staticmethod
        def _next_col(crange):
            sr = crange.split(":")
            if len(sr) == 1:
                m = cell2tuple(crange)
                result = col2abc(abc2col(m[0]) + 1) + m[1]
            else:
                hm = cell2tuple(sr[0])
                tm = cell2tuple(sr[1])
                head = col2abc(abc2col(tm[0]) + 1) + hm[1]
                tail = col2abc(2 * abc2col(tm[0]) - abc2col(hm[0]) + 1) + tm[1]
                result = ":".join([head, tail])
            return result

        @staticmethod
        def _next_row(rrange):
            sr = rrange.split(":")
            if len(sr) == 1:
                m = cell2tuple(sr)
                result = m[0] + str(int(m[1]) + 1)
            else:
                hm = cell2tuple(sr[0])
                tm = cell2tuple(sr[1])
                head = hm[0] + str(int(tm[1]) + 1)
                tail = tm[0] + str(2 * int(tm[1]) - int(hm[1]) + 1)
                result = ":".join([head, tail])
            return result

        def next(self):
            new_range = self
            if self.dynamic == 'rows':
                new_range = ReportTemplate.Range(self._name, self._next_row(self._range), **{'dynamic': self._dynamic})
            elif self.dynamic == 'cols':
                new_range = ReportTemplate.Range(self._name, self._next_col(self._range), **{'dynamic': self._dynamic})
            return new_range

    def __init__(self, template=None):
        self._template = template or {}
        self._report = {}
        self._generators = {'cell': self._generate_cell, 'range': self._generate_range}

    @staticmethod
    def __validate_type(item_type):
        if item_type not in ['cell', 'range']:
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
            if not xlutils.__REG__.match(ref):
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
            if isinstance(value, ReportTemplate.Range):
                self._process_range(value)
            else:
                self._process_cell(value)

    def _process_cell(self, cell):
        self._ss.set_cell(cell.range, self._dp.get_value(cell.name))

    def _process_range(self, xlrange):
        if xlrange.dynamic:
            r = xlrange
            for v in self._dp.get_range_value(xlrange.name):
                self._ss.set_range(r.range, v)
                r = r.next()
        else:
            self._ss.set_range(xlrange.range, self._dp.get_range_value(xlrange.name))

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
