#!/bin/env python
import datetime
import logging

from sqlalchemy import or_
from sqlalchemy.sql import func, case

from serializers import TimeSheet, User
from utils import make_weeks_range

logger = logging.getLogger(__name__)


class GDQueryBuilder(object):
    _n_weeks = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth']
    _HEAD = """ select users.sugar_uname AS username,"""
    _BODY = """ sum((case
                when (timesheets.activity_date between '%s' and '%s')
                      and (IFNULL(timesheets.source,'') <> 'JIRA')
                then timesheets.time_spent
                else 0
                end)) AS %s_week, """
    _DUMMY = """0 as %s_week, """
    _FOOT = """ sum((case
                when
                ((timesheets.activity_date between '{start_date}' and '{end_date}')
                    and (timesheets.description like 'overtime%%'))
                then
                    timesheets.time_spent
                else 0
                end)) AS overtime,
                sum(case
                    when
                        ((timesheets.source is not null)
                            and (timesheets.time_spent
                            and timesheets.activity_date between '{start_date}' and '{end_date}'))
                    then
                        timesheets.time_spent
                    else 0
                end) AS jira
                from
                (users
                left join timesheets ON ((timesheets.userid = users.id)))
                where
                (users.dissmissed = 'N')
                group by users.sugar_uname """

    def __init__(self, year=2014, month=2):
        self._year = year
        self._month = month

    def _build_query(self):
        make_calendar = make_weeks_range

        def f_date(day):
            return "%s-%s-%s" % (self._year, self._month, day)

        s_cal = make_calendar(self._year, self._month)
        s_sql = GDQueryBuilder._HEAD
        for n, dayt in enumerate(s_cal):
            s_sql += self._BODY % (f_date(dayt[0]), f_date(dayt[1]), self._n_weeks[n])
            logger.debug("Adjusting number of weeks to 6")
        # hack to provide 6th week in case if it is not present
        if len(s_cal) < 6:
            s_sql += self._DUMMY % self._n_weeks[5]
        s_sql += self._FOOT.format(start_date=f_date(s_cal[0][0]), end_date=f_date(s_cal[-1][-1]))
        logger.debug("Query build for {0},{1} is: {2}".format(self.year, self.month, s_sql))
        return s_sql

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @year.setter
    def year(self, y):
        self._year = y

    @month.setter
    def month(self, m):
        self._month = m

    @property
    def query(self):
        return self._build_query()


QT_SUGAR = 0
QT_JIRA = 2
QT_OVT = 3

MAX_WEEKS = 6


class GDORMQueryBuilder(object):
    def __init__(self, db, year, month):
        self._db = db
        self._year = year
        self._month = month

    def _make_week_subq(self, date_range, query_type=QT_SUGAR):

        stmt = self._db.query(TimeSheet.userid, func.sum(TimeSheet.time_spent).label('sumts')).filter(
            TimeSheet.activity_date >= date_range[0], TimeSheet.activity_date <= date_range[1])

        if query_type == QT_SUGAR:
            stmt = stmt.filter(or_(TimeSheet.source != 'JIRA', TimeSheet.source.is_(None)))
        if query_type == QT_JIRA:
            stmt = stmt.filter(TimeSheet.source.isnot(None))
        if query_type == QT_OVT:
            stmt = stmt.filter(TimeSheet.description.ilike('%overtime%'))

        stmt = stmt.group_by(TimeSheet.userid).subquery()

        return stmt

    def _make_query(self):
        week_ranges = map(lambda t: (
            datetime.datetime.strptime("{}-{}-{}".format(t[0], self._month, self._year), "%d-%m-%Y").date(),
            datetime.datetime.strptime("{}-{}-{}".format(t[1], self._month, self._year), "%d-%m-%Y").date()),
                          make_weeks_range(self._year, self._month))

        month_range = (week_ranges[0][0], week_ranges[-1][-1])
        if len(week_ranges) < 6:
            week_ranges.append((week_ranges[0][1], week_ranges[0][0]))  # Deliberate false condition

        columns = [User.sugar_uname]
        # typical 6 weeks
        for week in week_ranges:
            columns.append(self._make_week_subq(week))
        # overtime
        columns.append(self._make_week_subq(month_range, query_type=QT_OVT))
        # jira
        columns.append(self._make_week_subq(month_range, query_type=QT_JIRA))

        params = [User.sugar_uname]
        # 1st param is sugar_uname and it's not from a subquery
        for w in columns[1:]:
            params.append(case([(w.c.sumts.isnot(None), w.c.sumts)], else_=0))

        # Query params has been build (select from)
        qry = self._db.query(*params)

        # Building joins (where)
        for w in columns[1:]:
            qry = qry.outerjoin(w, User.id == w.c.userid)

        qry = qry.filter(User.dissmissed == 'N').order_by(User.sugar_uname)
        return qry

    @property
    def db(self):
        return self._db

    @db.setter
    def db(self, db):
        self._db = db

    @property
    def year(self):
        return self._year

    @property
    def month(self):
        return self._month

    @year.setter
    def year(self, y):
        self._year = y

    @month.setter
    def month(self, m):
        self._month = m

    @property
    def query(self):
        return self._make_query()


if __name__ == '__main__':
    report = GDQueryBuilder()
    # print report.cursor
    report.year = 2017
    report.month = 5
    print report.query
