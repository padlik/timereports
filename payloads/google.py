#!/bin/env python

from gdsupport import ReportTemplate, ReportBuilder, TEMPLATE, GDSpreadsheetProvider, ReportDataProvider
from primitives import Payload, Logger


class GooglePayload(Payload):
    def __init__(self, sheet, year, month):
        """

        :type sheet: google spreadsheet string
        """
        super(GooglePayload, self).__init__()
        Logger.info("Init Google spreadsheet export")
        self.year = year
        self.month = month
        self.sheet = sheet
        self.report = ReportTemplate()
        self.builder = ReportBuilder()
        self.report.template = TEMPLATE
        self.builder.template = self.report
        self.builder.datasource = ReportDataProvider(self.year, self.month, (160, 160))

    def payload(self):
        Logger.info("Starting Google spreadsheet export for {}-{}".format(self.year, self.month))
        with GDSpreadsheetProvider(self.sheet) as ssheet:
            self.builder.spreadsheet = ssheet
            self.builder.execute()
        Logger.info("Export to google spreadsheet complete")

    def __str__(self):
        return self.__class__.__name__
