#!/bin/env python
from multiprocessing.dummy import Pool

from primitives.logger import Logger
from primitives.runpayload import Payload
from reports import inject
from reports.injectors import SQLDb, Jira


class JiraPayload(Payload):
    def __init__(self, year=2017, month=3, threads=5):
        super(JiraPayload, self).__init__()
        self.users = self.__get_users()
        self.year = year
        self.month = month
        self.threads = threads

    def __thread_worker(self, user):
        """

        :param user: jira user name for timesheets retrieval
        :return: Dict {user_name: [array of timesheets]}
        """

        def get_dates():
            """

            :return: First and last day of a month for reporting
            """
            import datetime
            import calendar

            first = datetime.datetime(year=self.year, month=self.month, day=1)
            last = datetime.datetime(year=self.year, month=self.month,
                                     day=calendar.monthrange(self.year, self.month)[1])
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

        jira = inject.instance(Jira)
        start_date, finish_date = get_dates()
        Logger.debug("Querying from {} to {}".format(start_date, finish_date))
        qry = 'key in workedIssues("{start}", "{finish}", "{user}")'.format(start=start_date.strftime("%Y/%m/%d"),
                                                                            finish=finish_date.strftime("%Y/%m/%d"),
                                                                            user=user)
        Logger.debug("Query is {}".format(qry))
        try:
            issues = jira.search_issues(jql_str=qry, maxResults=1000)
        except Exception as e:
            Logger.error("Error getting data form JIRA: {}".format(e.message))
            Logger.warn("Thread will continue though with empty set for a user {}".format(user))
            return {user: []}
        ts = []
        for i in issues:
            Logger.debug("Issues found {}".format(user))
            for w in [w for w in jira.worklogs(i.key) if w.author.name == user]:
                d_created = jdate2pydate(w.started)
                Logger.debug("Worklog date for {} is {}".format(user, d_created))
                if start_date <= d_created <= finish_date:  # it might happens too!
                    Logger.debug("We are in the time frame {} {} {}".format(user, start_date, finish_date))
                    ts.append([w.id, w.comment, float(w.timeSpentSeconds) / 3600, d_created])
        Logger.debug("Timesheets for user {} are {}".format(user, ts))
        Logger.info("Finishing worker for user: {} ({} timeseets)".format(user, len(ts)))
        return {user: ts}

    def __set_timesheets(self, ts):
        """

        :param ts: timesheets for a user
        :return: nothing
        """
        Logger.info("Updating Jira timesheets overall:{}".format(len(ts)))
        db = inject.instance(SQLDb)
        flds = ['userid', 'id', 'description', 'time_spent', 'activity_date', 'source']
        Logger.debug("Updating with fields {}".format(flds))
        q_sql = 'INSERT INTO timesheets( ' + ','.join(flds) + ') VALUES (' + ','.join(['%s'] * (len(flds))) + ')'
        q_sql += ' ON DUPLICATE KEY UPDATE %s = VALUES(%s) ' % ('time_spent', 'time_spent')
        Logger.debug("Update query: {}".format(q_sql))
        c = db.cursor()
        c.executemany(q_sql, ts)
        db.commit()
        Logger.info("Update completed")

    def __get_users(self):
        """

        :return: Dict of {user_name: id} from MySQL DB
        """
        Logger.info("Getting user for Jira timesheets")
        db = inject.instance(SQLDb)
        q_sql = "SELECT TRIM(concat(intetics_uname,'@intetics.com')), id FROM users WHERE dissmissed = 'N'"
        c = db.cursor()
        c.execute(q_sql)
        return dict(c.fetchall())

    def payload(self):
        Logger.info("Jira payload start for {}-{}".format(self.year, self.month))
        Logger.info("Jira max threads is set to: {}".format(self.threads))
        pool = Pool(self.threads)
        Logger.info("Spreading threads")
        results = pool.map(self.__thread_worker, self.users)
        pool.close()
        pool.join()
        Logger.info("All threads are finished. Preparing summary")
        timesheets = []
        for r in results:
            for u, ts in r.iteritems():
                Logger.debug("{}->{} hrs".format(u, sum([t[2] for t in ts]) / 3600))
                Logger.debug("User: {} and timesheet {}".format(self.users[u], ts))
                for t in ts:
                    timesheets.append([self.users[u]] + t + ['JIRA'])
        self.__set_timesheets(timesheets)
        Logger.info("Jira timesheets are uploaded")

    def __str__(self):
        return self.__class__.__name__
