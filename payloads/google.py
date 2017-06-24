#!/bin/env python
import logging

from docutils import ReportTemplate, ReportBuilder, TEMPLATE, GDSpreadsheetProvider, ReportDataProvider

logger = logging.getLogger(__name__)


class GooglePayload(object):
    def __init__(self, sheet, year, month):
        """
        Init Google reporting object
        :param sheet: Spreadsheet code (copy form google)
        :param year: Year of the report
        :param month: Month of the report
        """

        logger.info("Init Google spreadsheet export month: {}={}".format(year, month))
        self.year = year
        self.month = month
        self.sheet = sheet
        self.report = ReportTemplate()
        self.builder = ReportBuilder()
        self.report.template = TEMPLATE
        self.builder.template = self.report
        self.builder.datasource = ReportDataProvider(self.year, self.month, (160, 160))

    def payload(self):
        logger.info("Starting Google spreadsheet export for {}-{}".format(self.year, self.month))
        with GDSpreadsheetProvider(self.sheet) as ssheet:
            self.builder.spreadsheet = ssheet
            self.builder.execute()
        logger.info("Export to google spreadsheet complete")

    def __repr__(self):
        return self.__class__.__name__
