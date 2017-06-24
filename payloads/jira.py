#!/bin/env python
import logging
from multiprocessing.dummy import Pool

from datasources import JiraSource
from datasources import SQLDataSource
from serializers import TimeSheet, User
from utils import make_month_range, jdate2pydate

logger = logging.getLogger(__name__)


class JiraPayload(object):
    def __init__(self, year=2017, month=3, threads=5):
        self.users = self.__get_users()
        self.year = year
        self.month = month
        self.threads = threads

    def __thread_worker(self, user):
        """
        Thread worker function against JIRA
        :param user: jira user name for timesheets retrieval
        :return: Dict {user_name: [array of timesheets]}
        """

        jira = JiraSource.instance
        start_date, finish_date = make_month_range(self.year, self.month)
        logger.debug("Querying from {} to {}".format(start_date, finish_date))
        qry = 'key in workedIssues("{start}", "{finish}", "{user}")'.format(start=start_date.strftime("%Y/%m/%d"),
                                                                            finish=finish_date.strftime("%Y/%m/%d"),
                                                                            user=user)
        logger.debug("Query is {}".format(qry))
        ts = []
        try:
            issues = jira.search_issues(jql_str=qry, maxResults=1000)
            for i in issues:
                logger.debug("Issues found {}".format(user))
                for w in [w for w in jira.worklogs(i.key) if w.author.name == user]:
                    d_created = jdate2pydate(w.started)
                    logger.debug("Worklog date for {} is {}".format(user, d_created))
                    if start_date <= d_created <= finish_date:  # it might happens too!
                        logger.debug("We are in the time frame {} {} {}".format(user, start_date, finish_date))
                        ts.append([w.id, w.comment, float(w.timeSpentSeconds) / 3600, d_created])
            logger.debug("Timesheets for user {} are {}".format(user, ts))
            logger.info("Finishing worker for user: {} ({} timesheets)".format(user, len(ts)))
        except Exception as e:
            logger.error("Error getting data form JIRA: {}".format(e))
            logger.warn("Thread will continue though with empty set for a user {}".format(user))
            ts = []
        return {user: ts}

    def __set_timesheets(self, ts):
        """
        Writes data to the date to database
        :param ts: timesheets for a user
        :return: nothing
        """
        logger.info("Updating Jira timesheets overall:{}".format(len(ts)))
        logger.info("Deleting previous version for {}-{}".format(self.year, self.month))
        mysql = SQLDataSource.instance

        try:
            dates = make_month_range(self.year, self.month)
            logger.info("Deleting previous timesheets from JIRA")
            mysql.query(TimeSheet).filter(TimeSheet.activity_date >= dates[0], TimeSheet.activity_date <= dates[1],
                                          TimeSheet.source == 'JIRA').delete()
            mysql.flush()
            logger.info('Deleted, waiting for insert and commit...')
            logger.info('Preparing for insert {} sheets'.format(len(ts)))

            fields = ['userid', 'id', 'description', 'time_spent', 'activity_date', 'source']
            bulk_ts = map(lambda lst: {fields[n]: v for n, v in enumerate(lst)}, ts)
            logger.debug("Bulk update package {}".format(bulk_ts))
            mysql.execute(TimeSheet.__table__.insert(), bulk_ts)
            mysql.commit()
            logger.info("Update completed")
        finally:
            mysql.rollback()

    def __get_users(self):
        """
        List of active users to build report for
        :return: Dict of {user_name: id} from database
        """
        logger.info("Getting user for Jira timesheets")
        mysql = SQLDataSource.instance
        users = mysql.query(User).filter(User.dissmissed == 'N').all()
        user_dict = {u.intetics_uname + '@intetics.com': u.id for u in users}
        logger.debug("Users fetched {}".format(user_dict))
        return user_dict

    def payload(self):
        """
        Main function for reporting. Starts number of threads to run __thread_worker
        :return: overall number of hours
        """
        logger.info("Jira payload start for {}-{}".format(self.year, self.month))
        logger.info("Jira max threads is set to: {}".format(self.threads))
        pool = Pool(self.threads)
        logger.info("Spreading threads")
        results = pool.map(self.__thread_worker, self.users)
        pool.close()
        pool.join()
        logger.info("All threads are finished. Preparing summary")
        timesheets = []
        overall = 0.0
        for r in results:
            for u, ts in r.iteritems():
                overall += sum([t[2] for t in ts])
                logger.debug("{}->{} hrs".format(u, sum([t[2] for t in ts]) / 3600))
                logger.debug("User: {} and timesheet {}".format(self.users[u], ts))
                for t in ts:
                    timesheets.append([self.users[u]] + t + ['JIRA'])
        self.__set_timesheets(timesheets)
        logger.info("Jira timesheets are uploaded: {} hrs".format(overall))
        return overall

    def __repr__(self):
        return self.__class__.__name__
