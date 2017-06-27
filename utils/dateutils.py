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


def make_weeks_range(year, month):
    """
    First and last days of week in a month for a yeat
    :param year: int, year
    :param month: int, month
    :return: list of tuples containing first and last day of week
    """
    # just first days of weeks are required
    z_trim = lambda x: [d for d in x if d != 0]
    calendar.setfirstweekday(calendar.MONDAY)
    weeks = calendar.monthcalendar(year, month)
    weeks[0] = z_trim(weeks[0])
    weeks[-1] = z_trim(weeks[-1])
    return [(wd[0], wd[-1]) for wd in weeks]
