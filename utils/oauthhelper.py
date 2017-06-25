#!/bin/env python
import logging

import gdata.gauth
from decouple import config

from datasources import SQLDataSource, mysql_creator
from serializers import OAuthData

SCOPE = 'https://spreadsheets.google.com/feeds/'

logger = logging.getLogger(__name__)


def refresh_tokens(params):
    """
    Refresh google auth token. Please refer google documentation for details.
    :param params: dict of params (client_id, client_secret, user_agent, scope)
    :return: extended dict with access and refresh tokens (client_at, client_rt)
    """
    token = gdata.gauth.OAuth2Token(client_id=params['client_id'], client_secret=params['client_sec'], scope=SCOPE,
                                    user_agent='paul.app')
    print 'Verification URL: %s' % token.generate_authorize_url()
    code = raw_input('Paste verification code from URL above:').strip()
    token.get_access_token(code)
    params['client_at'] = token.access_token
    params['client_rt'] = token.refresh_token
    return params


def get_oauth_params():
    """
    Fetch OAuth params from database
    :return:
    """
    mysql = SQLDataSource.instance
    params = {p.param: p.value for p in mysql.query(OAuthData).all()}
    return params


def set_oauth_params(data):
    """
    Stores OAuth params in the database
    :param data: dict of OAuth params
    :return:
    """
    logger.info("About to set data {}".format(data))
    mysql = SQLDataSource.instance
    for param, value in params.iteritems():
        row = OAuthData(param=param, value=value)
        mysql.merge(row)
    mysql.commit()
    return data


def setup_logging():
    """
    Setups basic logging logic and format. Special case for sqlalchemy.
    :return:
    """
    log_level = logging.DEBUG if config('DEBUG', cast=bool) else logging.INFO
    logging.basicConfig(level=logging.INFO,
                        format="[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
                        datefmt="%H:%M:%S")
    if log_level == logging.DEBUG:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


if __name__ == '__main__':
    setup_logging()
    SQLDataSource.set_creator(mysql_creator)
    params = get_oauth_params()
    params = refresh_tokens(params)
    logging.info("Token params are: {}".format(params))
    set_oauth_params(params)
