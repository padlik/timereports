#!/bin/env python
import MySQLdb

import gdata.spreadsheets.client
import gdata.spreadsheets.data
import gdata.gauth


class GSpreadsheetHelper(object):
    _s_magic = 'od6'  # first sheet magic name in Google
    _scope = 'https://spreadsheets.google.com/feeds/'
    _ua = 'sugarreport.app'

    def __init__(self, sheet_id, oauth2params):
        self.token = gdata.gauth.OAuth2Token(client_id=oauth2params['client_id'],
                                             client_secret=oauth2params['client_sec'],
                                             scope=self._scope, user_agent=self._ua,
                                             access_token=oauth2params['client_at'],
                                             refresh_token=oauth2params['client_rt'])
        self.client = gdata.spreadsheets.client.SpreadsheetsClient()
        self.token.authorize(self.client)
        self.sheet_id = sheet_id

    def update_cell(self, row, col, value, immediate=True):
        cell = self.client.get_cell(self.sheet_id, self._s_magic, row, col)
        cell.cell.input_value = str(value)
        self.client.update(cell, force=immediate)

    def get_cell(self, row, col):
        cell = self.client.get_cell(self.sheet_id, self._s_magic, row, col)
        return cell.cell.input_value

    def get_range(self, srange):
        query = gdata.spreadsheets.client.CellQuery(range=srange, return_empty='true')
        cells = self.client.GetCells(self.sheet_id, 'od6', q=query)
        n_of_cols = int(cells.entry[-1].cell.col)
        rows = 0
        matrix = []
        while True:
            sl = cells.entry[0 + rows * n_of_cols:n_of_cols + rows * n_of_cols]
            matrix.append([val.cell.input_value for val in sl])
            rows += 1
            if not cells.entry[0 + rows * n_of_cols:n_of_cols + rows * n_of_cols]:
                break
        return matrix

    def set_range(self, srange, matrix, clear_out=False, immediate=True):
        query = gdata.spreadsheets.client.CellQuery(range=srange, return_empty='true')
        cells = self.client.GetCells(self.sheet_id, 'od6', q=query)
        obj_data = gdata.spreadsheets.data
        batch = obj_data.BuildBatchCellsUpdate(self.sheet_id, 'od6')
        for cell in cells.entry:
            try:
                cell.cell.input_value = matrix[int(cell.cell.row) - 1][int(cell.cell.col) - 1]
            except IndexError:
                if clear_out:
                    cell.cell.input_value = ''
            batch.add_batch_entry(cell, cell.id.text, batch_id_string=cell.title.text, operation_string='update')

        self.client.batch(batch, force=immediate)


if __name__ == '__main__':
    db = MySQLdb.connect(user='root', passwd='pass', db='time_reports', host='localhost', charset='utf8')
    s_sql = 'select param, value from oauthdata'
    c = db.cursor()
    c.execute(s_sql)
    params = dict([(p, v) for p, v in c.fetchall()])

    st = '0Av6KMa_AP8_sdDdMMFgzb2V2V0laamdqa0N2WFc0R1E'
    sheet = GSpreadsheetHelper(st, params)
    print sheet.get_cell(1, 9)
    r = sheet.get_range("A1:I3")
    print r
    r[0][1] = '160'
    r[1][1] = '160'
    r[2][1] = 'username!'
    sheet.set_range("A1:I3", r)
    r = sheet.get_range("A1:I3")
    print r
    sheet.set_range("A1:I3", [], clear_out=True)
    print sheet.get_range("A1:I3")
    sheet.set_range("A1:I3", r)
    print sheet.get_range("A1:I3")




