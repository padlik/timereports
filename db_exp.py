from datasources import SQLDataSource, mysql_creator
from payloads import SugarPayload2


def get_dates(year, month):
    """

    :return: First and last day of a month for reporting
    """
    import datetime
    import calendar

    first = datetime.datetime(year=year, month=month, day=1)
    last = datetime.datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
    return tuple([first, last])


if __name__ == '__main__':
    SQLDataSource.set_creator(mysql_creator)
    mysql = SQLDataSource.instance
    # dates = get_dates(2017, 4)
    # print dates
    # users = mysql.query(TimeSheet).filter(TimeSheet.activity_date >= dates[0],
    #                                       TimeSheet.activity_date <= dates[1],
    #                                       TimeSheet.source.is_(None)).count()
    # print users

    print SugarPayload2.check_users_sugarid(check_dismissed=True)
