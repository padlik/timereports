#!/bin/env python#

import xlutils
from gdreport import SpreadsheetProvider
from gdspreadsheet import GSpreadSheet
from reports import inject
from reports.injectors import SQLDb


class GDSpreadsheetProvider(SpreadsheetProvider):
    def __init__(self, google_spreadsheet_id):
        self._sheet = self.__init_provider(google_spreadsheet_id)

    @staticmethod
    def __init_provider(ssid):
        db = inject.instance(SQLDb)
        s_sql = 'SELECT param, value FROM oauthdata'
        c = db.cursor()
        c.execute(s_sql)
        params = {p: v for p, v in c.fetchall()}
        return GSpreadSheet(ssid, params)

    def set_cell(self, cell_range, value):
        tm = xlutils.cell2tuple(cell_range)
        col = xlutils.abc2col(tm[0])
        row = tm[1]
        self._sheet.set_cell(row, col, value)

    def set_range(self, xlrange, value):
        self._sheet.set_range(xlrange, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._sheet:
            self._sheet.flush()

    def __del__(self):
        if self._sheet:
            self._sheet.flush()
