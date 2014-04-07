#!/bin/env python

import calendar

import inject
from primitives.lazydict import LazyDict
from sugarcrmquery import ChainSugarCrmQuery
from injectors import SugarDb
from logger import Logger


class UserLazyList(LazyDict):
    def __batch_update__(self, items):
        db = inject.instance(SugarDb)
        qry = ChainSugarCrmQuery(db)
        Logger.debug('Users list: Users->{}'.format(items.keys()))
        Logger.debug('Users list: fields->{} '.format(['user_name', 'id']))
        qry.cursor().select_(['user_name', 'id']).from_('Users').where_().in_('users.user_name', items.keys(),
                                                                              esq=True).end_()
        r_dict = {}
        for h in qry.fetch_all():
            r_dict = {k: v for k, v in h}
        Logger.debug('Users list: Returned->#{}'.format(len(r_dict)))
        Logger.debug('Users list: Output:->{}'.format(r_dict))
        return r_dict


class TimesheetsLazyList(LazyDict):
    def __init__(self, *args, **kwargs):
        super(TimesheetsLazyList, self).__init__(*args, **kwargs)
        self._year = 2014
        self._month = 2
        self._fields = ['created_by', 'activity_date', 'time_spent', 'description', 'id']


    @property
    def fields(self):
        return self._fields

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, year):
        self._year = year

    @property
    def month(self):
        return self._month

    @month.setter
    def month(self, month):
        self._month = month

    def __get_dates(self):
        first = "%s-%s-%s" % (self._year, self._month, 1)
        last = "%s-%s-%s" % (self._year, self._month, calendar.monthrange(self._year, self._month)[1])
        return tuple([first, last])

    def __batch_update__(self, items):
        keys = [key for key, value in items.iteritems() if value != []]  # special case for uniformity
        if keys:
            Logger.debug('TS List: Keys to update->#{}'.format(keys))
            db = inject.instance(SugarDb)
            qry = ChainSugarCrmQuery(db)
            dates = self.__get_dates()
            Logger.debug('TS List: Dates to fetch->{}'.format(dates))
            Logger.debug('TS List: Query params->fields:{}'.format(self._fields))
            Logger.debug('TS List: Query params->created_by:{}'.format(keys))
            Logger.debug('TS List: Query params->activity date between:{}'.format(dates))
            qry.cursor().select_(self._fields).from_('ps_Timesheets').where_(
            ).in_('ps_timesheets.created_by', keys, esq=True).and_().bw_('ps_timesheets.activity_date', dates,
                                                                         esq=True).end_()
            # ts = collections.defaultdict(list)
            ts = {k: [] for k in keys}
            for entries in qry.fetch_all():
                for entry in entries:
                    ts[entry[0]].append(entry[1:])
            Logger.debug('TS List: Query returned->{}'.format(ts))
            return ts
        else:
            Logger.debug('TS List: No items to update, passing')
            return items

