#!/usr/bin/env python

import json
import logging
from collections import namedtuple

import requests
from decouple import config

logger = logging.getLogger(__name__)


class RestSugarCRM(object):
    REST = 'https://sugarinternal.sugarondemand.com/rest/v11/'
    OAUTH2 = 'oauth2/token'
    LOGOUT = 'oauth2/logout'
    PING = 'ping'

    @staticmethod
    def _json_object_hook(d):
        return namedtuple('SugarJson', d.keys(), rename=True)(*d.values())

    @staticmethod
    def _check_response(response):
        if response.status_code == 200:
            return json.loads(response.text, object_hook=RestSugarCRM._json_object_hook)
        else:
            raise Exception('Failed to execute {} on {}'.format(response.url, response.status_code))

    def connect(self, user, passwd):
        logger.info("Connecting to {}".format(self._rest))
        payload = {'grant_type': 'password',
                   'username': user,
                   'password': passwd,
                   'client_id': 'sugar',
                   'client_secret': ''}
        logger.debug("Payload is: {}".format(payload))
        logger.debug("Headers are: {}".format(self._headers))
        url = self._rest + self.OAUTH2
        x = RestSugarCRM._check_response(requests.post(url, data=json.dumps(payload), headers=self._headers))
        self._headers['OAuth-Token'] = x.access_token
        self._refresh_token = x.refresh_token
        logger.info("Connected to {}".format(self._rest))
        logger.debug("Access token is: {}".format(x.access_token))

    def logout(self):
        logger.info("Logging out from {}".format(self._rest))
        x = None
        try:
            x = RestSugarCRM._check_response(requests.post(self._rest + self.LOGOUT, data=None, headers=self._headers))
        except Exception as e:
            logger.warn('Exception on logout from Sugar'.format(e))
            logger.info("Ignoring exceptions on logout")
        finally:
            if 'OAuth-Token' in self._headers:
                del self._headers['OAuth-Token']
            return x

    def ping(self):
        return self.get(self.PING)

    def get(self, url, params=None):
        u = self._rest + url
        return RestSugarCRM._check_response(requests.get(u, params=params, headers=self._headers))

    def __init__(self, rest=None):
        self._rest = rest or RestSugarCRM.REST
        self._headers = {'Content-Type': 'application/json',
                         'Cache-Control': 'no-cache'}
        self._refresh_token = None


if __name__ == "__main__":
    print "Checking RestSugarCRM"
    r = RestSugarCRM()
    r.connect(config('SUGAR_USER'), config('SUGAR_PASS'))
    print "There should be pong -> {}".format(r.ping())
    filter = "[{\"assigned_user_id\": \"%s\"}," \
             "{\"activity_date\": {\"$gte\":\"%s\"}},{\"activity_date\": {\"$lte\":\"%s\"}}]"
    from utils import make_month_range

    dates = make_month_range(2018, 5)
    print dates[0].strftime("%Y-%m-%d"), dates[1].strftime("%Y-%m-%d")
    q = filter % ('64dbcf2a-d883-8f19-ac2c-55fa2d795db4', dates[0].strftime("%Y-%m-%d"), dates[1].strftime("%Y-%m-%d"))
    querystring = {"filter": q, "max_num": "100"}
    x = r.get("ps_Timesheets/filter", params=querystring)
    print x._fields
    if 'records' in x._fields:
        for rec in x.records:
            print "==="
            print rec.created_by
            print rec.activity_date
            print rec.time_spent
            print rec.description
            print rec.id
            print rec.name
            print "======"
    print "There should be true -> {}".format(r.logout().success)
