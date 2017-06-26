from datasources import SQLDataSource, mysql_creator
from payloads import SugarPayload2
from serializers import TimeSheet, User
from sqlalchemy.sql import func


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
    dates = get_dates(2017, 4)
    us = [49L, 59L]
    # print dates
    s = mysql.query(TimeSheet.userid, func.sum(TimeSheet.time_spent).label('cnt')).group_by(TimeSheet.userid).subquery()
    for u, c in mysql.query(User, s.c.cnt).outerjoin(s, User.id == s.c.userid).order_by(User.sugar_uname):
        print (u.sugar_uname, c)
    # users = mysql.query(User).join(TimeSheet).filter(TimeSheet.time_spent > 100)
    # print users.all()
