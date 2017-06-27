#!/bin/env python

import datetime
import logging

from datasources import SQLDataSource
from gdreport import DataProvider
from gdsqlbuilder import GDORMQueryBuilder

logger = logging.getLogger(__name__)


class ReportDataProvider(DataProvider):
    def __init__(self, year, month, targets):
        self._report_data = {'minsk_target': targets[0], 'ua_target': targets[1],
                             'update_date': datetime.datetime.utcnow().strftime('%d, %b %Y'),
                             'update_time': datetime.datetime.utcnow().time().strftime('%H:%M'),
                             'hour_report': self._load_data(year, month)}

    @staticmethod
    def _load_data(year, month):
        mysql = SQLDataSource.instance
        # q = text(GDQueryBuilder(year=year, month=month).query)
        q = GDORMQueryBuilder(mysql, year, month).query
        logger.debug("Summary query is {}".format(q))
        summary = q.all()
        res = []
        # Conversion to string is required as google docs cannot convert floats properly
        for row in summary:
            res.append(tuple(map(str, row)))
        logger.debug("Rows returned {}".format(res))
        return res

    def get_range_value(self, key):
        logger.debug("range for key => {}".format(key))
        return [v for v in self._report_data[key]]

    def get_value(self, key):
        logger.debug("value for key => {}".format(key))
        return self._report_data[key]
