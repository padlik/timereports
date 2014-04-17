#!/bin/env python

import datetime

from gdreport import DataProvider
from injectors import SQLDb
import inject
from primitives import logger
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
        logger.Logger.debug("Executing => {}".format(q_sql))
        c.execute(q_sql)
        return c.fetchall()

    def get_range_value(self, key):
        logger.Logger.debug("range for key => {}".format(key))
        return [v for v in self._report_data[key]]

    def get_value(self, key):
        logger.Logger.debug("value for key => {}".format(key))
        return self._report_data[key]



