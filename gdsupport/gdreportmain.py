#!/bin/env python

import MySQLdb
import sys
import MySQLdb.converters

from paramsparser import AppParamsParser
import inject
from injectors import SQLDb
from gdreport import ReportBuilder, ReportTemplate, TEMPLATE
from gdspreadsheetprovider import GDSpreadsheetProvider
from reportdataprovider import ReportDataProvider


def do_parse(argv):
    parser = AppParamsParser()
    return parser.parse(argv)


def do_inject(config):
    mysql_conf = {'user': config['mysql.user'],
                  'passwd': config['mysql.password'],
                  'db': config['mysql.db'],
                  'host': config['mysql.host'],
                  #'charset': 'utf8',
                  'conv': {}}
    sql_db = MySQLdb.connect(**mysql_conf)

    def my_config(binder):
        binder.bind(SQLDb, sql_db)

    inject.configure(my_config)


def do_run(config):
    report = ReportTemplate()
    builder = ReportBuilder()
    data = ReportDataProvider(config['year'], config['month'], (160, 160))
    report.template = TEMPLATE
    builder.template = report
    builder.datasource = data
    with GDSpreadsheetProvider('0Av6KMa_AP8_sdDdMMFgzb2V2V0laamdqa0N2WFc0R1E') as sheet:
        builder.spreadsheet = sheet
        builder.execute()


if __name__ == "__main__":
    config = do_parse(sys.argv[1:])
    # set_logging(config)
    do_inject(config)
    do_run(config)

