__author__ = 'paul'

import MySQLdb
import sys

from jira.client import JIRA

from paramsparser import AppParamsParser
import inject
from injectors import SQLDb
from injectors import Jira
from primitives.logger import Logger

config = None


def do_parse(argv):
    parser = AppParamsParser()
    return parser.parse(argv)


def do_inject():
    mysql_conf = {'user': config['mysql.user'],
                  'passwd': config['mysql.password'],
                  'db': config['mysql.db'],
                  'host': config['mysql.host'],
                  'charset': 'utf8'}
    sql_db = MySQLdb.connect(**mysql_conf)

    jira_opts = {'server': config['jira.url']}
    jira_auth = (config['jira.user'], config['jira.password'])
    jira = JIRA(options=jira_opts, basic_auth=jira_auth)

    # injecting mysql and jira
    def my_config(binder):
        binder.bind(SQLDb, sql_db)
        binder.bind(Jira, jira)

    Logger.debug("Injection complete")
    inject.configure(my_config)


def prepare_users():
    db = inject.instance(SQLDb)
    q_sql = "select id, intetics_uname from users where dissmissed = 'N'"
    c = db.cursor
    c.execute(q_sql)
    return c.fetchall()


def report_worker(user):
    def get_dates():
        import datetime
        import calendar

        year = config['year']
        month = config['month']
        first = datetime.datetime(year=year, month=month, day=1)
        last = datetime.datetime(year=year, month=month, day=calendar.monthrange(year, month)[1])
        return tuple([first, last])

    def jira2date(date_string):
        import iso8601
        import datetime

        complex_date = iso8601.parse_date(date_string)
        simple_date = datetime.datetime(year=complex_date.year, month=complex_date.month, day=complex_date.day)
        return simple_date

    jira = inject.instance(Jira)
    start_date, finish_date = get_dates()
    Logger.debug("Dates to query from {} to {}".format(start_date, finish_date))
    qry = 'key in workedIssues("{start}", "{finish}", "{user}")'.format(start=start_date.strftime("%Y/%m/%d"),
                                                                        finish=finish_date.strftime("%Y/%m/%d"),
                                                                        user=user)
    Logger.debug("Query is {}".format(qry))
    issues = jira.search_issues(qry)
    ts = []
    for i in issues:
        for w in [w for w in jira.worklogs(i.key) if w.author.name == user]:

            d_created = jira2date(w.started)
            if start_date <= d_created <= finish_date:  # it might happens too!
                ts.append([w.id, w.comment, w.timeSpentSeconds, d_created])
    Logger.debug("Timesheets for user {} are {}".format(user, ts))
    return {user: ts}


if __name__ == "__main__":
    config = do_parse(sys.argv[1:])
    from primitives.logger import set_logging

    set_logging(config)
    do_inject()
    print report_worker("p.pronko@intetics.com")
