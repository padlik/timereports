#!/bin/env python
import logging
from collections import defaultdict

from sqlalchemy import or_

from datasources import SQLDataSource, SugarSource
from serializers import User, TimeSheet
from sugarutils import ChainSugarCrmQuery
from utils import make_month_range

logger = logging.getLogger(__name__)


class SugarPayload2(object):
    def __init__(self, year=2017, month=2):
        self.year = year
        self.month = month

    @staticmethod
    def check_users_sugarid(check_dismissed=False):
        """
        Search for users with empty sugar_id (empty or NULL) and updates them from Sugar
        :return: Number of users updated
        """
        mysql = SQLDataSource.instance
        sql_qry = mysql.query(User).filter(or_(User.sugar_id.is_(None), User.sugar_id == ''))
        if not check_dismissed:
            sql_qry = sql_qry.filter(User.dissmissed == 'N')
        empty_users = sql_qry.all()

        if empty_users:
            logger.info("Users with empty sugar_id found {}".format(empty_users))
            logger.info("Calling Sugar for user ids ")
            db = SugarSource.instance
            sugar_qry = ChainSugarCrmQuery(db)
            sugar_qry.cursor().select_(['user_name', 'id']).from_('Users').where_().in_('users.user_name',
                                                                                        [u.sugar_uname for u in
                                                                                         empty_users], esq=True).end_()
            r_dict = {}
            for h in sugar_qry.fetch_all():
                r_dict = {k: v for k, v in h}
            logger.info("Updating users...")
            for user in empty_users:
                logger.info("User: {}, SugarId: {}".format(user.sugar_uname, r_dict[user.sugar_uname]))
                try:
                    user.sugar_id = r_dict[user.sugar_uname]
                except KeyError as e:
                    logger.warn("User {} has no sugar_id {} ".format(user.sugar_uname, e.message))
                    pass
                mysql.add(user)
            mysql.commit()
        return len(empty_users)

    def fetch_timesheets(self):
        """
        Re
        :return:
        """
        mysql = SQLDataSource.instance
        sugar = SugarSource.instance

        try:
            active_users = mysql.query(User).filter(User.dissmissed != 'Y', User.sugar_id.isnot(None),
                                                    or_(User.sugar_id != '', User.sugar_id.isnot(None))).all()
            dates = make_month_range(self.year, self.month)
            logger.info("Removing previous entries...")
            deleted_num = mysql.query(TimeSheet).filter(TimeSheet.activity_date >= dates[0],
                                                        TimeSheet.activity_date <= dates[1],
                                                        or_(TimeSheet.source != 'JIRA',
                                                            TimeSheet.source.is_(None))).delete()
            logger.info("Removed {} timesheets entries for year:{} month:{}".format(deleted_num, self.year, self.month))
            user_dict = {u.sugar_id: u for u in active_users}
            logger.debug("Active users are {}".format(user_dict))
            qry = ChainSugarCrmQuery(sugar)
            logger.info("Querying SugarCRM... ")
            fields = ['created_by', 'activity_date', 'time_spent', 'description', 'id', 'name']
            qry.cursor().select_(fields).from_('ps_Timesheets').where_().in_('ps_timesheets.created_by',
                                                                             user_dict.keys(), esq=True).and_().bw_(
                'ps_timesheets.activity_date', dates, esq=True).end_()
            logger.info("Done querying")
            summary = defaultdict(float)
            for entries in qry.fetch_all():
                for entry in entries:
                    user = user_dict[entry[0]]
                    t = TimeSheet(userid=user.id, created_by=entry[0], activity_date=entry[1], time_spent=entry[2],
                                  description=entry[3], id=entry[4], name=entry[5])
                    summary[user.sugar_uname] += float(entry[2])
                    mysql.add(t)
            logger.debug("Dirty entries {}".format(mysql.dirty))
            mysql.commit()
            logger.info("Commit completed")
            logger.info("=== Timesheets summary Year: {} Month: {}  === ".format(self.year, self.month))
            for k, v in summary.iteritems():
                logger.info("{}: {} hrs".format(k, v))
            return sum(summary.values())
        finally:
            mysql.rollback()

    def payload(self):
        logger.info("Checking SugarId for users...")
        self.__class__.check_users_sugarid()
        logger.info("About to fetch timesheets for {}-{}".format(self.year, self.month))
        overall_hrs = self.fetch_timesheets()
        logger.info("=== Total Hrs for {}-{} = {}".format(self.year, self.month, overall_hrs))

    def __repr__(self):
        return self.__class__.__name__


SugarPayload = SugarPayload2
