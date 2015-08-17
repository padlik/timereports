#!/bin/env python
import calendar as cal

from primitives import logger


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
        def make_calendar(year, month):
            # just first days of weeks are required
            z_trim = lambda x: [d for d in x if d != 0]
            cal.setfirstweekday(cal.MONDAY)
            weeks = cal.monthcalendar(year, month)
            weeks[0] = z_trim(weeks[0])
            weeks[-1] = z_trim(weeks[-1])
            logger.Logger.debug("Calendar for month {}".format(str([(wd[0], wd[-1]) for wd in weeks])))
            return [(wd[0], wd[-1]) for wd in weeks]

        def f_date(day):
            return "%s-%s-%s" % (self._year, self._month, day)

        s_cal = make_calendar(self._year, self._month)
        s_sql = GDQueryBuilder._HEAD
        for n, dayt in enumerate(s_cal):
            s_sql += self._BODY % (f_date(dayt[0]), f_date(dayt[1]), self._n_weeks[n])
            logger.Logger.debug("Adjusting number of weeks to 6")
        # hack to provide 6th week in case if it is not present
        if len(s_cal) < 6:
            s_sql += self._DUMMY % self._n_weeks[5]
        s_sql += self._FOOT.format(start_date=f_date(s_cal[0][0]), end_date=f_date(s_cal[-1][-1]))
        logger.Logger.debug("Query build for {0},{1} is: {2}".format(self.year, self.month, s_sql))
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
    report.year = 2015
    report.month = 7
    print report.query
