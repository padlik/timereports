#!/bin/env python
import logging
from collections import defaultdict

from decouple import config
from sqlalchemy import or_

from datasources import SQLDataSource, SugarSource
from serializers import User, TimeSheet
from utils import make_month_range

logger = logging.getLogger(__name__)


class SugarPayloadRest(object):
    SERVICE = "ps_Timesheets/filter"
    USERID = "Users/filter"

    def __init__(self):
        self.year = config('REPO_YEAR', cast=int, default=2017)
        self.month = config('REPO_MONTH', cast=int, default=4)
        self.sugar = SugarSource.instance
        self.mysql = SQLDataSource.instance

    def get_sugar_id(self, sugar_uname):
        """

        :param sugar_uname: Sugar user_name (without email)
        :return: sugar user id
        """

        query_str = {"filter": "[{\"user_name\": \"%s\"}]" % sugar_uname}
        logger.debug("Query string for {} is {}".format(sugar_uname, query_str))
        response = self.sugar.get(self.USERID, params=query_str)
        if 'records' in response._fields:
            return response.records[0].id
        return ''

    def get_timesheets(self, sugar_id):
        """

        :param sugar_id: Sugar User ID
        :return: array of timesheets tuples or empty array
        """

        filter_str = "[{\"assigned_user_id\": \"%s\"}," \
                     "{\"activity_date\": {\"$gte\":\"%s\"}}," \
                     "{\"activity_date\": {\"$lte\":\"%s\"}}]"
        dates = make_month_range(self.year, self.month)
        query_str = {"filter": filter_str % (sugar_id, dates[0].strftime("%Y-%m-%d"), dates[1].strftime("%Y-%m-%d")),
                     "max_num": "100"}
        logger.debug("Query string for {} is {}".format(sugar_id, query_str))
        ts = []
        response = self.sugar.get(self.SERVICE, params=query_str)
        if 'records' in response._fields:
            for rec in response.records:
                ts.append((rec.created_by,
                           rec.activity_date,
                           rec.time_spent,
                           rec.description,
                           rec.id,
                           rec.name))
        return ts

    def check_users_sugarid(self, check_dismissed=False):
        """
        Search for users with empty sugar_id (empty or NULL) and updates them from Sugar
        :return: Number of users updated
        """
        sql_qry = self.mysql.query(User).filter(or_(User.sugar_id.is_(None), User.sugar_id == ''))
        if not check_dismissed:
            sql_qry = sql_qry.filter(User.dissmissed == 'N')
        empty_users = sql_qry.all()

        if empty_users:
            logger.info("Users with empty sugar_id found {}".format(empty_users))
            logger.info("Updating users...")
            for user in empty_users:
                logger.info("Query for {}".format(user.sugar_uname))
                sugar_id = self.get_sugar_id(user.sugar_uname)
                logger.info("User: {}, SugarId: {}".format(user.sugar_uname, sugar_id))
                user.sugar_id = sugar_id
                self.mysql.add(user)
            self.mysql.commit()
        return len(empty_users)

    def process_timesheets(self):
        """
        Re
        :return:
        """

        try:
            active_users = self.mysql.query(User).filter(User.dissmissed != 'Y', User.sugar_id.isnot(None),
                                                         or_(User.sugar_id != '', User.sugar_id.isnot(None))).all()
            dates = make_month_range(self.year, self.month)
            logger.info("Removing previous entries...")
            deleted_num = self.mysql.query(TimeSheet).filter(TimeSheet.activity_date >= dates[0],
                                                             TimeSheet.activity_date <= dates[1],
                                                             or_(TimeSheet.source != 'JIRA',
                                                                 TimeSheet.source.is_(None))).delete()
            logger.info("Removed {} timesheets entries for year:{} month:{}".format(deleted_num, self.year, self.month))
            user_dict = {u.sugar_id: u for u in active_users}
            logger.debug("Active users are {}".format(user_dict))
            logger.info("Querying SugarCRM... ")
            ts_list = []
            for sugar_id in user_dict.keys():
                logger.info("Querying timesheets for {} ".format(user_dict[sugar_id].sugar_uname))
                ts = self.get_timesheets(sugar_id)
                logger.info("User: {} -> {} timesheets".format(user_dict[sugar_id].sugar_uname, len(ts)))
                if ts:
                    ts_list.append(ts)
            logger.info("Done querying")
            summary = defaultdict(float)
            for entries in ts_list:
                for entry in entries:
                    user = user_dict[entry[0]]
                    t = TimeSheet(userid=user.id, created_by=entry[0], activity_date=entry[1], time_spent=entry[2],
                                  description=entry[3], id=entry[4], name=entry[5])
                    summary[user.sugar_uname] += float(entry[2])
                    self.mysql.add(t)
            logger.debug("Dirty entries {}".format(self.mysql.dirty))
            self.mysql.commit()
            logger.info("Commit completed")
            logger.info("=== Timesheets summary Year: {} Month: {}  === ".format(self.year, self.month))
            for k, v in summary.iteritems():
                logger.info("{}: {} hrs".format(k, v))
            return sum(summary.values())
        finally:
            self.sugar.logout()
            self.mysql.rollback()

    def payload(self):
        self.year = config('REPO_YEAR', cast=int, default=2017)
        self.month = config('REPO_MONTH', cast=int, default=4)
        logger.info("Re-connecting Sugar...")
        self.sugar.connect(config('SUGAR_USER'), config('SUGAR_PASS'))
        logger.info('Connected. Ping instance -> {}'.format(self.sugar.ping()))
        logger.info("About to fetch timesheets for {}-{}".format(self.year, self.month))
        overall_hrs = self.process_timesheets()
        logger.info("=== Total Hrs for {}-{} = {}".format(self.year, self.month, overall_hrs))

    def __repr__(self):
        return self.__class__.__name__


SugarPayload = SugarPayloadRest
