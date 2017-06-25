#!/bin/env python
import logging

from docutils import ReportTemplate, ReportBuilder, TEMPLATE, GDSpreadsheetProvider, ReportDataProvider
from decouple import config

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
        self.builder.datasource = ReportDataProvider(self.year, self.month, (160, 160))
        logger.info("Init Google spreadsheet export month: {}={}".format(self.year, self.month))

    def payload(self):
        logger.info("Starting Google spreadsheet export for {}-{}".format(self.year, self.month))
        with GDSpreadsheetProvider(self.sheet) as ssheet:
            self.builder.spreadsheet = ssheet
            self.builder.execute()
        logger.info("Export to google spreadsheet complete")

    def __repr__(self):
        return self.__class__.__name__
