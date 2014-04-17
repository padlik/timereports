#!/bin/env python

import datetime

from gdreport import DataProvider
from injectors import SQLDb
import inject
from gdsqlbuilder import GDQueryBuilder


class ReportDataProvider(DataProvider):
    def __init__(self, year, month, targets):
        self._report_data = {'minsk_target': targets[0], 'ua_target': targets[1],
                             'update_date': datetime.date.today().strftime('%d, %b %Y'),
                             'update_time': datetime.datetime.today().time().strftime('%H:%M'),
                             'hour_report': self._load_data(year, month)}

    @staticmethod
    def _load_data(year, month):
        db = inject.instance(SQLDb)
        builder = GDQueryBuilder(year=year, month=month)
        q_sql = builder.query
        c = db.cursor()
        c.execute(q_sql)
        return c.fetchall()

    def get_range_value(self, key):
        for v in self._report_data[key]:
            yield [v]

    def get_value(self, key):
        return self._report_data[key]


if __name__ == "__main__":
    import MySQLdb

    my_conv = {}
    mysql_conf = {'user': 'root',
                  'passwd': 'pass',
                  'db': 'time_reports',
                  'host': 'localhost',
                  #'charset': 'utf8',
                  'conv': my_conv}
    sql_db = MySQLdb.connect(**mysql_conf)

    def my_config(binder):
        binder.bind(SQLDb, sql_db)

    inject.configure(my_config)
    rdp = ReportDataProvider(2014, 4, (160, 160))
    for v in rdp.get_range_value('hour_report'):
        print v
    print rdp.get_value('update_time')
    print rdp.get_value('update_date')


