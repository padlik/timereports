#!/bin/env python
import MySQLdb

import gdata.spreadsheets.client
import gdata.spreadsheets.data
import gdata.gauth

from xlutils import range_dimension


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


__APP__ = 'sugarreport.app'
__SCOPE__ = 'https://spreadsheets.google.com/feeds/'


class GSpreadSheet(object):
    _scope = __SCOPE__
    _ua = __APP__

    def __init__(self, worksheet_id, oauth2params, sheet=0):
        self._token = gdata.gauth.OAuth2Token(client_id=oauth2params['client_id'],
                                              client_secret=oauth2params['client_sec'],
                                              scope=self._scope, user_agent=self._ua,
                                              access_token=oauth2params['client_at'],
                                              refresh_token=oauth2params['client_rt'])
        self._client = gdata.spreadsheets.client.SpreadsheetsClient()
        self._token.authorize(self._client)
        self._worksheet_id = worksheet_id
        self._s_magic = gid2id(sheet).lower()
        self._w_entry = self._client.GetWorksheet(self._worksheet_id, self._s_magic)
        self.batch = None

    def _get_batch(self):
        if not self.batch:
            obj_data = gdata.spreadsheets.data
            self.batch = obj_data.BuildBatchCellsUpdate(self._worksheet_id, self._s_magic)
        return self.batch

    def flush(self):
        if self.batch:
            self._client.batch(self.batch, force=True)
            self.batch = None

    def set_cell(self, row, col, value):
        item = self._client.get_cell(self._worksheet_id, self._s_magic, row, col)
        item.cell.input_value = str(value)
        self._get_batch().add_batch_entry(item, item.id.text, batch_id_string=item.title.text,
                                          operation_string='update')
        # self._client.update(item, force=immediate)

    def get_cell(self, row, col):
        item = self._client.get_cell(self._worksheet_id, self._s_magic, row, col)
        return item.cell.input_value

    def get_range(self, srange):
        query = gdata.spreadsheets.client.CellQuery(range=srange, return_empty='true')
        cells = self._client.GetCells(self._worksheet_id, self._s_magic, q=query)
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

    def set_range(self, srange, matrix, clear_out=False):
        query = gdata.spreadsheets.client.CellQuery(range=srange, return_empty='true')
        cells = self._client.GetCells(self._worksheet_id, self._s_magic, q=query)
        dim = range_dimension(srange)
        items = iter(cells.entry)
        for row in xrange(dim[1]):
            for col in xrange(dim[0]):
                item = items.next()
                try:
                    item.cell.input_value = matrix[row][col]
                except IndexError:
                    if clear_out:
                        item.cell.input_value = ''
                self._get_batch().add_batch_entry(item, item.id.text, batch_id_string=item.title.text,
                                                  operation_string='update')

    def __del__(self):
        self.flush()

    @property
    def dimension(self):
        return int(self._w_entry.col_count.text), int(self._w_entry.row_count.text)

    @dimension.setter
    def dimension(self, dim):
        self._w_entry.col_count.text = str(dim[0])
        self._w_entry.row_count.text = str(dim[1])
        self._client.update(self._w_entry)

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

