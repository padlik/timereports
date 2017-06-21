#!/bin/env python

import logging

import inject
from injectors import SQLDb
from primitives import BasicObserver

logger = logging.getLogger(__name__)


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
        super(UserListObserver, self).__init__()
        self._db = inject.instance(SQLDb)

    def pre_load(self):
        logger.debug("In UserList pre-load")
        q_sql = "SELECT sugar_uname, sugar_id FROM users WHERE dissmissed <> 'Y'"
        c = self._db.cursor()
        c.execute(q_sql)
        return dict(c.fetchall())

    def flush(self):
        if self._updated:
            logger.debug("In UserList flush")
            q_sql = "UPDATE users SET sugar_id = %s WHERE sugar_uname = %s"
            c = self._db.cursor()
            q_params = [(v, k) for k, v in self._updated]
            logger.debug("In UserList flush->params{}".format(q_params))
            c.executemany(q_sql, q_params)
            self._db.commit()
            logger.debug("Commit complete")
            self._updated = []


class TimesheetsObserver(CachingObserver):
    def __init__(self):
        super(TimesheetsObserver, self).__init__()
        self._db = inject.instance(SQLDb)

    def _get_users(self):
        q_sql = "SELECT sugar_id, id FROM users WHERE dissmissed <> 'Y'"
        c = self._db.cursor()
        c.execute(q_sql)
        return dict(c.fetchall())

    def flush(self, *args, **kwargs):
        if self._updated:
            logger.debug("Inside timesheets flush")
            users = self._get_users()
            logger.debug("Inside timesheets flush. Users->{}".format(users))
            fields = kwargs.get('fields',
                                ['userid', 'created_by', 'activity_date', 'time_spent', 'description', 'id', 'name'])
            logger.debug("Inside timesheets flush. Fields->{}".format(fields))
            if 'userid' not in fields:
                fields = ['userid'] + fields
            q_sql = 'INSERT INTO timesheets( ' + ','.join(fields) + ') VALUES (' + ','.join(
                ['%s'] * (len(fields))) + ')'
            q_sql += ' ON DUPLICATE KEY UPDATE %s = VALUES(%s) ' % ('time_spent', 'time_spent')
            logger.debug("Inside timesheets flush. Query->{}".format(q_sql))
            c = self._db.cursor()
            values = []
            for uid, timesheets in self._updated:
                for ts in timesheets:
                    values.append(([users[uid]] + [uid] + ts))
            logger.debug("Inside timesheets flush. Values->{}".format(values))
            c.executemany(q_sql, values)
            self._db.commit()
            logger.debug("Commit complete")
            self._updated = []
