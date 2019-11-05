#!/bin/env python
import logging
from multiprocessing.dummy import Pool

from decouple import config

from datasources import JiraSource
from datasources import SQLDataSource
from serializers import TimeSheet, User
from utils import make_month_range, jdate2pydate

logger = logging.getLogger(__name__)


class JiraPayload(object):
    def __init__(self):
        self.users = self._get_users()
        self.year = config('REPO_YEAR', cast=int, default=2017)
        self.month = config('REPO_MONTH', cast=int, default=4)
        self.threads = config('JIRA_THREADS', cast=int, default=4)

    def _thread_worker(self, user):
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
            logger.warn("Data for User -># {} #<- will NOT be updated ".format(user))
            ts = []
        return {user: ts}

    def _set_timesheets(self, ts, exclude_users=None):
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
            to_delete = mysql.query(TimeSheet).filter(TimeSheet.activity_date >= dates[0],
                                                      TimeSheet.activity_date <= dates[1], TimeSheet.source == 'JIRA')
            if exclude_users:
                to_delete = to_delete.filter(~TimeSheet.userid.in_(exclude_users))
                r_user_dict = {v: k for k, v in self.users.items()}
                logger.warn("Users excluded: {}".format([r_user_dict[u] for u in exclude_users]))
            to_delete.delete(synchronize_session='fetch')  # sync is required for complicated queries (IN is the case)
            mysql.flush()

            logger.info('Deleted, waiting for insert and commit...')
            logger.info('Preparing for insert {} sheets'.format(len(ts)))

            fields = ['userid', 'id', 'description', 'time_spent', 'activity_date', 'source']
            bulk_ts = [{fields[n]: v for n, v in enumerate(lst)} for lst in ts]
            logger.debug("Bulk update package {}".format(bulk_ts))
            mysql.execute(TimeSheet.__table__.insert(), bulk_ts)
            mysql.commit()
            logger.info("Update completed")
        finally:
            mysql.rollback()

    @staticmethod
    def _get_users():
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
        results = pool.map(self._thread_worker, self.users)
        pool.close()
        pool.join()
        logger.info("All threads are finished. Preparing summary")
        timesheets = []
        ex_users = []
        overall = 0.0
        for r in results:
            for u, ts in r.items():
                sum_ts = sum([t[2] for t in ts])
                overall += sum_ts
                if not ts:
                    ex_users.append(self.users[u])
                logger.info("{}->{} hrs".format(u, sum_ts))
                logger.debug("User: {} and timesheet {}".format(self.users[u], ts))
                for t in ts:
                    timesheets.append([self.users[u]] + t + ['JIRA'])
        self._set_timesheets(timesheets, ex_users)
        logger.info("Jira timesheets are uploaded: {} hrs".format(overall))
        return overall

    def __repr__(self):
        return self.__class__.__name__
