#!/bin/env python

import MySQLdb
import sys
import MySQLdb.converters

from paramsparser import AppParamsParser
import inject
from injectors import SQLDb
from gdsupport.gdreport import ReportBuilder, ReportTemplate, TEMPLATE
from gdsupport.gdspreadsheetprovider import GDSpreadsheetProvider
from gdsupport.reportdataprovider import ReportDataProvider
from primitives import logger


def do_parse(argv):
    parser = AppParamsParser()
    return parser.parse(argv)


def do_inject(config):
    logger.Logger.debug('injecting')
    mysql_conf = {'user': config['mysql.user'],
                  'passwd': config['mysql.password'],
                  'db': config['mysql.db'],
                  'host': config['mysql.host'],
                  'conv': {}}
    #conv is added to return all the values as strings which is good for google
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
    logger.set_logging(config)
    do_inject(config)
    do_run(config)

