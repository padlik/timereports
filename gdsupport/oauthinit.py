#!/bin/env python

#run  get refresh and access tokens for google oauth2 and load them into db
import MySQLdb
import gdata.gauth


SCOPE = 'https://spreadsheets.google.com/feeds/'


def refresh_tokens(params):
    token = gdata.gauth.OAuth2Token(client_id=params['client_id'], client_secret=params['client_sec'], scope=SCOPE,
                                    user_agent='paul.app')
    print 'Verification URL: %s' % token.generate_authorize_url()
    code = raw_input('Paste verification code from URL above:').strip()
    token.get_access_token(code)
    params['client_at'] = token.access_token
    params['client_rt'] = token.refresh_token
    return params


def get_oauth_params(user, password, db, host):
    db = MySQLdb.connect(user=user, passwd=password, db=db, host=host, charset='utf8')
    c = db.cursor()
    c.execute('select param, value from time_reports.oauthdata')
    params = {p: v for p, v in c.fetchall()}
    db.close()
    return params


def set_oauth_params(user, password, db, host, data):
    db = MySQLdb.connect(user=user, passwd=password, db=db, host=host, charset='utf8')
    c = db.cursor()
    s_qry = """insert into time_reports.oauthdata(param, value) values (%s, %s)
               ON DUPLICATE KEY UPDATE value = values(value)"""
    c.executemany(s_qry, data)
    db.commit()
    db.close()
    return data


if __name__ == '__main__':
    cred = ('root', 'pass', 'time_reports', 'localhost')
    params = get_oauth_params(*cred)
    params = refresh_tokens(params)
    print params
    data = [(k, v) for k, v in params.iteritems()]
    cred = cred + (data, )
    set_oauth_params(*cred)
