#!/bin/env python


import MySQLdb
import sys

from paramsparser import AppParamsParser
import inject
from injectors import SQLDb
from injectors import SugarDb
from logger import Logger
from logger import set_logging
import litesugarcrm
import sqlobservers
import lazycollect
from primitives.observer import Dispatcher


def do_parse(argv):
    parser = AppParamsParser()
    return parser.parse(argv)


def do_inject(config):
    sugar_db = litesugarcrm.LiteSugarCRM(config['sugar.user'], config['sugar.password'])
    mysql_conf = {'user': config['mysql.user'],
                  'passwd': config['mysql.password'],
                  'db': config['mysql.db'],
                  'host': config['mysql.host'],
                  'charset': 'utf8'}
    sql_db = MySQLdb.connect(**mysql_conf)

    def my_config(binder):
        binder.bind(SugarDb, sugar_db)
        binder.bind(SQLDb, sql_db)

    inject.configure(my_config)
    Logger.info('Starting')


def do_run(config):
    observers = (sqlobservers.UserListObserver(), sqlobservers.TimesheetsObserver())
    disp = Dispatcher()

    users = lazycollect.UserLazyList(observers[0].pre_load())
    disp.register_event(users, 'updated')
    disp.subscribe(observers[0], users, 'updated')

    ts = lazycollect.TimesheetsLazyList({k: None for k in users.values()})
    ts.year = config['year']
    ts.month = config['month']
    disp.register_event(ts, 'updated')
    disp.subscribe(observers[1], ts, 'updated')
    Logger.info('Year:{} and month:{}'.format(ts.year, ts.month))

    u = {v: k for k, v in users.iteritems()}
    logstr = ''
    for uid, time_sheets in ts.iteritems():
        hrs = 0
        if time_sheets:
            hrs = sum(map(float, [s[1] for s in time_sheets]))
        logstr += "[{}: {} hrs]".format(u[uid], hrs)

    Logger.info('Timesheets: {}'.format(logstr))
    for o in observers:
        o.flush()
    Logger.info('Done')


if __name__ == "__main__":
    config = do_parse(sys.argv[1:])
    set_logging(config)
    do_inject(config)
    do_run(config)
