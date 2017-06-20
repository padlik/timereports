#!/bin/env python
import gdata.gauth

import reports.inject
from reports.injectors import SQLDb
from utils.paramsparser import BasicParamsParser

SCOPE = 'https://spreadsheets.google.com/feeds/'

CONFIG = {"host": (('-h', '--host'), {'required': True, 'help': "DB host"}),
          "user": (('-u', '--user'), {'required': True, 'help': "DB user"}),
          "password": (('-p', '--password'), {'required': True, 'help': "DB password"}),
          "db": (('-d', '--db'), {'required': True, 'help': "schema name"})}


def refresh_tokens(params):
    token = gdata.gauth.OAuth2Token(client_id=params['client_id'], client_secret=params['client_sec'], scope=SCOPE,
                                    user_agent='paul.app')
    print 'Verification URL: %s' % token.generate_authorize_url()
    code = raw_input('Paste verification code from URL above:').strip()
    token.get_access_token(code)
    params['client_at'] = token.access_token
    params['client_rt'] = token.refresh_token
    return params


def get_oauth_params():
    db = reports.inject.instance(SQLDb)
    c = db.cursor()
    c.execute('SELECT param, value FROM time_reports.oauthdata')
    params = {p: v for p, v in c.fetchall()}
    return params


def set_oauth_params(data):
    db = reports.inject.instance(SQLDb)
    c = db.cursor()
    s_qry = """INSERT INTO time_reports.oauthdata(param, value) VALUES (%s, %s)
               ON DUPLICATE KEY UPDATE value = values(value)"""
    c.executemany(s_qry, data)
    db.commit()
    return data


if __name__ == '__main__':
    import sys
    import MySQLdb

    cmd_params = sys.argv[1:]
    config = BasicParamsParser(caption=sys.argv[0], config=CONFIG, need_help=False)
    config.parse(cmd_params)
    mysql_conf = {'user': config['user'], 'passwd': config['password'], 'db': config['db'], 'host': config['host'],
                  'charset': 'utf8'}
    sqldb = MySQLdb.connect(**mysql_conf)


    def my_config(binder):
        binder.bind(SQLDb, sqldb)


    reports.inject.configure(my_config)
    params = get_oauth_params()
    params = refresh_tokens(params)
    print params
    data = [(k, v) for k, v in params.iteritems()]
    set_oauth_params(data)
    db = reports.inject.instance(SQLDb)
    db.close()
