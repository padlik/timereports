#!/bin/env python
from primitives.logger import Logger
from primitives.observer import Dispatcher
from primitives.runpayload import Payload
from reports import lazycollect
from reports import sqlobservers


class SugarPayload(Payload):
    def __init__(self, year=2017, month=2):
        super(SugarPayload, self).__init__()
        self.dispatcher = Dispatcher()
        self.observers = self.__init_observers()
        self.collectors = self.__init_collectors()
        self.__connect()
        self.year = year
        self.month = month
        Logger.info("{} is ready to serve".format(str(self)))

    def __init_observers(self):
        Logger.info("Init observers")
        return sqlobservers.UserListObserver(), sqlobservers.TimesheetsObserver()

    def __init_collectors(self):
        Logger.info("Init collectors...")
        users = lazycollect.UserLazyList(self.observers[0].pre_load())
        Logger.info("Users collector initialized")
        ts = lazycollect.TimesheetsLazyList({k: None for k in users.values()})
        Logger.info("Timesheets collector initialized")
        return users, ts

    def __connect(self):
        Logger.info("Connecting observers and collectors")
        for i, collector in enumerate(self.collectors):
            self.dispatcher.register_event(collector, 'updated')
            self.dispatcher.subscribe(observer=self.observers[i], instance=collector, method='updated')

    def payload(self):
        Logger.info("Collecting users")
        u = {v: k for k, v in self.collectors[0].iteritems()}
        Logger.info("Collecting timesheets for {}:{}".format(self.year, self.month))
        self.collectors[1].year = self.year
        self.collectors[1].month = self.month
        Logger.info("Collecting timesheets")
        log_str = ''
        for uid, time_sheets in self.collectors[1].iteritems():
            hrs = 0
            if time_sheets:
                hrs = sum(map(float, [s[1] for s in time_sheets]))
            Logger.info("uid: {} \t - {} hrs".format(u[uid], hrs))
            log_str += "[{}: {} hrs]".format(u[uid], hrs)
        Logger.info("Timesheets collected: {}".format(log_str))
        Logger.info("Flushing changes to the DB")
        for o in self.observers:
            o.flush()
        self.collectors[1].clear()

    def __str__(self):
        return self.__class__.__name__
