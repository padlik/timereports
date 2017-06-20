#!/usr/bin/env python

import hashlib
import json
import urllib2
from urllib import urlencode

from primitives import Logger


class LiteSugarCRM(object):
    REST = 'https://sugarinternal.sugarondemand.com/service/v4_1/rest.php'

    def request(self, method, data):

        data = json.dumps(data)
        args = {'method': method, 'input_type': 'json', 'response_type': 'json', 'rest_data': data}
        params = urlencode(args)
        response = urllib2.urlopen(self._rest, params)
        response = response.read()
        Logger.debug("Raw response is {} ".format(response))
        result = json.loads(response)
        Logger.debug("Raw result is {} ".format(result))
        return result

    def execute(self, method, *args):
        return self.request(method, [self._session] + list(args))

    def close(self):
        return self.request('logout', [self._session])

    def _connect(self, user, passwd):

        args = {'user_auth': {'user_name': user, 'password': self._enconde_pass(passwd)}}

        x = self.request('login', args)
        try:
            return x['id']
        except KeyError:
            raise Exception('Can''t connect to Sugar')

    @staticmethod
    def _enconde_pass(passwd):
        encode = hashlib.md5(passwd)
        result = encode.hexdigest()
        return result

    def __init__(self, user, passwd, rest=None):
        self._rest = rest or LiteSugarCRM.REST
        self._session = self._connect(user, passwd)
