#!/bin/env python#

from gdreport import SpreadsheetProvider
from injectors import SQLDb
import inject
from gdspreadsheet import GSpreadSheet
import re
import xlutils


class GDSpreadsheetProvider(SpreadsheetProvider):

    def __init__(self, google_spreadsheet_id):
        self._sheet = self.__init_provider(google_spreadsheet_id)

    @staticmethod
    def __init_provider(id):
        db = inject.instance(SQLDb)
        s_sql = 'select param, value from oauthdata'
        c = db.cursor()
        c.execute(s_sql)
        params = {p: v for p, v in c.fetchall()}
        return GSpreadSheet(id, params)

    def set_cell(self, cell_range, value):
        tm = xlutils.cell2tuple(cell_range)
        col = xlutils.abc2col(tm[0])
        row = tm[1]
        self._sheet.set_cell(row, col, value)

    def set_range(self, xlrange, value):
        self._sheet.set_range(xlrange, value)

