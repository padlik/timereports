#!/bin/env python

import logging

from docutils import ReportTemplate, ReportBuilder, TEMPLATE, GDSpreadsheetProvider, ReportDataProvider
from payload import Payload

logger = logging.getLogger(__name__)


class GooglePayload(Payload):
    def __init__(self, sheet, year, month):
        """

        :type sheet: google spreadsheet string
        """
        super(GooglePayload, self).__init__()
        logger.info("Init Google spreadsheet export")
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

    def __str__(self):
        return self.__class__.__name__
