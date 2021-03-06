#!/bin/env python
import logging

from decouple import config

from docutils import ReportTemplate, ReportBuilder, TEMPLATE, GDSpreadsheetProvider, ReportDataProvider

logger = logging.getLogger(__name__)


class GooglePayload(object):
    def __init__(self):
        """
        Init Google reporting object
        """

        self.year = config('REPO_YEAR', cast=int, default=2017)
        self.month = config('REPO_MONTH', cast=int, default=4)
        self.sheet = config('GOOGLE_SHEET')
        self.report = ReportTemplate()
        self.builder = ReportBuilder()
        self.report.template = TEMPLATE
        self.builder.template = self.report
        logger.info("Init Google spreadsheet export month: {}={}".format(self.year, self.month))

    def payload(self):
        logger.info("Starting Google spreadsheet export for {}-{}".format(self.year, self.month))
        self.builder.datasource = ReportDataProvider(self.year, self.month, (160, 160))
        with GDSpreadsheetProvider(self.sheet) as ssheet:
            self.builder.spreadsheet = ssheet
            self.builder.execute()
        logger.info("Export to google spreadsheet complete")

    def __repr__(self):
        return self.__class__.__name__
