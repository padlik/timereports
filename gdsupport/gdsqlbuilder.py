#!/bin/env python
import calendar as cal


class GDQueryBuilder(object):
    _n_weeks = ['first', 'second', 'third', 'fourth', 'fifth', 'sixth']
    _HEAD = """ select users.sugar_uname AS username,"""
    _BODY = """ sum((case
                when (timesheets.activity_date between '%s' and '%s') then timesheets.time_spent
                else 0
                end)) AS %s_week, """
    _FOOT = """ sum((case
                when
                ((timesheets.activity_date between '%s' and '%s')
                    and (timesheets.description like 'overtime%%'))
                then
                    timesheets.time_spent
                else 0
                end)) AS overtime
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
        def make_calendar(year, month):
            #just first days of weeks are required
            z_trim = lambda x: [d for d in x if d != 0]
            cal.setfirstweekday(cal.MONDAY)
            weeks = cal.monthcalendar(year, month)
            weeks[0] = z_trim(weeks[0])
            weeks[-1] = z_trim(weeks[-1])
            return [(wd[0], wd[-1]) for wd in weeks]

        def f_date(day):
            return "%s-%s-%s" % (self._year, self._month, day)

        s_cal = make_calendar(self._year, self._month)
        s_sql = GDQueryBuilder._HEAD
        for n, dayt in enumerate(s_cal):
            s_sql += self._BODY % (f_date(dayt[0]), f_date(dayt[1]), self._n_weeks[n])
        s_sql += self._FOOT % (f_date(s_cal[0][0]), f_date(s_cal[-1][-1]))
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


if __name__ == '__main__':
    report = GDQueryBuilder()
    # print report.cursor
    report.year = 2014
    report.month = 3
    print report.query