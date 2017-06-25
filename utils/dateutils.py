import calendar
import datetime


def make_month_range(year, month):
    """
    First and last dates of the month in a year
    :param year: Year of the report
    :param month: Month of the report
    :return: return tuple(date1, date2) where date1 is the fist day of month and date2 is the last one
    """
    first = datetime.datetime(year=year, month=month, day=1)
    last = datetime.datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
    return tuple([first, last])


def jdate2pydate(date_string):
    """
    Converts JIRA date string to Python simple date value
    :param date_string: JIRA string date
    :return: Simple Python date without time zone
    """
    import iso8601
    import datetime

    complex_date = iso8601.parse_date(date_string)
    simple_date = datetime.datetime(year=complex_date.year, month=complex_date.month, day=complex_date.day)
    return simple_date
