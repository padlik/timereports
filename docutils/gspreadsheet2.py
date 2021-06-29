#!/bin/env python

import gspread

from datasources import SQLDataSource, postgres_creator
from serializers import OAuthData


class GSpreadSheet2(object):
    def __init__(self, worksheet_id, oauth2params, sheet=0):
        credentials = {k[3:]: v for (k, v) in oauth2params.items() if k.startswith("sa_")}
        gc = gspread.service_account_from_dict(credentials)
        self.sheet = gc.open_by_key(worksheet_id).get_worksheet(sheet)

    def set_acell(self, arange, value):
        self.sheet.update(arange, value)

    def set_cell(self, row, col, value):
        self.sheet.update_cell(row, col, value)

    def set_range(self, xlrange, value):
        self.sheet.update(xlrange, value, raw=False)

    def flush(self):
        pass
