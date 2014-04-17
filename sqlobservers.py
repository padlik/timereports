#!/bin/env python

from primitives.observer import BasicObserver
import inject
from injectors import SQLDb
from primitives.logger import Logger


class CachingObserver(BasicObserver):
    def __init__(self):
        self._updated = []

    def notify(self, sender, *m_args, **m_kwargs):
        self._updated.append(m_args)

    @property
    def updated(self):
        return self._updated

    def flush(self, *args, **kwargs):
        pass


class UserListObserver(CachingObserver):
    def __init__(self):
        super(UserListObserver).__init__()
        self._db = inject.instance(SQLDb)

    def pre_load(self):
        Logger.debug("In UserList pre-load")
        q_sql = "select sugar_uname, sugar_id from users"
        c = self._db.cursor()
        c.execute(q_sql)
        return dict(c.fetchall())

    def flush(self):
        if self._updated:
            Logger.debug("In UserList flush")
            q_sql = "update users set sugar_id = %s where sugar_uname = %s"
            c = self._db.cursor()
            q_params = [(v, k) for k, v in self._updated]
            Logger.debug("In UserList flush->params{}".format(q_params))
            c.executemany(q_sql, q_params)
            self._db.commit()
            Logger.debug("Commit complete")
            self._updated = []


class TimesheetsObserver(CachingObserver):
    def __init__(self):
        super(TimesheetsObserver).__init__()
        self._db = inject.instance(SQLDb)

    def _get_users(self):
        q_sql = "select sugar_id, id from users"
        c = self._db.cursor()
        c.execute(q_sql)
        return dict(c.fetchall())

    def flush(self, *args, **kwargs):
        if self._updated:
            Logger.debug("Inside timesheets flush")
            users = self._get_users()
            Logger.debug("Inside timesheets flush. Users->{}".format(users))
            fields = kwargs.get('fields', ['userid', 'created_by', 'activity_date', 'time_spent', 'description', 'id'])
            Logger.debug("Inside timesheets flush. Fields->{}".format(fields))
            if not 'userid' in fields:
                fields = ['userid'] + fields
            q_sql = 'insert into timesheets( ' + ','.join(fields) + ') values (' + ','.join(
                ['%s'] * (len(fields))) + ')'
            q_sql += ' ON DUPLICATE KEY UPDATE %s = VALUES(%s) ' % ('time_spent', 'time_spent')
            Logger.debug("Inside timesheets flush. Query->{}".format(q_sql))
            c = self._db.cursor()
            values = []
            for uid, timesheets in self._updated:
                for ts in timesheets:
                    values.append(([users[uid]] + [uid] + ts))
            Logger.debug("Inside timesheets flush. Values->{}".format(values))
            c.executemany(q_sql, values)
            self._db.commit()
            Logger.debug("Commit complete")
            self._updated = []