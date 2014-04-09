#!/bin/env python
import MySQLdb

import gdata.spreadsheets.client
import gdata.spreadsheets.data
import gdata.gauth


class GSpreadSheetError(Exception):
    pass


def base36encode(number, alphabet='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    """Converts an integer to a base36 string."""
    if not isinstance(number, (int, long)):
        raise TypeError('number must be an integer')

    base36 = ''
    sign = ''

    if number < 0:
        sign = '-'
        number = -number

    if 0 <= number < len(alphabet):
        return sign + alphabet[number]

    while number != 0:
        number, i = divmod(number, len(alphabet))
        base36 = alphabet[i] + base36

    return sign + base36


def id2gid(worksheet_id):
    return int(worksheet_id, 36) ^ 31578


def gid2id(worksheet_id):
    return base36encode(int(worksheet_id ^ 31578))


__ALFA__ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def abc2col(abc_col):
    """
      Converts AA columns style addressing to column number as per Google Sheet
    """
    idx = __ALFA__
    col = 0
    mul = 0
    for s in abc_col:
        col = idx.index(s) + col * mul + 1
        mul += len(idx)
    return col


def col2abc(col):
    """
      reverts the one done by abc2col
    """
    if not type(col) == int:
        raise GSpreadSheetError('Column number must be int')
    if col < 1:
        raise GSpreadSheetError('Column number shold start from 1 ')
    return __ALFA__[col / len(__ALFA__) - 1] + __ALFA__[col % len(__ALFA__) - 1]


__APP__ = 'sugarreport.app'
__SCOPE__ = 'https://spreadsheets.google.com/feeds/'


class GSpreadSheet(object):
    _scope = __SCOPE__
    _ua = __APP__

    def __init__(self, sheet_id, oauth2params, worksheet=0):
        self.token = gdata.gauth.OAuth2Token(client_id=oauth2params['client_id'],
                                             client_secret=oauth2params['client_sec'],
                                             scope=self._scope, user_agent=self._ua,
                                             access_token=oauth2params['client_at'],
                                             refresh_token=oauth2params['client_rt'])
        self.client = gdata.spreadsheets.client.SpreadsheetsClient()
        self.token.authorize(self.client)
        self.sheet_id = sheet_id
        self._s_magic = gid2id(worksheet).lower()
        self.w_entry = self.client.GetWorksheet(self.sheet_id, self._s_magic)

    def update_cell(self, row, col, value, immediate=True):
        cell = self.client.get_cell(self.sheet_id, self._s_magic, row, col)
        cell.cell.input_value = str(value)
        self.client.update(cell, force=immediate)

    def get_cell(self, row, col):
        cell = self.client.get_cell(self.sheet_id, self._s_magic, row, col)
        return cell.cell.input_value

    def get_range(self, srange):
        query = gdata.spreadsheets.client.CellQuery(range=srange, return_empty='true')
        cells = self.client.GetCells(self.sheet_id, self._s_magic, q=query)
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
        cells = self.client.GetCells(self.sheet_id, self._s_magic, q=query)
        obj_data = gdata.spreadsheets.data
        batch = obj_data.BuildBatchCellsUpdate(self.sheet_id, self._s_magic)
        for cell in cells.entry:
            try:
                cell.cell.input_value = matrix[int(cell.cell.row) - 1][int(cell.cell.col) - 1]
            except IndexError:
                if clear_out:
                    cell.cell.input_value = ''
            batch.add_batch_entry(cell, cell.id.text, batch_id_string=cell.title.text, operation_string='update')

        self.client.batch(batch, force=immediate)

    @property
    def dimension(self):
        return int(self.w_entry.col_count.text), int(self.w_entry.row_count.text)

    @dimension.setter
    def dimension(self, dim):
        self.w_entry.col_count.text = str(dim[0])
        self.w_entry.row_count.text = str(dim[1])
        self.client.update(self.w_entry)

    @property
    def cols(self):
        return self.dimension[0]

    @property
    def rows(self):
        return self.dimension[1]

    @property
    def sheet(self):
        return id2gid(self._s_magic)

    @sheet.setter
    def sheet(self, sheet):
        self._s_magic = gid2id(sheet).lower()


if __name__ == '__main__':
    db = MySQLdb.connect(user='root', passwd='pass', db='time_reports', host='localhost', charset='utf8')
    s_sql = 'select param, value from oauthdata'
    c = db.cursor()
    c.execute(s_sql)
    params = {p: v for p, v in c.fetchall()}

    st = '0Av6KMa_AP8_sdDdMMFgzb2V2V0laamdqa0N2WFc0R1E'
    sheet = GSpreadSheet(st, params)
    print sheet.dimension
    sheet.dimension = (10, 50)
    print sheet.sheet
    print sheet.dimension
    print sheet.get_cell(1, 9)
    r = sheet.get_range("A1:I3")
    print r
    # r[0][1] = '160'
    # r[1][1] = '160'
    # r[2][1] = 'username!'
    # sheet.set_range("A1:M3", r)
    r = sheet.get_range("A1:M3")
    print r
    sheet.set_range("A1:M3", [], clear_out=True)
    print sheet.get_range("A1:M3")
    sheet.set_range("A1:M3", r)
    print sheet.get_range("A1:M3")




